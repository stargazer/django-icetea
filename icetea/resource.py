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
    TYPEMAPPER = {}
    DEFAULT_EMITTER_FORMAT = 'json'

    def __init__(self, handler):
        """
        Initializes the Resource instance. It should appen once for every
        Handler, in the url mapper.

        When requests come in, Resource.__call__ takes off.

        # Every ``Resource`` instance pairs up with a ``Handler`` instance.
        # This handler, resource pair will be responsible to handle all
        # incoming request of a certain API endpoint.
        """
        # Instantiate Handler instance
        self.handler = handler()

        if getattr(self.handler, 'model', None):
            self.TYPEMAPPER[self.handler] = self.handler.model

        # TODO: Is this needed? Where and how is it used?
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

        if not self.handler.authentication:
            self.authentication = NoAuthentication()
        else:
            self.authentication = self.handler.authentication

        self.email_errors = getattr(settings, 'ICETEA_ERRORS', True)
        self.display_errors = getattr(settings, 'ICETEA_DISPLAY_ERRORS', True)
        
    
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
        if self.authentication.is_authenticated(request):
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
                return HttpResponseBadRequest()
                
            # Check whether the data have the correct format, according to
            # their 'Content/Type' header
            if not hasattr(request, 'data'):
                if request_method == 'POST':
                    request.data = request.POST
                else:
                    request.data = request.PUT


    def serialize_result(self, result, request, *args, **kwargs):
        """
        """
        # What's the emitter format to use?
        emitter_format = self.determine_emitter_format(request, *args, **kwargs)
        # Based on that, find the Emitter class, and the corresponding content
        # type
        emitter_class, content_type = Emitter.get(emitter_format)

        # Which fields should the response contain?
        # TODO: What happens with ``fields`` for BaseHandlers ?
        fields = self.handler.get_requested_fields(request)

        # create instance of the emitter class
        serializer = emitter_class(self.TYPEMAPPER, result, self.handler, fields)
        # serialize the result
        serialized_result = serializer.render(request)

        return serialized_result, content_type
 

    # TODO: study what this does
    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        """
        Initiates the serving of the request that has just been received.

        It analyzes the request, executes it, serializes the response, and
        sends it back to the caller.
        """
        # Reset query list
        connection.queries = []

        # Is user authenticated?
        if not self.authenticate(request):
            return HttpResponseForbidden()

        # Is this HTTP method allowed?
        request_method = request.method.upper()
        if not request_method in self.handler.allowed_methods:
            # TODO: error_handler should take care of this?
            return HttpResponseNotAllowed(self.handler.allowed_methods)

        # Cleanup the request and make sure its request body is valid.
        self.cleanup(request, request_method)

        # Execute request
        # Call the handler's request() method, which starts the actual
        # execution of the received request.
        try:            
            result = self.handler.execute_request(request, *args, **kwargs)
            # It's already in {data: <result>} data structure
        except Exception, e:
            # If an exception was raised, call the ``error_handler`` method to
            # format it nicely.
            result = self.error_handler(e, request)

        # Has an error occured?
        if isinstance(result, HttpResponse) and not result._is_string:
            # This is only the case for the HttpResponse objects with the special
            # message attributes. For now it only happens for
            # HttpResponseBadRequest.
            status_code = result.status_code
            result = result._container  #Description of the error
        elif isinstance(result, HttpResponse):
            # Else if it is an ``HttpResponse object`` but with no extra
            # messages, simply return the HttpResponse object, and end here.
            return result

        # Serialize the result
        serialized_result, content_type = self.serialize_result(result, request, *args, **kwargs) 

        try:
            status_code
        except:
            status_code = 200
        
        # Construct HTTP response       
        response = HttpResponse(serialized_result, mimetype=content_type, status=status_code)
        
        #if 'format' in request.GET and request.GET.get('format') == 'excel':
        #   date = datetime.date.today()
        #   response['Content-Disposition'] = 'attachment; filename=Smart.pr-export-%s.xls' % date
            
        return response

    def email_exception(self, reporter):
        subject = "Piston crash report"
        html = reporter.get_traceback_html()
        message = EmailMessage(
            settings.EMAIL_SUBJECT_PREFIX + subject,
            html,
            settings.SERVER_EMAIL,
            [admin[1] for admin in settings.ADMINS]
        )
        message.content_subtype = 'html'
        # Modify it if it works!
        message.send(fail_silently=False)

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

        if isinstance(e, (ValidationError, TypeError)):
            # HttpResponse object returned, contains the message in its
            # ``_container`` attribute. It's the only case where we give
            # details over what happened.
            return HttpResponseBadRequest(dict(
                type='validation',
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
            if self.email_errors:
                self.email_exception(reporter)
            if self.display_errors:
                return HttpResponseServerError(
                    format_error('\n'.join(reporter.format_exception())))
            else:
                raise
            # TODO: Give 500 error. Crash report.

        




