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

try:
	import xlwt
except ImportError:
	# Needed for sphinx documentation
	# WTF
	pass
import StringIO

# Class which will register MimeTypes to methods which will decode the
# corresponding MimeType to python data structures.
from utils import Mimer

#TODO: Needed?
#from validate_jsonp import is_valid_jsonp_callback_value

#TODO: WTF?
# Allow people to change the reverser (default `permalink`).
reverser = permalink

from handlers import BaseHandler, ModelHandler

# Mappings of: {<Api Handler instance>, <model>}
_TYPEMAPPER = {}

class Emitter:
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

    def __init__(self, payload, handler, fields=()):
        # Maps pairs of {<API Handler instance>: <Model>}
        self.typemapper = _TYPEMAPPER

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
                ret = _dict(thing, fields, nested)
            elif isinstance(thing, decimal.Decimal):
                ret = str(thing)
            elif isinstance(thing, Model):
                ret = _model(thing, fields, nested)
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
            
            If nested=True, then the ``fields`` are decided by:
                handler.fields - handler.exclude_nested.

            If not, the ``fields`` should be given as input to the method.

            If no handler can be found, the emitter will try to construct a
            default representation of the data.
            """
            ret = { }
            handler = self.in_typemapper(type(data))

            if nested and handler:
                # TODO: If the request does not ask for nested representation,
                # then give resource URI instead.
                fields = set(handler.allowed_out_fields) - set(handler.exclude_nested)

            
            if handler:
                get_fields = set(fields)

                # Callable fields
                met_fields = self.method_fields(handler, get_fields)
                v = lambda f: getattr(data, f.attname)

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

            # No handler could be found. So trying to construct a default
            # representation for the model.
            else:
                for f in data._meta.fields:
                    ret[f.attname] = _any(getattr(data, f.attname))

                fields = dir(data.__class__) + ret.keys()
                add_ons = [k for k in dir(data) if k not in fields]

                for k in add_ons:
                    ret[k] = _any(getattr(data, k))

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

        def _dict(data, fields=(), nested=False):
            """
            Dictionaries.

            IF the values of the dictionary are models or querysets, they
            should appear as nested.
            """
            if fields:
                # If there is no field selection, just output everything.
                return dict([ (k, _any(v, fields, nested)) for k, v in data.iteritems() if k in fields])
            else:
                return dict([ (k, _any(v, fields, nested)) for k, v in data.iteritems()])
        

        # If the handler is a BaseHandler, any models should appear as nested
        nested = False
        if not isinstance(self.handler, ModelHandler): nested = True
        
        # Kickstart the seralizin'. 
        return _any(self.data, self.fields, nested)


    def in_typemapper(self, model):
        """
        Returns the ``model``'s associated API handler.
        """
        for _handler, _model in self.typemapper.iteritems():
            if model is _model:
                return _handler

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

class XMLEmitter(Emitter):
    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement("resource", {})
                self._to_xml(xml, item)
                xml.endElement("resource")
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))

    def render(self, request):
        stream = StringIO.StringIO()

        xml = SimplerXMLGenerator(stream, "utf-8")
        xml.startDocument()
        xml.startElement("response", {})

        self._to_xml(xml, self.construct())

        xml.endElement("response")
        xml.endDocument()

        return stream.getvalue()
Emitter.register('xml', XMLEmitter, 'text/xml; charset=utf-8')


class ExcelEmitter(Emitter):
    def render(self, request):
        def _to_unicode(string):
            """ Return the unicode repsesentation of string"""
            try:
                return unicode(string)
            except UnicodeDecodeError:
                # the string is a bytestring
                ascii_text = str(string).encode('string_escape')
                return unicode(ascii_text)
        def to_utf8(string):
            """Return the utf-8 encoded representation of the string """
            unic = _to_unicode(string)
            return unic.encode('utf-8')

        # In the case of the ExcelEmitter, we want only the actual data. No
        # debug messages and shit
        data = self.data['data']
        # Fields that we should output. In theory, these should be the *only*
        # keys in the dictionary ``data``.
        fields = self.handler.get_output_fields(request)

        wb = xlwt.Workbook(encoding='utf-8')
        stream = StringIO.StringIO()
        
        ws = wb.add_sheet("SmartPR")
        
        # Write field names on row 0
        col = 0
        for field_name in fields:
            ws.write(0, col, field_name.capitalize())
            col = col + 1

        # In case the ``data`` is a dictionary (eg the request was asking for a
        # single model instance), we transform it to a list
        if isinstance(data, dict):
            data = [data]

        row = 1     

        for record in data:
            # every record is a dict
            
            col = 0         
            for key in fields:
                value = ""
                field_value = record[key]
                
                # I merge lists or dicts to "\r\n"-separated strings
                # Why?                                      
                # 2. There's not really any reasonable way to represent nested
                # fields/dics in excel.
                # 1. They look better thatn simply dumping them as
                # dictionaries.
                if isinstance(field_value, list):
                    if field_value:
                        field_value = [to_utf8(item) for item in field_value]
                        value = "\r\n".join(field_value)
                elif isinstance(field_value, dict):
                    if field_value:
                        value = "\r\n".join(to_utf8(key) + ":" + to_utf8(value)  for key, value in
                            field_value.items())
                else:
                    value = to_utf8(record[key])

                ws.write(row, col, value )
                col = col + 1
            row = row + 1
        wb.save(stream)
        return stream.getvalue()
    # TODO
    # Works only for outputting handlers extending the ModelHandler class
    # Doesn't really work with outputing nested fields 

Emitter.register('excel', ExcelEmitter, 'application/vnd.ms-excel')
 
               
class HTMLEmitter(Emitter):
    def render(self, request):
        construct = self.construct()

        if 'data' in construct:
            # Correct response
            return construct['data']

        elif 'errors' in construct:
            # Validation was raised
            return construct['errors']

        return None         
        

Emitter.register('html', HTMLEmitter, 'text/html')
