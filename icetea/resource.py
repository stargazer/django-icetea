from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse
from authentication import NoAuthentication
from django.conf import settings

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import Http404, HttpResponseBadRequest, \
    HttpResponseGone, HttpResponseNotAllowed, HttpResponseNotFound, \
    HttpResponseForbidden, HttpResponseServerError

from django.db import connection
import datetime
        
from utils import coerce_put_post, translate_mime, \
    MimerDataException, MethodNotAllowed
from emitters import Emitter
                   
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
    # Mappings of: {<Api Handler instance>, <model>}
    _TYPEMAPPER = {}
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
            self._TYPEMAPPER[self._handler] = self._handler.model

        # Exempt this view from CSRF token checks
        self.csrf_exempt = getattr(self._handler, 'csrf_exempt', True)

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

        # Is this HTTP method allowed?
        request_method = request.method.upper()
        if not request_method in self._handler.allowed_methods:
            return HttpResponseNotAllowed(self._handler.allowed_methods)

        try:
            # Cleanup the request and make sure its request body is valid.
            self.cleanup(request, request_method)
        except MimerDataException:
            return HttpResponseBadRequest("Invalid request body")
        

        # Execute request
        try:          
            # Dictionary containing {'data': <Data results in text>}                
            response_dictionary = self._handler.execute_request(request, *args, **kwargs)

            # Add debug messages to response dictionary
            self.response_add_debug(response_dictionary)

            # Serialize the result into JSON(or whatever else)
            serialized_result, content_type = self.serialize_result(response_dictionary, request, *args, **kwargs) 

            # Construct HTTP response       
            response = HttpResponse(serialized_result, mimetype=content_type, status=200)

            return response

        except Exception, e:
            # Create appropriate HttpResponse object, depending on the request
            result = self.error_handler(e, request)

            if isinstance(result, HttpResponse) and not result._is_string:
                # Only for HttpResponseBadRequest, we return data.
                serialized_result, content_type = self.serialize_result(
                    result, request, *args, **kwargs)
                return HttpResponse(serialized_result, mimetype=content_type, \
                    status=result.status_code)
            elif isinstance(result, HttpResponse):
                return result
        
        #if 'format' in request.GET and request.GET.get('format') == 'excel':
        #   date = datetime.date.today()
        #   response['Content-Disposition'] = 'attachment; filename=Smart.pr-export-%s.xls' % date
            

    def serialize_result(self, result, request, *args, **kwargs):
        """
        @param result: Result of the execution of the handler, wrapped in a
        dictionary where keys and values are simply text.
        @param request: Request object
        """
        # What's the emitter format to use?
        emitter_format = self.determine_emitter_format(request, *args, **kwargs)

        # Based on that, find the Emitter class, and the corresponding content
        # type
        emitter_class, content_type = Emitter.get(emitter_format)

        # create instance of the emitter class
        serializer = emitter_class(self._TYPEMAPPER, result, self._handler, None)
        # serialize the result
        serialized_result = serializer.render(request)

        return serialized_result, content_type
 
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
        True if the handler is authenticated(or the handler request no
        authentication).
        False otherwise.
        """
        if self._authentication.is_authenticated(request):
            return True
        else:
            return False 

    def cleanup(self, request, request_method):
        """
        If request is PUT, transform its data to POST... Study again!

        If request is PUT/POST, make sure the request body conforms to its
        ``content-type``.
        """
        if request_method == 'PUT':
            # TODO: STUDY what this does exactly
            coerce_put_post(request)

        if request_method in ('PUT', 'POST'):
            try:
                translate_mime(request)
            except MimerDataException:
                raise
                
            # Check whether the data have the correct format, according to
            # their 'Content/Type' header
            if not hasattr(request, 'data'):
                if request_method == 'POST':
                    request.data = request.POST
                else:
                    request.data = request.PUT


    def error_handler(self, e, request):
        """
        Any exceptions that are raised within the API handler, are taken care
        of here.                   

        Returns the HttpResponse object that indicates the kind of problem that
        occured.
        Takes care of the appropriate notifications, if an unexpected exception
        has been raised.
        """
        def format_error(error):
	        return u"Django-IceTea crash report:\n\n%s" % error

        if isinstance(e, ValidationError):
            # HttpResponse object returned, contains the message in its
            # ``_container`` attribute. It's the only case where we give
            # details over what happened.
            return HttpResponseBadRequest(dict(
                type='Validation Error',
                message='Invalid data provided.',
                errors=e.messages,
            ))

        elif isinstance(e, (NotImplementedError, ObjectDoesNotExist)):
            return HttpResponseGone()

        elif isinstance(e, MethodNotAllowed):
            return HttpResponseNotAllowed(e.permitted_methods)

        elif isinstance(e, Http404):
            raise HttpResponseNotFound()

        else:
            exc_type, exc_value, traceback = sys.exc_info()
            reporter = ExceptionReporter(
                request, 
                exc_type, 
                exc_value,
                traceback.tb_next
            )
            if self._email_errors:
                self.email_exception(reporter)
            if self._display_errors:
                return HttpResponseServerError(
                    format_error('\n'.join(reporter.format_exception())))
            else:
                raise
            # TODO: Give 500 error. Crash report.


    def email_exception(self, reporter):
        subject = "Django-IceTea crash report"
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

