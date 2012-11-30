import decimal, inspect, StringIO
from django.db.models.query import QuerySet
from django.db.models import Model
from django.db.models.fields import FieldDoesNotExist
from django.utils import simplejson
from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.encoding import smart_unicode
from django.core.serializers.json import DateTimeAwareJSONEncoder

# Class which will register MimeTypes to methods that will decode the
# corresponding MimeType to python data structures.
from utils import Mimer

# Wrapped the ``import xlwt`` in try/catch, otherwise sphinx crashes. WTF!!
try:
	import xlwt
except ImportError:
	pass

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

    """
    EMITTERS = { }
    # Maps pairs of {<API Handler class>: <Model>}
    TYPEMAPPER = {}

    def __init__(self, payload, handler, fields=()):
        # Data to be serialized
        self.data = payload
        # API Handler, handling this request        
        self.handler = handler
        # Fields that the handler needs to output
        self.fields = fields

        if isinstance(self.data, Exception):
            raise

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
                ret = _any(thing.all(), fields, nested)

            else:
                ret = smart_unicode(thing, strings_only=True)

            return ret

        def _fk(data, field):
            """
            The field ``field`` is a FK of the ``data`` model instance.
            
            FK fields are always nested.
            """
            return _any(getattr(data, field.name), fields=(), nested=True)

        def _m2m(data, field):
            """
            The field ``field`` is a many-to-many field of the ``data`` model
            instance.

            Many-to-Many fields are always nested.
            """
            return [ _model(m, fields=(), nested=True) for m in getattr(data, field.name).iterator() ]

        def _related(data):
            """
            ``data`` is a RelatedManager, so it represents a Queryset which a
            backwards relationship to the model from which we came here.

            Related fields are always nested.
            """
            return [ _model(m, fields=(), nested=True) for m in data.iterator() ]

        # TODO: Study it again, and get rid of all its garbage.
        def _model(data, fields=(), nested=False):
            """
            Models. 
            
            @param data: Model instance
            @param fields: Model fields that we are allowed to output. This is
            only relevant if nested==True. If nested==False, then the
            fields that we can output are decided by:
                handler.allowed_out_fields - handler.exclude_nested.
            @param nested: True if model is nested in the data response

            If there is no handler responsible for constructing the
            representation of the model type that ``data`` belongs to, the
            methodr will try to construct a default representataion of the
            data.
            """
            ret = {}
            handler = self.in_typemapper(type(data))

            if nested and handler:
                # If ``data`` is nested, we assemble the fields to output
                fields = set(handler.allowed_out_fields) - set(handler.exclude_nested)
            
            if handler:
                # If the ``data`` model is not nested, and ``fields`` is still
                # empty, then we use the ``allowed_out_fields`` that the API
                # handler for the model type of ``data``, allowes.
                # (When could that happen? In the case that a BaseHandler would 
                # like to return a model instance as a first class citizen. The
                # BaseHandler could have an empty ``allowed_out_fields`` tuple,
                # but the Handler for the models ``type(data)`` would dictate a
                # different representation).
                if not nested and not fields:
                    fields = handler.allowed_out_fields

                # Function that retrieves the value of the field ``f``
                v = lambda f: getattr(data, f.attname)

                for field_name in fields:   
                    f = None

                    # Try to retrieve the field by name
                    try:
                        f = data._meta.get_field_by_name(field_name)[0]
                    except FieldDoesNotExist:                         
                        # Field is not a physical model field. So we look in
                        # the ``fake_fields`` tuple of the model class.
                        # Check if any of the fields that we want to output, are
                        # included in the model's ``fake_fields`` list. If yes,
                        # evaluate them using the model's ``_compute_fake_fields()`` method.
                        if hasattr(data, 'fake_fields'):
                            if field_name in data.fake_fields:
                                try:
                                    ret[field_name] = data._compute_fake_fields(field_name)
                                except AttributeError:
                                    raise
                                else:
                                    continue

                    # The field ``f`` is a physical model field.
                    else:                               
                        # Check if it is a related field
                        value = getattr(data, field_name)
                        if hasattr(value, 'all'):
                            # value is a RelatedManager object
                            ret[field_name] = _related(value)
                            continue

                        # Check if it is a many_to_many field
                        elif f in data._meta.many_to_many:
                            if f.serialize:
                                ret[field_name] = _m2m(data, f)
                                continue                   

                        # Check if it is a local field or virtual field
                        elif f in (data._meta.local_fields + data._meta.virtual_fields)\
                        and hasattr(f, 'serialize')\
                        and f.serialize:
                            # Is it a serializable physical field on the model?
                            if not f.rel:
                                ret[field_name] = _any(v(f))
                                continue
                            # Is it a foreign key?
                            else:
                                ret[field_name] = _fk(data, f)
                                continue

                        # Else try to read the value of the field from the
                        # model
                        else:
                            ret[field_name] = _any(v(f))
                            continue

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

            If the values of the dictionary are models or querysets, they
            should appear as nested.
            """
            # If there is field selection selection, output only allowed
            # fields. Else, output all fields
            if fields:
                return dict([ (k, _any(v, fields=(), nested=True)) for k, v in data.iteritems() if k in fields])
            else:
                return dict([ (k, _any(v, fields=(), nested=True)) for k, v in data.iteritems()])

        return _any(self.data, self.fields, nested=False)


    def in_typemapper(self, model):
        """
        Returns the ``model``'s associated API handler.
        """
        for _handler, _model in self.TYPEMAPPER.iteritems():
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
        data_as_dic = self.construct()
        seria = simplejson.dumps(data_as_dic, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=4)

        return seria
Emitter.register('json', JSONEmitter, 'application/json; charset=utf-8')
Mimer.register(simplejson.loads, ('application/json',))

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
            """ 
            Return the unicode repsesentation of string
            """
            try:
                return unicode(string)
            except UnicodeDecodeError:
                # the string is a bytestring
                ascii_text = str(string).encode('string_escape')
                return unicode(ascii_text)
        def to_utf8(string):
            """
            Return the utf-8 encoded representation of the string 
            """
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
        
        ws = wb.add_sheet("Sheet")
        
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
            # If the ``construct['data']`` is dictionary(hence the request was
            # singular), and only contains one field,
            # we can simmly output the  ``value`` of this field. 
            # Else, we simply output the whole data structure 
            # as is (altough it doesn't make much sense).
            if isinstance(construct['data'], dict)\
            and len(construct['data']) == 1:
                return construct['data'].values()[0]
            else:
                return construct['data']

        elif 'errors' in construct:
            # Validation was raised
            return construct['errors']

        return None         
Emitter.register('html', HTMLEmitter, 'text/html')
