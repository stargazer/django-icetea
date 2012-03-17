"""
Generic handlers.
"""

import re
from django.core.exceptions import ValidationError
from django.db import models
from authentication import DjangoAuthentication, NoAuthentication
from utils import MethodNotAllowed
from django.core.exceptions import ValidationError
from custom_filters import filter_to_method

# mappings of {Http request type, method}
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
    values without requiring an explicit value in their definition. See for
    example :attr:`BaseHandler.request_fields`.
    """
    
    def __new__(meta, name, bases, attrs):
        
        # Operations should not be allowed unless explicitly enabled. At the
        # same time we want to be able to define inheritable default
        # implementations of *create*, *read*, *update* and *delete*. We marry
        # the two requirements by disabling operations (overriding them with
        # ``False``) at the last minute, just before the class is being
        # constructed.
        # Basically we get rid of the attrs that are of the form:
        #    <operation> = True,
        # so that they don't overwrite the function calls for the
        # respective operations.
        for operation in CALLMAP.values():
            attrs.setdefault(operation, False)
            if attrs.get(operation) is True:
                del attrs[operation]
        
        cls = type.__new__(meta, name, bases, attrs)
        
        # At this point, the  enabled operations are:
        #       - those that have been enabled as <operation> = True. These keep    
        #         the default implementation of the superclass.
        #       - the ones that have been overwritten explicitly in the handler.

        # We always auto-generate (and thus overwrite) *allowed_methods*
        # because the definition of which methods are allowed is now done via
        # *create*, *read*, *update* and *delete* and *allowed_methods* should
        # therefore always reflect their settings.
        cls.allowed_methods = tuple([method
            for method, operation in CALLMAP.iteritems()
            if callable(getattr(cls, operation))])


        # The general idea is that an attribute with value ``True`` indicates
        # that we want to enable it with its default value.
        
        # Indicates which querystring parameter will make the field selection
        if cls.request_fields is True:
            cls.request_fields = 'field'

        # Indicates which querystring parameter will request ordering
        if cls.order is True:
            cls.order = 'order'

        # Indicates which querystring parameter will request data slicing
        if cls.slice is True:
            cls.slice = 'slice'
        
        if cls.authentication is True:
            cls.authentication = DjangoAuthentication() 
        else:
            cls.authentication = NoAuthentication()      

        # For ModelHandler classes, disallow incoming fields that are related
        # fields or primary keys        
        if 'model' in attrs and cls.model != None:
            local_fields = [field.name for field in cls.model._meta.local_fields]

            cls.allowed_in_fields = [ \
                field for field in cls.allowed_in_fields if \
                field in local_fields and 
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
    overwrite method ``get_out_fields``

    It only makes sense in the case of ModelHandler classes. BaseHandler
    classes, return whatever they want anyway.
    """

    allowed_in_fields = ()
    """
    Specifies the set of allowed incoming fields. 

    Mandatory to declare it

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

    def get_output_fields(self, request):
        """
        Returns the request specific field selection.

        It takes into account the ``self.allowed_out_fields`` tuple, as well as
        any request-level field selection that might have taken place.

        Since a BaseHandler is a not a handler for models, the fields returned
        by this function, basically have the sense of dictionary keys allowed
        to be returned, IF the data of the execution of the operation(say the
        read() method) is a dictionary. If the response is for example a
        string, the fields returned don't have any sense.
        """
        requested = request.GET.getlist(self.request_fields)
        # Make sure that if ``field=`` is given(without specifying value), we
        # consider that no request level field-selection has been made.
        if requested == ['']:
            requested = ()

        if requested:
            return set(requested).intersection(self.allowed_out_fields)
        
        return self.allowed_out_fields


    
    def validate(self, request, *args, **kwargs):
        """
        Validates and cleanses incoming data (in the request body).
        We discard data that the handler doesn't allow in the request body.
        """
        if isinstance(request.data, list):            
            if request.method.upper() == 'PUT':
                # PUT request with array of data has no sense.
                raise ValidationError("Illegal operation: PUT request with array in request body")          

            elif request.method.upper() == 'POST':
                # Should only happen in POST request with an array of data
                new_request_data = []

                for item in request.data:
                    new_request_data.append(dict(
                        [(field, value) for field, value in item.iteritems() \
                        if field in self.allowed_in_fields])
                    )
                request.data = new_request_data
        
        # Only one data item in request.data
        else:
            request.data = dict([(field, value)
                for field, value in request.data.iteritems()
                if field in self.allowed_in_fields])

    
    def working_set(self, request, *args, **kwargs):
        """
        Returns the operation's base data set. No data beyond this set will be
        accessed or modified. The reason why we need this one in addition to
        :meth:`.data_set` is that :meth:`.data_item` needs to have a data set
        to pick from -- we need to define which items it is allowed to obtain
        (and which not). This data set should not have user filters applied
        because those do not apply to item views.
        """
        raise NotImplementedError
    
    def data_set(self, request, *args, **kwargs):
        """
        Returns the operation's result data set, which is always an iterable.
        The difference with :meth:`.working_set` is that it returns the data
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
                        raise ValidationError('Invalid filter data provided')
        
        order = request.GET.getlist(self.order)
        if order:
            data = self.order_data(data, *order)
        
        return data
    
    def data_item(self, request, *args, **kwargs):
        """
        Returns the data item that is being worked on. This is how the handler
        decides if the requested data is singular or not. By returning
        ``None`` we signal that this request should be handled as a request
        for a set of data, as opposed to a request for a single record.
        """
        return None
    
    def data(self, request, *args, **kwargs):
        """
        Returns the data that is the result of the current operation, without
        having to specify if the request is singular or plural.
        """
        
        data = self.data_item(request, *args, **kwargs)

        if data is None:
            data = self.data_set(request, *args, **kwargs)

        return data
    
    
    def set_response_data(self, response, key, data):
        """
        Sets data onto a response structure. 
        @param: Dictionary that represents response
        @param key: New key added to the dictinary
        @param data: Value added under key
        """
        response.update({key: data})
    
    
    filters = False
    """
    User filter data query string parameter, or ``True`` if the default
    (``filter``) should be used. Disabled (``False``) by default.
    """
    
    def filter_data(self, data, definition, values):
        """
        Applies user filters (as specified in :attr:`.filters`) to the
        provided data. Does nothing unless overridden with a method that
        implements filter logic.
        """
        return data
    
    
    order = False
    """
    Order data query string parameter, or ``True`` if the default (``order``)
    should be used. Disabled (``False``) by default.
    """
    
    def order_data(self, data, *order):
        """
        Orders the provided data. Does nothing unless overridden with a method
        that implements ordering logic.
        """
        return data
    
    
    slice = False
    """
    Slice data query string parameter, or ``True`` if the default (``slice``)
    should be used. Disabled (``False``) by default.
    """
    
    def response_slice_data(self, data, request, total=None):
        """
        @param data: Dataset to slice
        @param request: Incoming request 
        @total: Total items in dataset (Has a value only if invoked by
        :meth:`.ModelHandler.response_slice_data`

        @return: Returns a list (sliced_data, total)
         * sliced_data: The final data set, after slicing. If no slicing has
           been performed, the initial dataset will be returned
         * total:       Total size of initial dataset. None if no slicing was
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
            'data': <data result>,
            'total': <Number>,        # If slicing was performed
            '<key>: <value>,          # if
            :meth:`.ModelHandler.enrich_response` has been overwritten
        The dictionary values are simply text. The nested models, queryset and
        everything else, have been serialized as text, within this dictionary.       
        """
        if request.method.upper() == 'POST' and not self.data_item(request, *args, **kwargs) is None:
            raise MethodNotAllowed('GET', 'PUT', 'DELETE')
        # Validate request body data
        if hasattr(request, 'data'):
            self.validate(request, *args, **kwargs)
        
        # Pick action to run
        action = getattr(self,  CALLMAP.get(request.method.upper()))
        # Run it
        data = action(request, *args, **kwargs)
        # Select output fields
        fields = self.get_output_fields(request)
        # Slice
        sliced_data, total = self.response_slice_data(data, request)
        
        # Use the emitter to serialize the ``data``. The emitter is responsible for
        # allowing only fields in ``fields``, if such a selection makes sense.
        # Depending on ``data``'s type, after the serialization, it becomes
        # either a dict, list(of strings, dicts, etc) or string.
        from resource import Resource; from emitters import Emitter
        emitter = Emitter(Resource._TYPEMAPPER, sliced_data, self, fields)       
        ser_data = emitter.construct()

        # Structure the response data
        ret = {}
        self.set_response_data(ret, 'data', ser_data)
        if total:
            self.set_response_data(ret, 'total', total)
        # Add extra metadata
        self.enrich_response(ret, data)

        if request.method.upper() == 'DELETE':
            self.data_safe_for_delete(data)

        return ret


    def enrich_response(self, response_structure, data):
        """
        Overwrite this method in your handler, in order to add more (meta)data
        within the response data structure.
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
    :attr:`~BaseHandler.fields`. 
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
    
    def validate(self, request, *args, **kwargs):
        """
        Turns the data on the request into model instances; a new instance
        with the ``POST``'ed data or a current instance to be updated with the 
        ``PUT``'ed data.
        """
        
        super(ModelHandler, self).validate(request, *args, **kwargs)
        
        # TODO: Will *request.data* always be ``None`` if no data was provided
        # in the request body? Will IceTea even allow for an empty request
        # body?
        if request.data is None:
            return

        if request.method.upper() == 'POST':
            # Single data item in request body
            if not isinstance(request.data, list):
                request.data = self.model(**request.data)
            # Array of data items
            else:               
                request.data = [self.model(**data_item) for data_item in request.data]
        
        elif request.method.upper() == 'PUT':
            # current = model instance(s) to be updated
            current = self.data(request, *args, **kwargs)
            
            def update(current, data):
                update_values = data.items()
                for instance in isinstance(current, self.model) and [current] or \
                    current:         
                    for field, value in update_values:
                        setattr(instance, field, value)

            # update the model instances with the(but not save them)
            update(current, request.data)
            
            # request.data contains a model instance or a list of model instances 
            # that have been updated, but not yet saved in the database.
            request.data = current
       

    def working_set(self, request, *args, **kwargs):
        """
        Returns the working set of the model handler. It should be the whole
        queryset of the model instances, with filtering made only based on
        keyword arguments.

        .. note::
            Keyword arguments are defined in the URL mapper, and are usually in
            the form of ``/api endpoint/<id>/``.

        """
        # All keyword arguments that originate from the URL pattern are
        # applied as filters to the *QuerySet*.

        # We were using select_related() but decided to skip it. As we `found
        # out <https://code.djangoproject.com/ticket/17>_`, the use of
        # select_related() causes the WSGI process to use a lot of memory to
        # reference the same database records. There are cases when this is
        # catastrophic, and crashed the server due to memory problems.

        # eg.    
        # A query selects the recipients of a Mailing m, of NewsRelease n.
        # The use of select_related() causes every recipient instance, to
        # reference the Mailing, which references the NewsRelease. If there are
        # X recipients, every one of them references a separate copy of m, and every 
        # copy of m references a separate copy of y. If there are 1000
        # recipients, and n is a huge NewsRelease, then we are in big trouble.

        # On the other hand, if we don't use select_related(), references from
        # a recipient to a Mailing, and from the Mailing to a NewsRelease, are
        # done in a lazy fashion (only when asked), so we don't have this huge
        # memory overhead to deal with.              

        # Wait a minute... Lazy or not, still the data all have to be populated
        # before constructing the response. So we will still need the same
        # memory, right?
        
        # Update 5/1/2012: Using ``depth=1`` forces the select_related to go up
        # to a depth of 1 to retrieve foreign keys.

        return self.model.objects.filter(**kwargs)
    
    def data_item(self, request, *args, **kwargs):
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
                    # turns out not to be there, the raised exception will
                    # automatically be handled by the error handler in
                    # Resource.
                    return self.working_set(request, *args, **kwargs).get(**{ field: kwargs.get(field) })
            except models.FieldDoesNotExist:
                # No field named *field* on *self.model*, try next field.
                pass
        return super(ModelHandler, self).data_item(request, *args, **kwargs)
    
    def filter_data(self, data, definition, values):
        """
        Recognizes and applies two types of filters:
        
        * If its *definition* (the value of the filter in :attr:`.filters`) is
          a text string, it will be interpreted as a filter on the *QuerySet*.
        * If its definition is a list (or tuple or set), it will be
          interpreted as a search operation on all fields that are mentioned
          in this list.
        
        """
        
        if isinstance(definition, basestring):
            # If the definition's suffix is equal to the name of a custom
            # lookup filter, call the corresponding method.
            for lookup in filter_to_method:
                if definition.endswith(lookup):
                    return filter_to_method[lookup](data, definition, values)
            return data.filter(**{ definition: values })
        
        if isinstance(definition, (list, tuple, set)):
            query = models.Q()
            
            for term in ' '.join(values).split():
                for field in definition:
                    query |= models.Q(**{ '%s__icontains' % field: term })
            
            return data.filter(query)
        
        return data
    
    def order_data(self, data, *order):
        return data.order_by(*order)
    
    def response_slice_data(self, data, request):
        """
        Slices the ``data`` and limits it to a certain range.

        @param data: Dataset to slice
        @param request: Incoming request

        @return: Returns a tuple (sliced_data, total)
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
        Creates model instances available in ``request.data``. Returns the
        subset of ``request.data`` which contains the successfully created
        model instances.
        """

        if isinstance(request.data, list):
            # request.data is an array of self.model instances
            
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
                # All instances have been saved successfully:
                pass

        else:
            # request.data is a single self.model instance
            try:
                # The *force_insert* should not be necessary here, but look at it
                # as the ultimate guarantee that we are not messing with existing
                # records.
                request.data.save(force_insert=True)
            except:
                # Not sure what errors we could get, but I think it's safe to just
                # assume that *any* error means that no record has been created.
                request.data = None
        
        return super(ModelHandler, self).create(request, *args, **kwargs)
    
    read = True
    
    def update(self, request, *args, **kwargs):
        """
        Saves (updates) the model instances in ``request.data``. Returns the
        subset of ``request.data`` which contains the successfully updated
        model instances.
        """
        # Returns the model instance(s) in request.data, that have been
        # successfully updated
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
    
    delete = True
    
    
    def data_safe_for_delete(self, data):
        """
        We only run this method AFTER the result data have been serialized into
        text. If we had ran it earlier, then the model instances of the result
        set would have been deleted, hence their ``id `` field would have been
        equal to ``None``, and hence their ``id`` would not be available for
        serialization.        
        """
        # The delete() Django method can only be called on a QuerySet or on a
        # Model instance. However, sometimes data=None (in cases where a
        # singular DELETE request has been issued, but the model instance
        # specified cannot be deleted because of some dependencies), and the 
        # delete() cannot be applied on a None object. 
        # Therefore, we need the check `if data`
        if data:
            data.delete()

        return super(ModelHandler, self).data_safe_for_delete(data)
