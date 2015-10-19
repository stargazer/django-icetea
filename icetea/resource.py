from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse
from django.conf import settings

from django.core.exceptions import ValidationError, ObjectDoesNotExist, \
    PermissionDenied
from django.http import HttpResponseBadRequest, \
    HttpResponseGone, HttpResponseNotAllowed, \
    HttpResponseForbidden, HttpResponseServerError

from django.db import connection
        
from utils import coerce_put_post, translate_mime
from exceptions import MethodNotAllowed, UnprocessableEntity,\
    ValidationErrorList, UnprocessableEntityList
from emitters import Emitter, JSONEmitter
                   
from django.views.debug import ExceptionReporter   
from django.core.mail import EmailMessage
import sys

class Resource:
    """
    Instances of this class act as Django views.
    For every API endpoint, one such instance should be created, with the API
    handler as its argument. The instance should then be used in the URL mapper
    to associate the resource instance with an API endpoint.

    Instances are callable, and therefore, every request on the application endpoint will start from
    the L{Resource.__call__}.
    """
    DEFAULT_EMITTER_FORMAT = 'json'

    def __init__(self, handler):
        """
        Initializes the Resource instance. It should happen once for every
        Handler, in the url mapper.

        Data assigned on the resource instance, should be read-only. Why?
        Concurrent requests coming on the same API endpoint, will be served by
        the same resource. So, the same __call__ method will be called by
        different threads of the wsgi process. If one of the threads modifies
        the resource's attributes, the modifications will affect all threads.
        
        Then, is it a problem that both threads will be running the same
        handler?        
        No. The handlers take the ``request`` object as input, and their
        behaviour is based on that. So, the 2 threads running the same handler,
        will be running it with different input, and therefore different
        behaviour.

        Every L{Resource} instance pairs up with a Handler instance. This
        resource/handler pair will be responsible of handling all incoming
        requests on a certain API endpoint.
        """
        # Instantiate Handler instance
        self.handler = handler()

        if getattr(self.handler, 'model', None):
            Emitter.TYPEMAPPER[self.handler] = self.handler.model

        # Exempt this view from CSRF token checks
        self.csrf_exempt = True

        self.authentication = getattr(self.handler, 'authentication')

        self.email_errors = getattr(settings, 'ICETEA_ERRORS', True)
        self.display_errors = getattr(settings, 'ICETEA_DISPLAY_ERRORS', True)

    # TODO: study what this does
    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        """
        Actual Django view
        Initiates the serving of the request that has just been received.

        It analyzes the request, executes it, packs and serializes the response, and
        returns it back to the caller.

        I{Note:}
       
        This method is invoked by the URL mapper. It is run by a separate
        thread for every request.
        """                     
        # Reset (request specific) query list
        connection.queries = []

        # Is user authenticated?
        if not self.authenticate(request):
            return self.error_response(PermissionDenied(), request)

        # Is this HTTP method allowed?
        try:
            self.authorize(request, *args, **kwargs)
        except MethodNotAllowed, e:
            return self.error_response(e, request)

        # Cleanup request
        try:
            self.cleanup(request, *args, **kwargs)
        except (ValidationError, MethodNotAllowed), e:
            return self.error_response(e, request)

        # Determine the emitter, and get rid of the ``emitter_format`` keyword
        # argument
        emitter_format = self.determine_emitter_format(request, *args, **kwargs)
        kwargs.pop('emitter_format', None)
        
        # Execute request
        try:      
            # Dictionary containing {'data': <Serialized result>}                
            response_dictionary = self.handler.execute_request(request, *args, **kwargs)
        except Exception, e:
            return self.error_response(e, request)

        return self.non_error_response(request, response_dictionary, emitter_format)

    def authenticate(self, request, *args, **kwargs):
        """
        Returns I{True} if the request is authenticated or the handler does not
        require authentication. I{False} otherwise.
        """
        if self.authentication.is_authenticated(request):
            return True
        return False 
             
    def authorize(self, request, *args, **kwargs):   
        """
        Is this HTTP method allowed?

        I{Note:}

        Assumes that the I{id} keyword argument indicates singular requests on all handlers
        """
        request_method = request.method.upper()

        if not request_method in self.handler.allowed_methods:
            raise MethodNotAllowed(*self.handler.allowed_methods)

        #  Singular POST request? (eg contacts/1/)
        #  This makes no sense at all.
        #  Note: We assume that any ``id`` keyword argument in the request, indicates a
        #  singular request.       
        if request_method == 'POST':
            if 'id' in kwargs.keys():
                raise MethodNotAllowed(*self.handler.allowed_methods)

        #  Check if the request is a plural PUT or DELETE. Allow only if
        #  explicitly enabled through ``plural_update`` and ``plural_delete``. 
        #  Note: We assume that any ``id`` keyword argument in the request, indicates a
        #  singular request.       
        if request_method == 'PUT' and \
            not self.handler.plural_update and \
            not 'id' in kwargs.keys():
            raise MethodNotAllowed(*self.handler.allowed_plural)
        if request_method == 'DELETE' and \
            not self.handler.plural_delete and \
            not 'id' in kwargs.keys():
            raise MethodNotAllowed(*self.handler.allowed_plural)

    def determine_emitter_format(self, request, *args, **kwargs):
        """
        Returns the emitter format.
        Either taken from the I{emitter_format} keywork argument(should be
        given in the I{urls.py}, when declaring the urls view function), or by
        the I{format} querystring parameter.

        Defaults to I{json}
        """
        emitter_format = kwargs.pop('emitter_format', None)
        if not emitter_format:
            emitter_format = request.GET.get('format', None)

        if not emitter_format or emitter_format not in Emitter.EMITTERS.keys():
            return self.DEFAULT_EMITTER_FORMAT

        return emitter_format
 
    def serialize_result(self, result, request, emitter_format):
        """
        The request has been executed succefully and we end up here to
        serialize the result

        @type result: dict
        @param result: Result of the execution of the handler, wrapped in a
        dictionary. The dictionary contains the I{data} key, whose value is the
        result of running the operation. The value can be another dictionary,
        list or simply a string. If it's a dictionary or list, it might contain
        other dictionaries/lists, strings, or even I{datetime} functions. All
        dictionary key/value pairs, and list elements, should be strings, other
        than the I{datetime} functions. In anycase, I{self.data} should be
        serializable very easily, without any magic.

        @type request: HTTPRequest
        @param request: Incoming request

        @type emitter_format: str
        @param emitter_format: Emitter format
        """
        # Find the Emitter class, and the corresponding content
        # type
        emitter_class, mimetype = Emitter.get(emitter_format)

        # create instance of the emitter class
        serializer = emitter_class(self.handler, result, None)
        # serialize the result
        serialized_result = serializer.render(request)

        return serialized_result, mimetype, emitter_format

    def cleanup(self, request, *args, **kwargs):
        """
        Cleanes up the incoming request, makes sure it's valid and allowed. In
        detail, the checks performed are the folowing:
        
        * If the request is I{PUT}, transform its data to I{POST}.
        * If request is I{PUT} or I{POST}, make sure the request body
          conforms to the I{Content-Type} header.
        * If request is I{PUT} with a list in the request body, raise
          exception. If request is I{Bulk-POST} and ``bulk_create`` has not
          been set, raise exception.
        * Makes sure that non-allowed incoming fields, are cut off the request
          body.
        """
        request_method = request.method.upper()
         
        # Construct the request.data dictionary, if the request is PUT/POST
        if request_method in ('PUT', 'POST'):
            if request_method == 'PUT':
                # TODO: STUDY what this does exactly
                coerce_put_post(request)
            # Check whether data has the correct format, according to
            # ``Content-Type``          
            if request_method in ('PUT', 'POST'):
                try:
                    translate_mime(request)
                except ValidationError:
                    raise
                if not hasattr(request, 'data'):
                    if request_method == 'POST':
                        request.data = request.POST
                    else:
                        request.data = request.PUT  
                if request.data is None:
                    # In the case when Content-Type is not given or is invalid
                    raise ValidationError('Please make sure the header '+ \
                    '"Content-Type: application/json" is given')

        #    Bulk-PUT makes no sense at all, so it gives a ValidationError.
        #    Bulk-POST should only be allowed if it has been explicitly enabled
        #    by the ``bulk_create`` parameter.
        if request_method == 'PUT' and isinstance(request.data, list):
            raise ValidationError('Illegal Operation: PUT request with ' + \
                'array in request body')
        if request_method =='POST' and \
            not self.handler.bulk_create and \
            isinstance(request.data, list):
            raise ValidationError('API Handler does not allow bulk POST ' + \
                'requests')

        # Ok, the request has survived all the checks. At this point we strip
        # off the disallowed fields from the request body.
        if request_method in ('POST', 'PUT')\
        and self.handler.allowed_in_fields != self.handler.ALL_FIELDS:
            if isinstance(request.data, list):
                # We assume it's a list of dictionaries, and reject any non dicts.
                new_request_data = []
                for item in request.data:
                    if not isinstance(item, dict):
                        continue
                
                    clean_item = dict((key, value) for key, value in item.iteritems() \
                        if key in self.handler.allowed_in_fields)
        
                    new_request_data.append(clean_item)
                request.data = new_request_data                

            else:
                # Assume it's a dictionary
                request.data = dict((
                    (key, value) for key, value in request.data.iteritems() \
                    if key in self.handler.allowed_in_fields))

    def non_error_response(self, request, response_dictionary, emitter_format):           
        """
        No exception has been raised in the handler. 
        Here we construct and return the HTTP response object, with the
        appropriate content in the response body.

        @type request: HTTPRequest
        @param request: Incoming request

        @type response_dictionary: dict
        @param response_dictionary: Dictionary that includes all the response
        data.

        @type emitter_format: str
        @param emitter_format: Emitter format
        
        @rtype: HTTPResponse
        @return: Response object
        """
        # Add debug messages to response dictionary
        self.response_add_debug(response_dictionary)

        # Serialize the result into JSON(or whatever else)
        serialized_result, content_type, emitter_format = \
            self.serialize_result(response_dictionary, request,\
            emitter_format) 
        
        # Construct HTTP response       
        response = HttpResponse(serialized_result, mimetype=content_type,status=200)

        if emitter_format == 'excel':
            if callable(self.handler.excel_filename):
                filename = self.handler.excel_filename()
            else:
                filename = self.handler.excel_filename
            response['Content-Disposition'] = 'attachment; filename=%s' % \
                filename
        
        return response

    def error_response(self, e, request):            
        """
        Creates and returns the appropriate HttpResponse object, depending on
        the type of exception that has been raised.

        @type e: Exception
        @param e: Exception object

        @type request: HTTPRequest
        @param request: Incoming request
        
        @rtype: HTTPResponse
        @return: Response object
        """
        http_response, message = self.exception_to_http_response(e, request)

        # If a Server Error (500) has occured, return it as is
        if isinstance(http_response, HttpResponseServerError):
            http_response.content = message
            return http_response

        # Else return the error message as JSON
        out = ''
        if message:
            out = JSONEmitter(self.handler, message).render(request)
        http_response.content = out
        http_response['Content-type'] = 'application/json; charset=utf-8'
        return http_response

    def exception_to_http_response(self, e, request):
        """
        Any exceptions that are raised within the API handler, are taken care
        of here.                   
        
        @type e: Exception
        @param e: Exception object

        @type request: HTTPRequest
        @param request: Incoming request
        
        @rtype: tuple
        @return: Tuple of (HttpResponseObject, message)

        The HttpResponseObject, is simply an HttpRespone object of the
        appropriate form, depending on the error that occured.
        The message is any kind of message that we will be included in the
        response body.        
        """
        def format_error(error):
            return u'django-icetea crash report:\n\n%s' % error
        
        http_response, message = None, ''

        def validation_error_message(e):
            if hasattr(e, 'message_dict'):
                if '__all__' in e.message_dict:
                    errors = e.message_dict['__all__']
                else:
                    errors = e.message_dict
            elif hasattr(e, 'messages'):
                errors = e.messages
            message = dict(
                type='Validation Error',
                errors=errors,
            )
            if hasattr(e, 'params') and e.params:
                message.update(**e.params)
            return message

        def unprocessable_entity_message(e):
            message = dict(
                type='Unprocessable Entity Error',
                errors=e.errors,
            )
            if hasattr(e, 'params') and e.params:
                message.update(**e.params)
            return message
        
        if isinstance(e, ValidationError):
            message = validation_error_message(e)
            http_response = HttpResponseBadRequest()

        elif isinstance(e, UnprocessableEntity):
            message = unprocessable_entity_message(e)
            http_response = HttpResponse(status=422)

        elif isinstance(e, (NotImplementedError, ObjectDoesNotExist, ValueError)):
            http_response = HttpResponseGone()

        elif isinstance(e, MethodNotAllowed): 
            http_response = HttpResponseNotAllowed(e.permitted_methods)

        elif isinstance(e, PermissionDenied):
            http_response = HttpResponseForbidden()

        elif isinstance(e, ValidationErrorList):       
            http_response = HttpResponseBadRequest()
            # TODO: Differentiate between validation error and unprocessable
            # entity errors
            message = [validation_error_message(error) for error in e.error_list]

        elif isinstance(e, UnprocessableEntityList):
            http_response = HttpResponse(status=422)
            message = [unprocessable_entity_message(error) for error in e.error_list]

        else: 
            # Consider it a Server Error.
            # Send email, respond with a 500 Error code, display error.
            exc_type, exc_value, traceback = sys.exc_info()
            reporter = ExceptionReporter(
                request, 
                exc_type, 
                exc_value,
                traceback.tb_next
            )
            if self.email_errors:
                self.email_exception(reporter)
            if self.display_errors and settings.DEBUG:
                message = format_error('\n'.join(reporter.format_exception()))
            
            http_response = HttpResponseServerError()
        return http_response, message            

    def email_exception(self, reporter):
        """
        Sends email to I{ADMINS}, informing them of the crash
        """
        subject = 'django-icetea crash report'
        html = reporter.get_traceback_html()
        message = EmailMessage(
            subject=settings.EMAIL_SUBJECT_PREFIX + subject,
            body=html,
            from_email=settings.SERVER_EMAIL,
            to=[admin[1] for admin in settings.ADMINS],
        )
        message.content_subtype = 'html'
        message.send(fail_silently=True)

    def response_add_debug(self, response_dictionary):
        """
        Adds debug information to the response -- currently the database
        queries that were performed in this operation. May be overridden to
        extend with custom debug information.
        """
        if settings.DEBUG:
            # In the GAE there is no ``time`` key in the ``connection.queries``
            # dictionaries. That's why I first check for the existence of ``time``
            time_per_query = [
                float(dic['time']) for dic in connection.queries if 'time' in dic
            ]
            if time_per_query:
                total_query_time = sum(time_per_query)
            else:
                total_query_time = 'Not Available'
            
            response_dictionary.update({
                'debug': {
                    'total_query_time': total_query_time,
                    'query_count': len(connection.queries),
                    'query_log': connection.queries,
                }
            })

