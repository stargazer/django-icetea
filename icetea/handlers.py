from django.db import models
from authentication import DjangoAuthentication, NoAuthentication
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from custom_filters import filter_to_method
from exceptions import UnprocessableEntity, ValidationErrorList
from emitters import Emitter

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

    In case that we wish a different output field selection algorithm, we should override
    method L{get_output_fields}.

    In the case of a L{ModelHandler}, it indicates the model fields that we
    wish to output. In the case of a L{BaseHandler} that for example returns a
    dictionary, it indicates the dictionary keys that we wish to output
    """

    allowed_in_fields = ()
    """
    Specifies the set of allowed incoming fields. 
    """

    request_fields = True
    """
    Specifies if request-level fields selection is enabled. 
    
    Should be the name of the query string parameter in which the 
    selection can be found.
    
    If this attribute is defined as I{True} (which is the default) the
    default parameter I{field} will be used. 
    If I{False}, request-level field selection is disabled.
    """
    
    authentication = None
    """
    The authenticator that should be in effect on this handler. If defined as
    I{True}, an instance of I{authentication.DjangoAuthentication} is used. A
    value of I{None}, implies no authentication
    """

    bulk_create = False
    """
    Specifies whether bulk POST requests(creating multiple resources in one
    request) are allowed.
    """                

    plural_update = False
    """
    Specifies whether plural PUT requests(updating multiple resources at in one request)
    are allowed.
    """

    plural_delete = False
    """
    Specifies whether plural DELETE requests(deleting multiple resources in one
    request) requests are allowed.
    """
                         
    order = False
    """
    Specifies the querystring parameter for requesting ordering of data.
    If I{True}, the default parameter I{order} will be used. 
    If I{False}, ordering is disabled.
    """

    slice = False
    """
    Specifies the querystring parameter for requesting slicing of data.
    If I{True}, the querystring parameter ``slice`` is used. If ``False``,
    slicing is disabled.
    """

    # TODO: Instead of doing so, why not simply doing like the ``slice`` and
    # ``order`` parameters.
    # excel = True # allows output to excel. default file name(file.xls) is
    #              # used
    # excel = 'string' or <callable> # allows output to excel. defiles filename
    #                                # to use.
    # excel = False # Disables excel output
    #  
    # Of course this implies that I will have some check for the requested
    # output format, and return an error if the request asks for a forbidden
    # output format.
    excel_filename = 'file.xls'
    """
    Specifies the filename used for the attachment generated when the response
    is an I{Excel} type file.

    It can either be a string, or a callable.
    """

    def get_output_fields(self, request):
        """
        Returns a tuple of the fields that the handler should output, for the current request
        being served.
        It takes into account the L{allowed_out_fields} tuple, as well as
        any request-level field selection indicated by the querystring.

        If the selection of fields indicates that the response should contain
        no fields at all(which doesn't really make sense), the response will
        instead contain all fields in L{allowed_out_fields}.

        For a L{ModelHandler}, the tuple returned by this method, indicates the
        model fields that the handler should output. For a L{BaseHandler}, it
        only has sense if the handler returns a dictionary, or a list of
        dictionaries. In that case, the tuple returned by this method,
        indicates the dictionary keys that the handler can output. If however
        the handler returns strings, the output of this method has no real
        meaning at all.
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
        Request body(I{request.data}) validation. Should be overridden if any
        specific validation is needed.
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
        for a set of data, as opposed to a request for a single resource.
        """
        return None
     
    def data_set(self, request, *args, **kwargs):
        """
        Returns the operation's result data set, which is always an iterable.
        The difference with L{working_set} is that it returns the data
        B{after} all filters and ordering (not slicing) are applied.
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
        Returns the operation's base data set. No data beyond this set will be
        accessed or modified. 
        """
        raise NotImplementedError
  
    def filter_data(self, data, definition, values):
        """
        Applies filters to the provided data.
        Does nothing unless overridden with a method that implements filter
        logic.
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
        Returns the sliced data, as well as its total size.

        @param data: Dataset to slice
        @param request: Incoming request object
        @param total: Total items in dataset (Has a value only if invoked by
        the L{ModelHandler.response_slice_data} method.
        
        @rtype: list
        @return: sliced_data, total
        
        * sliced_data: The final data set, after slicing. If no slicing has
        been performed, it will be equal to the initial dataset.
        
        * total:  Total size of initial dataset. I{None} if no slicing was
        performed.
        """
        # Is slicing allowed, and has it been requested?
        slice = request.GET.get(self.slice, None)
        if not slice:
            return data, None
        
        if total is None:
            total = len(data)
    
        return self.slice_data(data, slice), total

    def slice_data(self, data, slice):
        """
        Slices and returns the provided data.

        @param data: Dataset to slice
        @param slice: Querydict with ``slice`` parameter, as captured from the
        querystring
        
        @return: Sliced data. If data is not sliceable, simply return it as is.
        """
        slice = slice.split(':')

        # Gather all slice arguments
        slice_args = []
        for i in range(3):
            try:
                param = int(slice[i])
            except (IndexError, ValueError):
                param = None
            finally:
                slice_args.append(param)
        # start: Slicing starts here
        # stop:  Stop slicing here -1
        # step:  Step    
        start, stop, step = slice_args

        try:
            return data[start:stop:step]
        except:
            # Allows us to run L{response_slice_data} without having to worry
            # whether the data is actually sliceable.
            return data
    
    def execute_request(self, request, *args, **kwargs):
        """
        This is the entry point for all incoming requests
        (To be more precise, the URL mapper calls the
        L{resource.Resource.__call__} that does
        some pre-processing, which then calls L{execute_request} )

        It guides the request through all the necessary steps up to the point
        that its result is serialized into a dictionary.

        @type request: HTTPRequest object
        @param request: Incoming request

        @rype: dict
        @return: Dictionary of the result. The dictionary contains the
        following keys:
        
        * data: Contains the result of running the requested operation. The
        value to this key can be a dictionary, list, or string. Within this
        data structure, any dictionaries or lists are made of strings, with the
        exception of dates, which appear as I{datetime} functions, and will be
        serialized by the JSONEmitter.

        * total: Is only included if slicing was performed, and indicates the
        total result size.

        * Any other key can be included, if L{BaseHandler.enrich_response} has
        been overridden
        """
        # Validate request body data
        if hasattr(request, 'data') and request.data is not None:
            if request.method.upper() == 'PUT':
                # In the case of PUT requests, we first force the evaluation of
                # the affected dataset (theferore if there are any
                # HttpResourceGone exceptions, they will be raised now), and then in the
                # ``validate`` method, we perform any data validations. We
                # assign it to parameter ``request.dataset``.
                request.dataset = self.data(request, *args, **kwargs)              
            self.validate(request, *args, **kwargs)
        
        # Pick action to run
        action = getattr(self,  CALLMAP.get(request.method.upper()))
        # Run it
        data = action(request, *args, **kwargs)
        # Select output fields
        fields = self.get_output_fields(request) 
        # Slice
        sliced_data, total = self.response_slice_data(data, request)
        
        # Use the emitter to serialize any python objects / data structures
        # within I{sliced_data}, to serializable forms(dict, list, string), 
        # so that the specific emitter we use for returning
        # the response, can easily serialize them in some other format,
        # The L{Emitter} is responsible for making sure that only fields contained in
        # I{fields} will be included in the result.
        emitter = Emitter(sliced_data, self, fields)      
        ser_data = emitter.construct()

        # Structure the response data
        ret = {'data': ser_data}
        if total is not None:
            ret['total'] = total
        # Add extra metadata
        self.enrich_response(ret, data)

        if request.method.upper() == 'DELETE':
            self.data_safe_for_delete(data)

        return ret

    def enrich_response(self, response_structure, data):
        """
        Override this method in your handler, in order to add more (meta)data
        within the response data structure.
    
        @type response_structure: dict
        @param response_structure: Dictionary that includes the I{data} key.
        I{data} contains the sliced dataset that will be returned in the
        response.

        @param data: Contains the full(unsliced) data result of the operation

        @return: None
        """
        pass

    def create(self, request, *args, **kwargs):
        """
        Default implementation of a create operation, put in place when the
        handler defines I{create = True}.

        @type request: HTTPRequest object
        @param request: Incoming request

        @return: Result dataset
        """
        return request.data
    
    def read(self, request, *args, **kwargs):
        """
        Default implementation of a read operation, put in place when the
        handler defines I{read = True}.

        @type request: HTTPRequest object
        @param request: Incoming request

        @return: Result dataset
        """
        return self.data(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """
        Default implementation of an update operation, put in place when the
        the handler defines I{update = True}.

        @type request: HTTPRequest object
        @param request: Incoming request

        @return: Result dataset
        """
        # If *request.data* is not an appropriate response, we should *make*
        # it an appropriate response. Never directly use *self.data*, as that
        # one can in no way be considered the result of an update operation.
        return request.data
    
    def delete(self, request, *args, **kwargs):
        """
        Default implementation of a delete operation, put in place when the
        the handler defines I{delete = True}.

        @type request: HTTPRequest object
        @param request: Incoming request

        @return: Result dataset
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
    I{BaseHandler.allowed_out_fields}. 
    """    
    model = None
    """
    A Django model class.
    """
    
    exclude_nested = ()
    """
    A list of field names that should be excluded from the fields selection in
    case of a nested representation; eg. when the model is contained by
    another model object.
    """
 
    filters = False
    """
    Dictionary specifying data filters, in pairs of I{name: filter}. 
    
    I{name} is the querystring parameter used to trigger the filter.

    {filter} defines the field on  which the filter will be applied on, as well as (implicitly or explicitly)
    the type of field lookup.

    For example, {filters = dict(id=id__in)}, defines that the querystring
    parameter ``id``, will trigger the Django field lookup ``id__in``, with the
    value given to ``id``. So, the querystring I{?id=12&id=14}, will perform
    the filter I{filter(id__in=[12, 14])}, on the corresponding model.
    """
    
    read = True
    create = True
    update = True
    delete = True

    def validate(self, request, *args, **kwargs):
        """
        Turns the data on the request(I{request.data}) into a model instance, or list of model
        instances; New instance(s) for I{POST}'ed data, or current instance(s)
        to be updated, for I{PUT}'ed data.

        The model instances are validated using Django's I{full_clean()}
        method, so we can be sure that they are valid model instances, ready to
        hit the database. This can be seen as something totally similar to Django ModelForm
        validation.         
        
        After this method, we shouldn't perform modifications on the model
        instances, since any modifications might make the data models invalid.

        For Bulk POST or plural PUT requests, if some of the data
        instances fail to validate, we raise an L{authentication.ErrorList} exception, which
        includes the validation errors of the corresponding data instances.

        @type request: HTTPRequest object
        @param request: Incoming request

        @rtype: None
        @return: None
        """
        def validate_all_post(instances):
            """
            Generator that validates a list of L{model} instances.
            Should be used to validate the model instance in the case of Bulk
            POST and plural PUT requests.

            @param instances: List of L{model} instances

            For every instance in I{instances}, it returns None if the
            instance validates correctly, or a ValidationError if not.
            """
            for i, instance in enumerate(instances):
                try:
                    instance.full_clean()
                except ObjectDoesNotExist:
                    yield ValidationError(
                        'Foreign Keys on model not defined',
                        params={'index': i}
                    )
                except ValidationError, e:
                    e.params = {'index': i}
                    yield e
                yield None

        def validate_all_put(instances): 
            for instance in instances:
                try:
                    instance.full_clean()
                except ObjectDoesNotExist:
                    yield ValidationError(
                        'Foreign Keys on model not defined',
                        params={'id': instance.id}
                    )
                except ValidationError, e:
                    e.params = {'id': instance.id}
                    yield e
                yield None

        super(ModelHandler, self).validate(request, *args, **kwargs)

        if request.method.upper() == 'POST':
            # Create model instance(s) (without saving them), and validate them
            if not isinstance(request.data, list):
                # Single model instance. 
                #Validate and raise any exception that may happen                
                request.data = self.model(**request.data)
                try:                    
                    request.data.full_clean()                    
                except ObjectDoesNotExist:
                    # There is a weird case, when if a Foreign Key on the model
                    # instance is not defined, and this foreign key is used in
                    # the __unicode__ method of the model, to derive its string
                    # representation, we get a ``DoesNotExist``exception,
                    # instead of a ``ValidationError``.
                    # #TODO: Is this a bug though? 
                    # It can also be dealt with by removing the use of the FK
                    # from the model's unicode method, but that would require a
                    # lot of manual work
                    raise ValidationError('Foreign Keys on model not defined')
                except ValidationError:
                    raise
            else:                   
                # Multiple model instances. 
                # Create(not save), validate all, make a list of all exceptions
                # that may happen, and pack them in a ValidationErrorList.
                request.data = \
                    [self.model(**data_item) for data_item in request.data]
                
                error_list = [error for error in validate_all_post(request.data) if error]
                if error_list:
                    raise ValidationErrorList(error_list)

        elif request.method.upper() == 'PUT':     
            current = getattr(request, 'dataset', None)
            
            def update(instance, update_items):
                # Update ``instance`` with the key, value pairs in
                # ``update_values``
                [setattr(instance, field, value) for field, value in update_items]

            # (key, value) pairs to update                
            update_items = request.data.items()

            if isinstance(current, self.model):
                # Single model instance
                # Update, validate and raise any exception that may happen
                update(current, update_items)
                current.full_clean()
            else:
                # Multiple model instance
                # Update, validate all, make list of all exceptions that
                # occur, and pack them in a ValidationErrorList.
                [update(instance, update_items) for instance in current]
                error_list = [error for error in validate_all_put(current) if error]
                if error_list:
                    raise ValidationErrorList(error_list)
            request.data = current

    def working_set(self, request, *args, **kwargs):
        """
        Returns the working set of the model handler. It should be the whole
        queryset of the model instances, with filtering made only based on
        keyword arguments.

        @type request: HTTPRequest object
        @param request: Incoming request

        @rtype: QuerySet
        @return: Model Queryset
        
        I{Notes:}

        * Keyword arguments are defined in the URL mapper, and are usually in
        the form of I{/api_endpoint/<id>/}.

        * For faster query execution, consider the use of
        U{select_related<https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-related>}
        Be aware though, that it can be very U{memory-intensive
        <https://code.djangoproject.com/ticket/17>}. A middle-of-the-way
        solution would probably be to use it with the I{depth} parameter.
        """
        return self.model.objects.filter(**kwargs)
    
    def data_item(self, request, *args, **kwargs):
        """
        Returns a single model instance, if such has been pointed out. Else the
        super class returns None.
        
        @type request: HTTPRequest object
        @param request: Incoming request

        @return: Model instance, or None
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
        @type data: QuerySet
        @param data: Data on which the filter iwll be applied

        @type definition: str, tuple
        @param definition: Filter definition. Could be:

        * A Django U{field lookup
        <https://docs.djangoproject.com/en/dev/topics/db/queries/#field-lookups>},
        defining both the field and the lookup. For example I{id__in}, which
        defines the field {id} and the lookup filter to be applied upon it.
        
        * A {a custom filter} as defined in L{custom_filters}, defining
        both the field and the filter. For example, I{emails__in_list},
        which defines the field {emails} and the filter {__in_list} to be
        applied upon it.
        
        * A tuple defining the fields on which an OR based Full Text search will be performed.
        For example I{('name', 'surname')}.

        @type values: list
        @param values: The values to be applied on the filter.

        @rtype: QuerySet
        @return: Filtered queryset
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
        """
        """
        return data.order_by(*order)
    
    def response_slice_data(self, data, request):
        """
        Slices the data and limits it to a certain range.

        @type data: Model or Queryset
        @param data: Dataset to slice

        @type request: HTTPRequest
        @param request: Incoming request

        @rtype: list
        @return: List of (sliced_data, total)
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
        Writes the model instances available in I{request.data}, to the
        database.
        
        After this method, I{request.data} only contains the successfully
        created model instance(s).

        When can a model instance fail to be created?
        * In very rare cases, when a model instance will escape the uniqueness
        constraints(eg, bulk create: More that one entries are the same.
        They both escape the uniqueness constraints since they are not yet
        created, but only the first of them managed to be created eventually), 
        and the second only fails upon hitting the database.
        * Database failure

        @type request: HTTPRequest
        @param request: Incoming request

        @rtype: Model or Queryset
        @return: Succesfully created instance(s)
        """
        def persist(instance):
            try:
                instance.save(force_insert=True)
            except:
                # TODO: 
                # 1. If I was using InnoDB storage engine, I could simply consider
                # the whole operation (whether single or Bulk) as a
                # transaction, and roll it back in the first failure.
                # Unfortunately I cannot assume that InnoDB is used
                # 
                # 2. Use bulk_create that Django 1.4 offers
                #
                # Long term plan:
                # - Single item POST: Raise an error and an appropriate
                #   HTTPResponse, when the database fails.
                # - Bulk POST: Use Django 1.4 ``bulk_create``. This way a
                # failure can raise an error.
                #
                return None
            else:
                return instance

        if isinstance(request.data, self.model):
            request.data = persist(request.data)
        elif request.data:
            request.data = \
                [instance for instance in request.data if persist(instance)]

        return super(ModelHandler, self).create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """
        Saves (updates) the model instances contained in I{request.data}. Returns the
        subset of {request.data} which contains the successfully updated
        model instances.

        @type request: HTTPRequest
        @param request: Incoming request

        @rtype: Model or Queryset
        @return: Succesfully updated instance(s)
        """
        def persist(instance):
            try:
                instance.save(force_update=True)
            except:
                return None
            else:
                return instance
        
        if isinstance(request.data, self.model):
            request.data = persist(request.data)
        elif request.data:
            request.data = \
                [instance for instance in request.data if persist(instance)]
        
        return super(ModelHandler, self).update(request, *args, **kwargs)
    
    def data_safe_for_delete(self, data):
        """
        We only run this method AFTER the result data have been serialized into
        text. If we had ran it earlier, then the model instances of the result
        set would have been deleted, hence their I{id} field would have been
        equal to I{None}, and hence their I{id} would not be available for
        serialization.        

        @type data: Model or QuerySet
        @param data: Model instance(s) to be deleted

        @rtype: None
        @return: None
        """
        if data:
            data.delete()

        return super(ModelHandler, self).data_safe_for_delete(data)
