from django.db import models
from authentication import DjangoAuthentication, NoAuthentication
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from custom_filters import filter_to_method
from icetea.utils import UnprocessableEntity

# mappings of {HTTP Request: API Handler method}
CALLMAP = {
    'GET': 'read',
    'PUT': 'update',
    'POST': 'create',
    'DELETE': 'delete',
}

class BaseHandlerMeta(type):
    """
    Allows a handler class definition to be different from a handler class
    type. This is useful because it enables us to set attributes to default
    values without requiring an explicit value in their definition. 
    """
    
    def __new__(meta, name, bases, attrs):
        
        # For operations which have been declared in a handler with
        # ``operation=True``, eg ``read=True``, we remove the operation from
        # the handler's attributes, so that the attribute instead points to the
        # method that implements the operation
        for operation in CALLMAP.values():
            attrs.setdefault(operation, False)
            if attrs.get(operation) is True:
                del attrs[operation]
        
        # At this point, the  enabled operations are:
        #       - those that have been enabled as <operation> = True. These keep    
        #         the default implementation of the superclass.
        #       - the ones that have been overwritten explicitly in the handler.

        cls = type.__new__(meta, name, bases, attrs)
        
        # Construct the `allowed_methods`` attribute
        cls.allowed_methods = tuple([method
            for method, operation in CALLMAP.iteritems()
            if callable(getattr(cls, operation))])

        # Construct the ``allowed_plural`` attribute, which indicates which plural methods
        # will be permitted.
        cls.allowed_plural = list(cls.allowed_methods[:])
        if not cls.plural_update and 'PUT' in cls.allowed_plural:            
            cls.allowed_plural.remove('PUT')
        if not cls.plural_delete and 'DELETE' in cls.allowed_plural:
            cls.allowed_plural.remove('DELETE')

        # Indicates which querystring parameter will make the field selection
        if cls.request_fields is True:
            cls.request_fields = 'field'

        # Indicates which querystring parameter will request ordering
        if cls.order is True:
            cls.order = 'order'

        # Indicates which querystring parameter will request data slicing
        if cls.slice is True:
            cls.slice = 'slice'

        # Indicates Authentication method.
        if cls.authentication is True:
            cls.authentication = DjangoAuthentication() 
        else:
            cls.authentication = NoAuthentication()      

        # For ``ModelHandler`` classes, forbid incoming fields that are primary
        # keys. We wouldn't like anyone to try to alter a primary key of any
        # model instance. 
        # TODO: Is it enough to just forbid the ``id`` field?
        if 'model' in attrs and cls.model != None:
            cls.allowed_in_fields = [ \
                field for field in cls.allowed_in_fields if \
                field != 'id'
            ]

        return cls

class BaseHandler():
    """
    All handlers should (directly or indirectly) inherit from this one. Its
    public attributes and methods were designed with extensibility in mind, so
    don't hesitate to override.
    """
    __metaclass__ = BaseHandlerMeta
            

    allowed_out_fields = ()
    """
    Specifies the set of fields that are allowed to be included in a response.
    It's an iterable of field names.

    Mandatory to declare it

    In case that we wish a more flexible output field selection, we should
    overwrite method :meth:`.get_output_fields`

    It only makes sense in the case of ModelHandler classes. BaseHandler
    classes, return whatever they want anyway.
    """

    allowed_in_fields = ()
    """
    Specifies the set of allowed incoming fields. 

    Mandatory to declare it.

    TODO: Add check in metaclass, and make sure that no primary keys are
    allowed. EG. no 'id' field should be allowed here.
    """

    request_fields = True
    """
    Determines if request-level fields selection is enabled. Should be the
    name of the query string parameter in which the selection can be found.
    If this attribute is defined as ``True`` (which is the default) the
    default parameter name ``field`` will be used. Note that setting to (as
    opposed to "defining as") ``True`` will not work. Disable request-level
    fields selection by defining this as ``False``.
    """
    
    authentication = None
    """
    The authenticator that should be in effect on this handler. If
    defined as ``True`` (which is not the same as assigning ``True``, as this
    will not work) an instance of
    :class:`.authentication.DjangoAuthentication` is used. A value of ``None``
    implies no authentication, which is the default.
    """

    bulk_create = False
    """
    Indicates whether bulk POST(creating multiple items with one request) requests are allowed.
    """

    plural_update = False
    """
    Indicates whether plural PUT(updating multiple resources at once) requests
    are allowed.
    """

    plural_delete = False
    """
    Indicates whether plural DELETE(Deleting multiple resources at once)
    requests are allowed.
    """
                         
    order = False
    """
    Order data query string parameter, or ``True`` if the default (``order``)
    should be used. Disabled (``False``) by default.
    """

    slice = False
    """
    Slice data query string parameter, or ``True`` if the default (``slice``)
    should be used. Disabled (``False``) by default.
    """

    

    def get_output_fields(self, request):
        """
        Returns the fields that the handler can output, for the current request
        being served.
        It takes into account the ``allowed_out_fields`` tuple, as well as
        any request-level field selection that might have taken place.

        If the selection of fields indicates that the response should contain
        no fields at all(which doesn't really make sense), we instead respond
        with all fields in ``allowed_out_fields``.

        In the case of a BaseHandler, the fields returned
        by this function, basically have the sense of dictionary keys allowed
        to be returned, If the data which is resulf ot the execution of the operation(say the
        read() method) is a dictionary. If the response is for example a
        string, the fields returned by this method have no sense at all..
        """
        selection = ()
        requested = request.GET.getlist(self.request_fields)

        # Make sure that if ``field=`` is given(without specifying value), we
        # consider that no request level field-selection has been made.
        if requested == ['']:
            requested = ()

        if requested:
            selection = set(requested).intersection(self.allowed_out_fields)

        return selection or self.allowed_out_fields            
    
    def validate(self, request, *args, **kwargs):
        """
        Should be overwritten if we need any specific validation of the
        request body
        """
        pass        
    
    def data(self, request, *args, **kwargs):
        """
        Returns the data that is the result of the current operation, without
        having to specify if the request is singular or plural.
        """
        
        data = self.data_item(request, *args, **kwargs)
        if data is None:
            data = self.data_set(request, *args, **kwargs)
        return data
                              
    def data_item(self, request, *args, **kwargs):
        """
        Returns the data item that is being worked on. This is how the handler
        decides if the requested data is singular or not. By returning
        ``None`` we signal that this request should be handled as a request
        for a set of data, as opposed to a request for a single record.
        """
        return None
     
    def data_set(self, request, *args, **kwargs):
        """
        Returns the operation's result data set, which is always an iterable.
        The difference with :meth:`~working_set` is that it returns the data
        *after* all filters and ordering (not slicing) are applied.
        """
        
        data = self.working_set(request, *args, **kwargs)
        
        filters = self.filters or {}
        if filters:
            for name, definition in filters.iteritems():
                values = request.GET.getlist(name)
                if values:
                    try:
                        data = self.filter_data(data, definition, values)
                    except ValueError:
                        # Happens when giving invalid filter type data, like
                        # for example providing a string instead of integer.
                        raise UnprocessableEntity('Invalid filter data')
        
        order = request.GET.getlist(self.order)
        if order:
            data = self.order_data(data, *order)
        
        return data

    def working_set(self, request, *args, **kwargs):
        """                                                          
        Returns the operation's base dataset. No data beyond this set will be
        accessed or modified.
        Returns the operation's base data set. No data beyond this set will be
        accessed or modified. The reason why we need this one in addition to
        :meth:`~data_set` is that :meth:`~data_item` needs to have a data set
        to pick from -- we need to define which items it is allowed to obtain
        (and which not). This data set should not have user filters applied
        because those do not apply to item views.
        """
        raise NotImplementedError
  
    def filter_data(self, data, definition, values):
        """
        Applies user filters (as specified in :attr:`.filters`) to the
        provided data. Does nothing unless overridden with a method that
        implements filter logic.
        """
        return data
    
    def order_data(self, data, *order):
        """
        Orders the provided data. Does nothing unless overridden with a method
        that implements ordering logic.
        """
        return data
    
    def response_slice_data(self, data, request, total=None):
        """
        ``@param data``: Dataset to slice
        ``@param request``: Incoming request object 
        ``@total``: Total items in dataset (Has a value only if invoked by
        :meth:`.ModelHandler.response_slice_data`

        ``@return``: Returns a list (sliced_data, total):
        
        * ``sliced_data``: The final data set, after slicing. If no slicing has
          been performed, the initial dataset will be returned
        * ``total``:  Total size of initial dataset. None if no slicing was
          performed.
        """
        # Is slicing allowed, and has it been requested?
        slice = request.GET.get(self.slice, None)
        if not slice:
            return data, None
        
        if not total:
            total = len(data)
        
        slice = slice.split(':')

        # Gather all slice arguments
        process = []
        for i in range(3):
            try:
                slice_arg = int(slice[i])
            except (IndexError, ValueError):
                slice_arg = None
            finally:
                process.append(slice_arg)
        
        return self.slice_data(data, *process), total
        
    def slice_data(self, data, start=None, stop=None, step=None):
        """
        Slices and returns the provided data according to *start*, *stop* and *step*.
        If the data is not sliceable, simply return it
        """
        try:
            return data[start:stop:step]
        except:
            # Allows us to run *response_slice_data* without having to worry
            # about if the data is actually sliceable.
            return data
    
    def execute_request(self, request, *args, **kwargs):
        """
        All requests are entering the handler here.

        It returns a dictionary of the result. The dictionary only contains:

        * ``data: <data result>``: ``data result`` is a dictionary, if that was
          possible.
        * ``total: <Number>``: if slicing was performed
        * ``<key>: <value>``: if  :meth:`.ModelHandler.enrich_response` has been overwritten

        The dictionary values are simply text. The nested models, queryset and
        everything else, have been serialized as text, within this dictionary.       
        """
        # Validate request body data
        if hasattr(request, 'data') and request.data is not None:
            if request.method.upper() == 'PUT':
                # In the case of PUT requests, we first force the evaluation of
                # the affected dataset (theforore if there are any
                # HttpResourseGone exceptions, will be raise now), and then in the
                # ``validate`` method, we perform any data validations.
                dataset = self.data(request, *args, **kwargs)              
                kwargs['dataset'] = dataset
            self.validate(request, *args, **kwargs)
        
        # Pick action to run
        action = getattr(self,  CALLMAP.get(request.method.upper()))
        # Run it
        data = action(request, *args, **kwargs)
        # Select output fields
        fields = self.get_output_fields(request) 
        # Slice
        sliced_data, total = self.response_slice_data(data, request)
        # Add extra fields to the data items in the response
        self.add_extra_fields(sliced_data, fields, request)
        
        # Use the emitter to serialize the ``data``. The emitter is responsible for
        # allowing only fields in ``fields``, if such a selection makes sense.
        # Depending on ``data``'s type, after the serialization, it becomes
        # either a dict, list(of strings, dicts, etc) or string.
        from emitters import Emitter
        emitter = Emitter(sliced_data, self, fields)       
        ser_data = emitter.construct()

        # Structure the response data
        ret = {}
        ret['data'] = ser_data
        if total:
            ret['total'] = total
        # Add extra metadata
        self.enrich_response(ret, data)

        if request.method.upper() == 'DELETE':
            self.data_safe_for_delete(data)

        return ret

    def enrich_response(self, response_structure, data):
        """
        Overwrite this method in your handler, in order to add more (meta)data
        within the response data structure.
    
        ``@param response_structure``: Dictionary that includes at least the
        {'data': <data>} pair.
        ``@param data``: The (unsliced) data result of the operation 
        """
        pass

    def add_extra_fields(self, data, fields, request):
        """
        Overwrite this method in the handler, if you want to add any artificial
        fields within the data that will be packed in the response.
        It follows the slicing of the data, so that it only processes the data
        that will actually be returned.
        
        ``@param data``: Sliced data

        ``@param fields``: Fields to output

        ``@param request``: Incoming request object
        """
        pass
    
    def create(self, request, *args, **kwargs):
        """
        Default implementation of a create operation, put in place when the
        handler defines ``create = True``.
        """
        return request.data
    
    def read(self, request, *args, **kwargs):
        """
        Default implementation of a read operation, put in place when the
        handler defines ``read = True``.
        """
        return self.data(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """
        Default implementation of an update operation, put in place when the
        the handler defines ``update = True``.
        """
        # If *request.data* is not an appropriate response, we should *make*
        # it an appropriate response. Never directly use *self.data*, as that
        # one can in no way be considered the result of an update operation.
        return request.data
    
    def delete(self, request, *args, **kwargs):
        """
        Default implementation of a delete operation, put in place when the
        the handler defines ``delete = True``.
        """
        return self.data(request, *args, **kwargs)
    
    def data_safe_for_delete(self, data):
        """
        If we want the delete operation to remove data without impacting the
        data in the response we can do it safely here.
        """
        pass


class ModelHandler(BaseHandler):
    """
    Provides off-the-shelf CRUD operations on data of a certain model type.
    
    Note that in order to prevent accidental exposure of data that was never
    intended to be public, model data fields will not be included in the
    response if they are not explicitly mentioned in
    :attr:`~BaseHandler.allowed_in_fields`. 
    """    
    model = None
    """
    A model class of type :class:`django.db.models.Model`.
    """
    
    exclude_nested = ()
    """
    A list of field names that should be excluded from the fields selection in
    case of a nested representation; eg. when the model is contained by
    another model object.
    """
 
    filters = False
    """
    Dictionary specifying data filters, in pairs of ``name: filter``. 
    
    ``name`` is the querystring parameter used to trigger the filter.

    ``filter`` defines the field on  which the filter will be applied on, as well as (implicitly or explicitly)
    the type of field lookup.

    For example, ``filters = dict(id=id__in)``, defines that the querystring
    parameter ``id``, will trigger the Django field lookup ``id__in``, with the
    value given to ``id``. So, the querystring ``?id=12&id=14``, will perform
    the filter ``filter(id__in=[12, 14]``), on the corresponding model.
    """
 

    read = True
    create = True
    update = True
    delete = True

    def validate(self, request, *args, **kwargs):
        """
        Turns the data on the request into model instances; a new instance
        with the ``POST``'ed data or a current instance to be updated with the 
        ``PUT``'ed data.
        The model instances have been validated using Django's ``full_clean()``
        method, so we can be sure that they are valid model instances, ready to
        hit the database. This can be seen as something totally similar to Django ModelForm
        validation.         
        
        After this method, we shouldn't perform modifications on the model
        instances, since any modifications might make the data models invalid.
        """
        super(ModelHandler, self).validate(request, *args, **kwargs)

        if request.method.upper() == 'POST':
            # Create model instance(s) without saving them, and go through all
            # field level validation checks.
            if not isinstance(request.data, list):
                request.data = self.model(**request.data)
                try:                    
                    request.data.full_clean()                    
                except ObjectDoesNotExist, e:
                    # There is a weird case, when if a Foreign Key on the model
                    # instance is not defined, and this foreign key is used in
                    # the __unicode__ method of the model, to derive its string
                    # representation, we get a ``DoesNotExist``exception.
                    # #TODO: Is this a bug though? 
                    # It can also be dealt with by removing the use of the FK
                    # from the model's unicode method, but that would require a
                    # lot of manual work
                    raise ValidationError('Foreign Keys on model not defined')

            else:
                request.data = [self.model(**data_item) for \
                    data_item in request.data]
                for instance in request.data:
                    try:
                        instance.full_clean()
                    except ObjectDoesNotExist, e:
                        raise ValidationError('Foreign Keys on model not defined')

        elif request.method.upper() == 'PUT':      
            current = kwargs.pop('dataset', None)  # Evaluated in ``execute_request``        

            def update(current, data):
                update_values = data.items()
                for instance in isinstance(current, self.model) and [current]\
                    or current:
                    for field, value in update_values:
                        setattr(instance, field, value)
                    instance.full_clean()   
            # Update all model instances in ``current``, with the data from the
            # reqeust body.
            update(current, request.data)
            
            request.data = current
  

    def working_set(self, request, *args, **kwargs):
        """
        Returns the working set of the model handler. It should be the whole
        queryset of the model instances, with filtering made only based on
        keyword arguments.

        .. note::
            Keyword arguments are defined in the URL mapper, and are usually in
            the form of ``/api endpoint/<id>/``.

            For faster query execution, consider the
            use of `select_related
            <https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-related>`_
            Be aware though, that it is very `memory-intensive
            <https://code.djangoproject.com/ticket/17>`_. A middle-of-the-way
            solution would probably be to use it with the ``depth`` parameter.
        """
        return self.model.objects.filter(**kwargs)
    
    def data_item(self, request, *args, **kwargs):
        """
        Returns a single model instance, if such has been pointed out. Else the
        super class returns None.
        """
        # First we check if we have been provided with conditions that are
        # capable of denoting a single item. If we would try to ``get`` an
        # instance based on *kwargs* right away, things would go wrong in case
        # of a set with one element. This element would be returned by this
        # method as if it was explicitly requested.
        for field in kwargs.keys():
            try:
                if self.model._meta.get_field(field).unique:
                    # We found a parameter that identifies a single item, so
                    # we assume that singular data was requested. If the data
                    # turns out not to be there, an ``ObjectDoesNotExist``
                    # exception will be raised.
                    return self.working_set(request, *args, **kwargs).get(**{ field: kwargs.get(field) })
            except models.FieldDoesNotExist:
                # No field named *field* on *self.model*, try next field.
                pass
        return super(ModelHandler, self).data_item(request, *args, **kwargs)
    
    def filter_data(self, data, definition, values):
        """
        ``@param data``: Data on which the filter will be applied

        ``@param definition``: Filter definition. Could be:
        
        * A Django `field lookup
          <https://docs.djangoproject.com/en/dev/topics/db/queries/#field-lookups>`_,
          defining both the field and the lookup. For example ``id__in``, which
          defines the field ``id`` and the lookup filter to be applied upon it.
        * A `a custom filter` as defined in :mod:`~custom_filters`, defining
          both the field and the filter. For example, ``emails__in_list``,
          which defines the field ``emails`` and the filter ``__in_list`` to be
          applied upon it.
        * A tuple defining the fields on which an OR based Full Text search will be performed.
          For example ``('name', 'surname')``.

        ``@param values``: The values to be applied on the filter.
        """
        if isinstance(definition, basestring):
            # If the definition's suffix is equal to the name of a custom
            # lookup filter, call the corresponding method.
            for lookup in filter_to_method:
                if definition.endswith(lookup):
                    return filter_to_method[lookup](data, definition, values)
            return data.filter(**{ definition: values })
        
        if isinstance(definition, (list, tuple, set)):
            # definition: List of fields to filter based on
            # values: list of terms to apply on each field for filtering.
            # For every value, we apply an OR among all definitions
            # We AND all partial queries generated for very value.
                                                                                 
            query = models.Q()
            
            for value in values:
                partial_query = models.Q()
                for field in definition:
                    partial_query = partial_query | models.Q(**{'%s__icontains' % field:value})                     
                query = query & partial_query
            return data.filter(query)
        
        return data
    
    def order_data(self, data, *order):
        return data.order_by(*order)
    
    def response_slice_data(self, data, request):
        """
        Slices the ``data`` and limits it to a certain range.

        ``@param data``: Dataset to slice

        ``@param request``: Incoming request

        ``@return``: Returns a tuple (sliced_data, total)

         * sliced_data: The final data set, after slicing. If no slicing has
           been performed, the initial dataset will be returned
         * total:       Total size of initial dataset. None if no slicing was
           performed.
        """
        # Single model instance cannot be sliced
        if isinstance(data, self.model) or not request.GET.get(self.slice, None):
            return data, None
        
        # Slicing is allowed, and has been requested, AND we have a queryset
        total = data.count()
                 
        # ``data`` gets sliced
        sliced_data, _ = super(ModelHandler, self).response_slice_data(data, request, total)
                            
        # Return sliced, total
        return sliced_data, total

    def create(self, request, *args, **kwargs):
        """
        Saves the model instances available in ``request.data``. Returns the
        subset of ``request.data`` which contains the successfully created
        model instances.
        """
        if not isinstance(request.data, self.model):
            unsuccessful = []
            for instance in request.data:
                try:
                    instance.save(force_insert=True)
                except:
                    unsuccessful.append(instance)
            if unsuccessful:
                # Remove model instances that were not saved successfully, from
                # ``request.data``
                request.data = set(request.data) - set(unsuccessful)
        else:
            # request.data is a single self.model instance
            try:
                request.data.save(force_insert=True)
            except:
                # Not sure what errors we could get, but I think it's safe to just
                # assume that *any* error means that no record has been created.
                request.data = None
        
        return super(ModelHandler, self).create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """
        Saves (updates) the model instances in ``request.data``. Returns the
        subset of ``request.data`` which contains the successfully updated
        model instances.
        """
        def persist(instance):
            try:
                instance.save(force_update=True)
                return instance
            except:
                return None
        
        if isinstance(request.data, self.model):
            request.data = persist(request.data)
        elif request.data:
            request.data = [instance for instance in request.data if persist(instance)]
        
        return super(ModelHandler, self).update(request, *args, **kwargs)
    
    def data_safe_for_delete(self, data):
        """
        We only run this method AFTER the result data have been serialized into
        text. If we had ran it earlier, then the model instances of the result
        set would have been deleted, hence their ``id `` field would have been
        equal to ``None``, and hence their ``id`` would not be available for
        serialization.        
        """
        if data:
            data.delete()

        return super(ModelHandler, self).data_safe_for_delete(data)
