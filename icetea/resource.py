from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse
from authentication import NoAuthentication
from django.conf import settings

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import Http404, HttpResponseBadRequest, \
    HttpResponseGone, HttpResponseNotAllowed, HttpResponseNotFound, \
    HttpResponseForbidden, HttpResponseServerError

from django.conf import settings
from django.db import connection
import datetime
        
from utils import coerce_put_post, translate_mime, \
    MimerDataException, MethodNotAllowed, UnprocessableEntity
from emitters import Emitter, JSONEmitter, _TYPEMAPPER
                   
from django.views.debug import ExceptionReporter   
from django.core.mail import send_mail, EmailMessage
import sys

class Resource:
    """
    Instances of this class act as Django views.
    For every API endpoint, one such instance should be created, with the API
    handler as its argument. The instance then should be used in the URL
    mapper, to initiate the serving of the HTTP request.

    Instances are callable, and therefore, every request on the application endpoint will start from
    the :meth:`Resource.__call__`.
    """
    DEFAULT_EMITTER_FORMAT = 'json'

    def __init__(self, handler):
        """
        Initializes the Resource instance. It should happen once for every
        Handler, in the url mapper.

        When requests come in, Resource.__call__ takes off.
        
        Data assigned on the resource instance, should be read-only. Why?
        Concurrent requests coming on the same API endpoint, will be server by
        the same resource. So, the same __call__ method will be called by
        different threads of the wsgi process. If one of the threads modifies
        the resource's attributes, the modifications will affect all threads.
        
        Then, is it a problem that both threads will be running the same
        handler?        
        No. The handlers take the ``request`` object as input, and their
        behaviour is based on that. So, the 2 threads running the same handler,
        will be running it with different input, and therefore different
        behaviour.


        # Every ``Resource`` instance pairs up with a ``Handler`` instance.
        # This handler, resource pair will be responsible to handle all
        # incoming request of a certain API endpoint.
        """
        # Instantiate Handler instance
        self._handler = handler()

        if getattr(self._handler, 'model', None):
            _TYPEMAPPER[self._handler] = self._handler.model

        # Exempt this view from CSRF token checks
        self.csrf_exempt = True

        self._authentication = getattr(self._handler, 'authentication')

        self._email_errors = getattr(settings, 'ICETEA_ERRORS', True)
        self._display_errors = getattr(settings, 'ICETEA_DISPLAY_ERRORS', True)
        


    # TODO: study what this does
    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        """
        Actual Django view
        Initiates the serving of the request that has just been received.

        It analyzes the request, executes it, packs and serializes the response, and
        sends it back to the caller.

        .. note::
            This method is invoked by the URL mapper. It is run by a separate
            thread for every request.
        """                     
        # Reset (request specific) query list
        connection.queries = []

        # Is user authenticated?
        if not self.authenticate(request):
            return HttpResponseForbidden()

        try:
            # Cleanup the request, make sure its request body is valid, and
            # make sure that the given request can be applied on the given
            # resource.
            self.cleanup(request, *args, **kwargs)
        except MimerDataException:
            return HttpResponseBadRequest("Invalid request body")
        except ValidationError, e:
            return HttpResponseBadRequest(e.messages)
        except MethodNotAllowed, e:
            return HttpResponseNotAllowed(e.permitted_methods)

        # Determine the emitter, and get rid of the ``emitter_format`` keyword
        # argument
        emitter_format = self.determine_emitter_format(request, *args, **kwargs)
        kwargs.pop('emitter_format', None)
        
        # Execute request
        try:          
            # Dictionary containing {'data': <Serialized result>}                
            response_dictionary = self._handler.execute_request(request, *args, **kwargs)
        except Exception, e:
            # Create appropriate HttpResponse object, depending on the error
            # message
            http_response, message = self.error_handler(e, request)

            # If a Server Error (500) has occured, return it as is
            if isinstance(http_response, HttpResponseServerError):
                http_response.content = message
                return http_response

            # Else return the error message as JSON
            out = ''
            if message:
                out = JSONEmitter(message, self._handler).render(request)
            http_response.content = out
            http_response.mimetype = 'application/json; charset=utf-8'
            return http_response

        else:            
            # Add debug messages to response dictionary
            self.response_add_debug(response_dictionary)
            # Serialize the result into JSON(or whatever else)
            serialized_result, content_type, emitter_format = \
                self.serialize_result(response_dictionary, request,\
                emitter_format) 
            # Construct HTTP response       
            response = HttpResponse(serialized_result, mimetype=content_type,status=200)

            if emitter_format == 'excel':
                response['Content-Disposition'] = 'attachment; filename=file.xls'

            return response
        
    def serialize_result(self, result, request, emitter_format):
        """
        ``@param result``: Result of the execution of the handler, wrapped in a
        dictionary where keys and values are simply text.
        ``@param request``: Request object
        """
        # Find the Emitter class, and the corresponding content
        # type
        emitter_class, mimetype = Emitter.get(emitter_format)

        # create instance of the emitter class
        serializer = emitter_class(result, self._handler, None)
        # serialize the result
        serialized_result = serializer.render(request)

        return serialized_result, mimetype, emitter_format
 
    def determine_emitter_format(self, request, *args, **kwargs):
        """
        Returns the emitter format.
        Either taken from the ``emitter_format`` keywork argument(should be
        given in the ``urls.py``, when declaring the urls view function), or by
        the ``format`` querystring parameter.

        Defaults to ``json``
        """
        emitter_format = kwargs.pop('emitter_format', None)
        if not emitter_format:
            emitter_format = request.GET.get('format', None)

        if not emitter_format:
            return self.DEFAULT_EMITTER_FORMAT

        return emitter_format

    def authenticate(self, request):
        """
        ``True`` if the handler is authenticated(or the handler hasn't overwritten
        the default ``authentication`` parameter).
        ``False`` otherwise.
        """
        if self._authentication.is_authenticated(request):
            return True
        else:
            return False 

    def cleanup(self, request, *args, **kwargs):
        """
        Cleanes the incoming request, and makes sure that it is allowed. The
        checks performed are the folowing:
        
        * If the request is ``PUT``, transform its data to POST.
        * If request is ``PUT`` or ``POST``, make sure the request body
          conforms to the ``Content-Type`` header.
        * Makes sure that the type of request is allowed.
        * Makes sure that if it is a bulk or plural request, it is allowed.
        * Makes sure that non-allowed incoming fields, are cut off the request
          body.

        .. note::

            Assumes that the `id` keyword argument inidicates singular requests on all handlers
        """
        request_method = request.method.upper()
         
         # Is this HTTP method allowed?
        if not request_method in self._handler.allowed_methods:
            raise MethodNotAllowed(*self._handler.allowed_methods)

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
                except MimerDataException:
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

        # Checks start at this point:

        # 1. Singular POST request? (eg contacts/1/)
        #    This makes no sense at all.
        #    Note: We assume that any ``id`` keyword argument in the request, indicates a
        #    singular request.       
        if request_method == 'POST':
            if 'id' in kwargs.keys():
                raise MethodNotAllowed(*self._handler.allowed_methods)
 
        # 2. Check if the request is a plural PUT or DELETE. Allow only if
        #    explicitly enabled through ``plural_update`` and ``plural_delete``. 
        #    Note: We assume that any ``id`` keyword argument in the request, indicates a
        #    singular request.       
        if request_method == 'PUT' and \
            not self._handler.plural_update and \
            not 'id' in kwargs.keys():
            raise MethodNotAllowed(*self._handler.allowed_plural)
        if request_method == 'DELETE' and \
            not self._handler.plural_delete and \
            not 'id' in kwargs.keys():
            raise MethodNotAllowed(*self._handler.allowed_plural)
 
        # 3. Check for Bulk-PUT and Bulk-POST requests.
        #    Bulk-PUT makes no sense at all, so it gives a ValidationError.
        #    Bulk-POST should only be allowed if it has been explicitly enabled
        #    by the ``bulk_create`` parameter.
        if request_method == 'PUT' and isinstance(request.data, list):
            raise ValidationError('Illegal Operation: PUT request with ' + \
                'array in request body')
        if request_method =='POST' and \
            not self._handler.bulk_create and \
            isinstance(request.data, list):
            raise ValidationError('API Handler does not allow bulk POST ' + \
                'requests')

        # Ok, the request has survived all the checks. At this point we strip
        # off the disallowed fields from the request body.
        if request_method in ('POST', 'PUT'):
            if isinstance(request.data, list):
                # We assume it's a list of dictionaries, and reject any non dicts.
                new_request_data = []
                for item in request.data:
                    if not isinstance(item, dict):
                        continue
                
                    clean_item = dict((key, value) for key, value in item.iteritems() \
                        if key in self._handler.allowed_in_fields)
        
                    new_request_data.append(clean_item)
                request.data = new_request_data                

            else:
                # Assume it's a dictionary
                request.data = dict((
                    (key, value) for key, value in request.data.iteritems() \
                    if key in self._handler.allowed_in_fields))


    def error_handler(self, e, request):
        """
        Any exceptions that are raised within the API handler, are taken care
        of here.                   
        
        Returns a tuple (HttpResponseObject, message).
        The HttpResponseObject, is simply an HttpRespone object of the
        appropriate form, depending on the error that occured.
        The message is any kind of message that we would like to return in the
        response body.

        """
        def format_error(error):
            return u'django-icetea crash report:\n\n%s' % error
        
        http_response, message = None, ''
        
        if isinstance(e, ValidationError):
            if hasattr(e, 'message_dict'):
                if '__all__' in e.message_dict:
                    # In the case of a ``clean`` model method, that raises a
                    # ValidationError with a string argument.           
                    errors = e.message_dict['__all__']
                else:
                    # In the case of a ``clean`` model method, that raises a
                    # ValidationError with a dict argument.                    
                    errors = e.message_dict
            elif hasattr(e, 'messages'):
                # Generic ValidationError messages
                errors = e.messages

            message = dict(
                type='Validation Error',
                errors=errors,
            )
            http_response = HttpResponseBadRequest()

        elif isinstance(e, (NotImplementedError, ObjectDoesNotExist)):
            http_response = HttpResponseGone()

        elif isinstance(e, MethodNotAllowed): 
            http_response = HttpResponseNotAllowed(e.permitted_methods)

        elif isinstance(e, UnprocessableEntity):
            message = dict(
                type='Unprocessable Entity Error',
                errors=e.errors,
            )
            http_response = HttpResponse(status=422)

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
            if self._email_errors:
                self.email_exception(reporter)
            if self._display_errors and settings.DEBUG:
                message = format_error('\n'.join(reporter.format_exception()))
            
            http_response = HttpResponseServerError()

        return http_response, message            


    def email_exception(self, reporter):
        subject = 'django-icetea crash report'
        html = reporter.get_traceback_html()
        message = EmailMessage(
            settings.EMAIL_SUBJECT_PREFIX + subject,
            html,
            settings.SERVER_EMAIL,
            [admin[1] for admin in settings.ADMINS]
        )
        message.content_subtype = 'html'
        message.send(fail_silently=False)

        
    def response_add_debug(self, response_dictionary):
        """
        Adds debug information to the response -- currently the database
        queries that were performed in this operation. May be overridden to
        extend with custom debug information.
        """
        if settings.DEBUG:
            response_dictionary.update({
                'debug': {
                    'query_count': len(connection.queries),
                    'query_log': connection.queries,
                }
            })

