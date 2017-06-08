import StringIO
import decimal
import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.db.models import Model
from django.db.models.fields import FieldDoesNotExist
from django.db.models.query import QuerySet
from django.db.models.related import RelatedObject
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator


# Wrapped the ``import xlwt`` in try/catch, otherwise sphinx crashes.
try:
    import xlwt
except ImportError:
    pass


class Emitter(object):
    """
    Super emitter. All other emitters should subclass this one.

    Its L{Emitter.construct} method returns a dictionary, list or string, of
    whatever data it is given. This is basically a serializable representation
    of I{self.data}, and is typically the only method that a custom emitter
    needs.

    The custom emitter will then take this serializable data, and serialize it
    into any format(JSON, XML, wtc) it needs to.
    """
    # List of registered emitters
    EMITTERS = {}

    # Maps pairs of {<API Handler class>: <Model>}
    TYPEMAPPER = {}

    def __init__(self, handler, payload, fields=()):
        # API Handler, handling this request
        self.handler = handler
        # Data to be serialized
        self.data = payload
        # Fields that the handler needs to output
        self.fields = fields

        if isinstance(self.data, Exception):
            raise

    def construct(self):
        """
        Recursively serialize a lot of types, and in cases where it doesn't
        recognize the type, it will fall back to Django's I{smart_unicode}.

        Returns a serializable representation of I{self.data}.
        """
        def _any(thing, fields=(), nested=False):
            """
            Dispatch, all types are routed through here.

            @param thing:  Data we are trying to serialize.
            @param fields: The fields of I{thing} to serialize. Relevant only
            for models and dictionaries.
            @param nested: Are the fields of I{thing} nested, or are they
            first class fields? This is relevant only for models.
            """
            ret = None

            if isinstance(thing, QuerySet):
                ret = _qs(thing, fields, nested)

            elif isinstance(thing, Model):
                ret = _model(thing, fields, nested)

            elif isinstance(thing, (tuple, list, set)):
                ret = _list(thing, fields, nested)

            elif isinstance(thing, dict):
                ret = _dict(thing, fields)

            elif isinstance(thing, decimal.Decimal):
                ret = str(thing)

            else:
                ret = smart_unicode(thing, strings_only=True)

            return ret

        def _model(data, fields=(), nested=False):
            """
            Models.

            @type data: Model
            @param data: Model instance that we need to represent as a dict

            @type fields: tuple
            @param fields: Model fields that we are allowed to output. This is
            only relevant if nested==False. If nested==True, then the
            fields that we can output are decided by:
                handler.allowed_out_fields - handler.exclude_nested.

            @type nested: bool
            @param nested: True if model is nested in the data response

            @rtype: dict
            @return: Serializable representation of model I{data}

            If there is no handler responsible for constructing the
            representation of the model type that ``data`` belongs to, the
            method will try to construct a default representation of the data.
            """
            def _fk(data, field):
                """
                Serializes and returns the FK field ``field`` of the data model
                ``data``. FK fields are always nested.
                """
                return _any(getattr(data, field.name), fields=(), nested=True)

            def _m2m(data, field):
                """
                Serializes and returns the many-to-many field ``field`` of the
                ``data`` model instance. Many-to-Many fields are always nested.
                """
                return [_model(m, fields=(), nested=True)
                        for m in getattr(data, field.name).iterator()]

            def _related(data):
                """
                Serializes and returns the RelatedManager ``data``. ``data``
                represents a QuerySet which is a backwards relationshop to the
                model from which we came here. Related fields are always
                nested.
                """
                return [_model(m, fields=(), nested=True)
                        for m in data.iterator()]

            def get_fields(handler, fields, nested):
                """
                Returns a tuple with the final output field names.
                """
                # If the model is nested, we assemble the fields with the
                # following formula
                if nested:
                    fields = set(handler.allowed_out_fields) - set(handler.exclude_nested)

                # If the model is not nested, and the ``fields`` is still
                # empty, then we use the ``allowed_out_fields`` that the API
                # handler for model type of ``data`` defined.  (When could this
                # happen? In the case that a BaseHandler would like to return a
                # model instance of type A as a first class citizen. If that
                # BaseHandler has an empty ``allowed_out_fields`` tuple, but
                # the Handler for the model A would dictate a different
                # representation. Then we use the representation that the
                # handler for A defined.
                elif not fields:
                    fields = handler.allowed_out_fields
                return fields

            ret = {}
            handler = self.in_typemapper(data)

            if handler:
                fields = get_fields(handler, fields, nested)

                for field_name in fields:
                    # Try to retrieve the field by name
                    try:
                        field_object, model, direct, m2m = data._meta.get_field_by_name(field_name)

                        # Django 1.7 and up now include the field attname in
                        # the Options name.map. This means that both the field
                        # name and field attname will be found by
                        # `get_field_by_name`. For example the following
                        # definition:
                        #
                        # class Foo(models.Model):
                        #      bar = ForeignKeyField(...)
                        #
                        # In Django 1.6 get_field_by_name("bar_id") would raise
                        # a FieldDoesNotExist exception but starting in 1.7 it
                        # will return the field.
                        #
                        # This is a work around to maintain the 1.6 behaviour.
                        if direct and field_object.rel is not None and field_name.endswith("_id"):
                            raise FieldDoesNotExist

                    except FieldDoesNotExist:
                        # Field is not a physical model field.
                        # So it's either a fake static field, or a fake dynamic
                        # field.
                        # In the first case, it is defined in the model's
                        # ``_fake_static_fields`` tuple. So we invoke the
                        # ``_compute_fake_static_field`` method to get its
                        # value.
                        # In the second case, its value has already been
                        # computed in the handler, so we simple read the value
                        # and serialize it.

                        # So, is it a fake static field?
                        if hasattr(data, '_fake_static_fields'):
                            if field_name in data._fake_static_fields:
                                try:
                                    ret[field_name] = _any(data._compute_fake_static_field(field_name))
                                except AttributeError:
                                    raise
                                else:
                                    continue

                        # Then it's a fake dynamic field
                        try:
                            ret[field_name] = _any(getattr(data, field_name))
                        except:
                            # Field hasn't been found on this model.
                            # It's most likely defined as a fake dynamic field,
                            # but has never been populated on this model
                            # instance. This means there's most likely a bug in
                            # the handler's ``inject_fake_dynamic_fields``
                            # method.
                            continue

                    # The field ``field_object`` is a physical model field.
                    else:
                        try:
                            value = getattr(data, field_name)
                        except (AttributeError, ObjectDoesNotExist):
                            # Happens if the field f does not exist on this
                            # model instance.
                            # For example: model class B inherits from model
                            # class A. Therefore, every instance of A has
                            # ReverseObject references to B. However, a pure
                            # instance of model A, will throw a DoesNotExist
                            # exception when trying to read the reference to B.
                            continue

                        # ``field_name``: Name of the field (string)
                        # ``value``: Value of the field
                        # ``field_object``: Instance of a subclass of
                        #                   ``django.models.db.fields.Field``

                        # Check if the field is a RelatedManager object(reverse
                        # FK)
                        if not direct and not m2m:
                            ret[field_name] = _related(value)
                            continue

                        # Check if the field is many_to_many
                        elif not direct and m2m:
                            if field_object.serialize:
                                ret[field_name] = _m2m(data, field_object)
                                continue

                        # Check if the field is a RelatedObject instance.
                        # Happens when a modelB inherits from modelA. In that
                        # case, in the representation of modelA, the modelB
                        # instance appears as a RelatedObject.
                        elif isinstance(field_object, RelatedObject):
                            ret[field_name] = _model(value)

                        # Check if it is a local field or virtual field
                        elif (field_object in (data._meta.local_fields + data._meta.virtual_fields)
                                and hasattr(field_object, 'serialize')
                                and field_object.serialize):
                            # Is it a serializable physical field on the model?
                            if not field_object.rel:
                                ret[field_name] = _any(value)
                                continue
                            # Is it a foreign key?
                            else:
                                ret[field_name] = _fk(data, field_object)
                                continue

                        # Else simple try to serialize the value
                        else:
                            ret[field_name] = _any(value)
                            continue

            # No handler could be found. So we fallback to the string
            # represenation of the model instance
            else:
                ret = smart_unicode(data, strings_only=True)

            return ret

        def _qs(data, fields=(), nested=False):
            """
            Querysets.

            Queryset data might be both nested or first class citizens of the
            representation.
            """
            return [_any(v, fields, nested) for v in data]

        def _list(data, fields=(), nested=False):
            """
            Lists.
            """
            return [_any(v, fields, nested) for v in data]

        def _dict(data, fields=()):
            """
            Dictionaries.

            The values of dictionaries should always be considered nested.
            """
            # If there is field selection selection, output only allowed
            # fields. Else, output all fields
            if fields:
                return dict([(k, _any(v, fields=(), nested=True)) for k, v in data.iteritems() if k in fields])
            else:
                return dict([(k, _any(v, fields=(), nested=True)) for k, v in data.iteritems()])

        # kickstart
        return _any(self.data, self.fields, nested=False)

    def in_typemapper(self, model_instance):
        """
        Returns the I{model}'s associated API handler.
        """
        # First check whether this model instance belongs to a class
        # which is directly mapped in the TYPEMAPPER
        for _handler, _model in self.TYPEMAPPER.items():
            if type(model_instance) is _model:
                return _handler

        # Else, check whether one of its superclasses is mapped
        # in the typemapper (this is useful in cases ``model_instance``
        # is not a pure model instance, but rather a Deferred one.
        for _handler, _model in self.TYPEMAPPER.items():
            if isinstance(model_instance, _model):
                return _handler

    def render(self):
        """
        This super emitter does not implement I{render},
        this is a job for the specific emitter below.
        """
        raise NotImplementedError("Please implement render.")

    @classmethod
    def get(cls, format):
        """
        Gets an emitter, returns the class and a content-type.
        """
        if format in cls.EMITTERS:
            return cls.EMITTERS.get(format)

        raise ValueError("No emitters found for type %s" % format)

    @classmethod
    def register(cls, name, klass, content_type='text/plain'):
        """
        Register an emitter.

        Parameters:

        * name: The name of the emitter ('json', 'xml', 'yaml', ...)
        * klass: The emitter class.
        * content_type: The content type to serve response as.
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
        # I{self.data} is already in a serializable form, since it can only
        # contain any of the following python data structures: dict, list, str.
        # So here we simply serialize it into JSON.
        return json.dumps(self.data, cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=4)


Emitter.register('json', JSONEmitter, 'application/json; charset=utf-8')


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

                # I show lists or dicts to comma-separated strings
                if isinstance(field_value, list):
                    if field_value:
                        field_value = [to_utf8(item) for item in field_value]
                        value = ", ".join(field_value)
                elif isinstance(field_value, dict):
                    if field_value:
                        value = ", ".join(to_utf8(key) + ": " + to_utf8(value) for key, value in
                            field_value.items())
                else:
                    value = to_utf8(record[key])

                ws.write(row, col, value)
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
            if (isinstance(construct['data'], dict)
                    and len(construct['data']) == 1):
                return construct['data'].values()[0]
            else:
                return construct['data']

        elif 'errors' in construct:
            # Validation was raised
            return construct['errors']

        return None


Emitter.register('html', HTMLEmitter, 'text/html')
