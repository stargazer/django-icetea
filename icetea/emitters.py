# TODO: Incorporate all the monkey patching in here!

# TODO: What is this
from __future__ import generators

import decimal, re, inspect
import copy

from django.db.models.query import QuerySet
from django.db.models import Model, permalink
from django.utils import simplejson
from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.encoding import smart_unicode
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse
from django.core import serializers

import simplejson

from utils import HttpStatusCode

# Class which will register MimeTypes to methods which will decode the
# corresponding MimeType to python data structures.
from utils import Mimer

#TODO: Needed?
#from validate_jsonp import is_valid_jsonp_callback_value

# TODO: WTF?
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

#TODO: WTF?
# Allow people to change the reverser (default `permalink`).
reverser = permalink

class Emitter(object):
    """
    Super emitter. All other emitters should subclass
    this one. 
    
    Its :meth:~`icetea.emitters.Emitter.construct`method returns a serialized 
    dictionary of whatever data it is given. This is typically the only method 
    that a custom emitter needs.

    Every time we need the API handler needs to return a response, a new
    instance of the appropriate emitter should be created. Calling the
    emitter's :meth:`icetea.emitters.Emitter.render` method, should serialize
    the response data, and return them to the calling function.

    TODO: WTF?
    `RESERVED_FIELDS` was introduced when better resource
    method detection came, and we accidentially caught these
    as the methods on the handler. Issue58 says that's no good.
    """
    EMITTERS = { }
    RESERVED_FIELDS = set([ 'read', 'update', 'create',
                            'delete', 'model', 'anonymous',
                            'allowed_methods', 'fields', 'exclude' ])

    def __init__(self, payload, typemapper, handler, fields=()):
        # Typemapper: Contains mappings of { <api handler>: <data model>}       
        self.typemapper = typemapper
        # Data to be serialized
        self.data = payload
        # API Handler, handling this request        
        self.handler = handler
        # Fields that the handler needs to output
        self.fields = fields

        if isinstance(self.data, Exception):
            raise

    # TODO: WTF?
    def method_fields(self, handler, fields):
        if not handler:
            return { }

        ret = dict()

        for field in fields - Emitter.RESERVED_FIELDS:
            t = getattr(handler, str(field), None)

            if t and callable(t):
                ret[field] = t

        return ret
            
    def construct(self):

        """
        Recursively serialize a lot of types, and
        in cases where it doesn't recognize the type,
        it will fall back to Django's `smart_unicode`.

        Returns a dictionary representation of ``self.data``.
        """
        def _any(thing, fields=(), nested=False):
            """
            Dispatch, all types are routed through here.

			@param thing: Data we are trying to serialize
			@param fields: The fields of ``thing`` to serialize. Applies only
            for database models.
			@param nested: Are the fields of ``thing`` nested, or are they
			first class fields?
            """        
            ret = None

            if isinstance(thing, QuerySet):
                ret = _qs(thing, fields=fields, nested=nested)
            elif isinstance(thing, (tuple, list, set)):
                ret = _list(thing, fields=fields)
            elif isinstance(thing, dict):
                ret = _dict(thing, fields)
            elif isinstance(thing, decimal.Decimal):
                ret = str(thing)
            elif isinstance(thing, Model):
                ret = _model(thing, fields, nested)
            elif isinstance(thing, HttpResponse):
                raise HttpStatusCode(thing)
            elif inspect.isfunction(thing):
                if not inspect.getargspec(thing)[0]:
                    ret = _any(thing())
            elif hasattr(thing, '__emittable__'):
                f = thing.__emittable__
                if inspect.ismethod(f) and len(inspect.getargspec(f)[0]) == 1:
                    ret = _any(f())
            elif repr(thing).startswith("<django.db.models.fields.related.RelatedManager"):
                ret = _any(thing.all(), (), nested)
            else:
                ret = smart_unicode(thing, strings_only=True)

            return ret

        def _fk(data, field, nested=True):
            """
            Foreign keys.

			Fields of foreign keys are always nested.
            """
            return _any(getattr(data, field.name), fields=(), nested=True)

        def _related(data, fields=(), nested=True):
            """
            Foreign keys.

            Fields of (related) foreign keys are always nested
            """
            return [ _model(m, fields) for m in data.iterator() ]

        def _m2m(data, field, fields=()):
            """
            Many to many (re-route to `_model`.)
            """
            return [ _model(m, fields) for m in getattr(data, field.name).iterator() ]

        # TODO: Study it again, and get rid of all its garbage.
        def _model(data, fields=(), nested=False):
            """
            Models. 
            
            If ``data`` is nested, then the ``fields`` are decided by:
                handler.fields - handler.exclude_nested.
            If not, the ``fields`` should be given as input to the method.
            """
            ret = { }
            handler = self.in_typemapper(type(data))

            if nested:
                fields = set(handler.fields) - set(handler.exclude_nested)

            get_absolute_uri = False

            if handler or fields:
                v = lambda f: getattr(data, f.attname)

                if not fields:
                    """
                    Fields was not specified, try to find teh correct
                    version in the typemapper we were sent.
                    """
                    mapped = self.in_typemapper(type(data))
                    get_fields = set(mapped.fields)
                    exclude_fields = set(mapped.exclude).difference(get_fields)

                    if 'absolute_uri' in get_fields:
                        get_absolute_uri = True

                    if not get_fields:
                        get_fields = set([ f.attname.replace("_id", "", 1)
                            for f in data._meta.fields + data._meta.virtual_fields])
                    
                    if hasattr(mapped, 'extra_fields'):
                        get_fields.update(mapped.extra_fields)

                    # sets can be negated.
                    for exclude in exclude_fields:
                        if isinstance(exclude, basestring):
                            get_fields.discard(exclude)

                        elif isinstance(exclude, re._pattern_type):
                            for field in get_fields.copy():
                                if exclude.match(field):
                                    get_fields.discard(field)

                else:
                    get_fields = set(fields)

                met_fields = self.method_fields(handler, get_fields)

                for f in data._meta.local_fields + data._meta.virtual_fields:
                    if f.serialize and not any([ p in met_fields for p in [ f.attname, f.name ]]):
                        if not f.rel:
                            if f.attname in get_fields:
                                ret[f.attname] = _any(v(f))
                                get_fields.remove(f.attname)
                        else:
                            if f.attname[:-3] in get_fields:
                                ret[f.name] = _fk(data, f, nested=True)
                                get_fields.remove(f.name)

                for mf in data._meta.many_to_many:
                    if mf.serialize and mf.attname not in met_fields:
                        if mf.attname in get_fields:
                            ret[mf.name] = _m2m(data, mf)
                            get_fields.remove(mf.name)

                # try to get the remainder of fields
                for maybe_field in get_fields:
                    if isinstance(maybe_field, (list, tuple)):
                        model, fields = maybe_field
                        inst = getattr(data, model, None)

                        if inst:
                            if hasattr(inst, 'all'):
                                ret[model] = _related(inst, fields)
                            elif callable(inst):
                                if len(inspect.getargspec(inst)[0]) == 1:
                                    ret[model] = _any(inst(), fields)
                            else:
                                ret[model] = _model(inst, fields, nested=True)

                    elif maybe_field in met_fields:
                        # Overriding normal field which has a "resource method"
                        # so you can alter the contents of certain fields without
                        # using different names.
                        ret[maybe_field] = _any(met_fields[maybe_field](data))

                    else:
                        maybe = getattr(data, maybe_field, None)
                        if maybe is not None:
                            if callable(maybe):
                                if len(inspect.getargspec(maybe)[0]) <= 1:
                                    ret[maybe_field] = _any(maybe())
                            else:
                                ret[maybe_field] = _any(maybe, nested=True)
                        else:
                            handler_f = getattr(handler or self.handler, maybe_field, None)

                            if handler_f:
                                ret[maybe_field] = _any(handler_f(data))

            else:
                for f in data._meta.fields:
                    ret[f.attname] = _any(getattr(data, f.attname))

                fields = dir(data.__class__) + ret.keys()
                add_ons = [k for k in dir(data) if k not in fields]

                for k in add_ons:
                    ret[k] = _any(getattr(data, k))

            # resouce uri
            if self.in_typemapper(type(data)):
                handler = self.in_typemapper(type(data))
                if hasattr(handler, 'resource_uri'):
                    url_id, fields = handler.resource_uri(data)

                    try:
                        ret['resource_uri'] = reverser( lambda: (url_id, fields) )()
                    except NoReverseMatch, e:
                        pass

            if hasattr(data, 'get_api_url') and 'resource_uri' not in ret:
                try: ret['resource_uri'] = data.get_api_url()
                except: pass

            # absolute uri
            if hasattr(data, 'get_absolute_url') and get_absolute_uri:
                try: ret['absolute_uri'] = data.get_absolute_url()
                except: pass

            return ret

        def _qs(data, fields=(), nested=False):
            """
            Querysets.
			``data`` is a queryset

            Queryset data might as well be nested or first class fields.
            """
            return [ _any(v, fields, nested) for v in data ]

        def _list(data, fields=()):
            """
            Lists.
            """
            return [ _any(v, fields) for v in data ]

        def _dict(data, fields=()):
            """
            Dictionaries.
            """
            return dict([ (k, _any(v, fields)) for k, v in data.iteritems() ])
        
        # Kickstart the seralizin'. 
        return _any(self.data, self.fields)

    def in_typemapper(self, model):
        """
        Returns the ``model``'s associated API handler.
        """
        for _handler, _model in self.typemapper.iteritems():
            if model is _model:
                return _handler

    def get_fields(self, handler):
        if handler != self.handler:
            #nested
			return set(handler.fields) - set(handler.exclude_nested)
        return handler.fields


    def render(self):
        """
        This super emitter does not implement `render`,
        this is a job for the specific emitter below.
        """
        raise NotImplementedError("Please implement render.")

    @classmethod
    def get(cls, format):
        """
        Gets an emitter, returns the class and a content-type.
        """
        if cls.EMITTERS.has_key(format):
            return cls.EMITTERS.get(format)

        raise ValueError("No emitters found for type %s" % format)

    @classmethod
    def register(cls, name, klass, content_type='text/plain'):
        """
        Register an emitter.

        Parameters::
         - `name`: The name of the emitter ('json', 'xml', 'yaml', ...)
         - `klass`: The emitter class.
         - `content_type`: The content type to serve response as.
        """
        cls.EMITTERS[name] = (klass, content_type)

    @classmethod
    def unregister(cls, name):
        """
        Remove an emitter from the registry. Useful if you don't
        want to provide output in one of the built-in emitters.
        """
        return cls.EMITTERS.pop(name, None)

class JSONEmitter(Emitter):
    """
    JSON emitter, understands timestamps.
    """
    def render(self, request):
        # TODO: Get rid of this callback shit
        cb = request.GET.get('callback', None)
        data_as_dic = self.construct()
        seria = simplejson.dumps(data_as_dic, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=4)

        # Callback
        if cb and is_valid_jsonp_callback_value(cb):
            return '%s(%s)' % (cb, seria)

        return seria

Emitter.register('json', JSONEmitter, 'application/json; charset=utf-8')
Mimer.register(simplejson.loads, ('application/json',))


class DjangoEmitter(Emitter):
    """
    Emitter for the Django serialized format.
    """
    def render(self, request, format='xml'):
        if isinstance(self.data, HttpResponse):
            return self.data
        elif isinstance(self.data, (int, str)):
            response = self.data
        else:
            response = serializers.serialize(format, self.data, indent=True)

        return response

Emitter.register('django', DjangoEmitter, 'text/xml; charset=utf-8')
