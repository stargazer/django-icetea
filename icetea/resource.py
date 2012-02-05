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
        
from utils import coerce_put_post, translate_mime, format_error, \
	MimerDataException, MethodNotAllowed, HttpStatusCode
from .emitters import Emitter
                   
from django.views.debug import ExceptionReporter   
from django.core.mail import send_mail, EmailMessage
import sys
									 
# Mappings of:
# {Handler, model}
TYPEMAPPER = {}

class Resource():

	def __init__(self, handler):
		"""
		Initialize the Resource instance.
		Happens one for every Handler, in the urls.py.

		When requests come in, resource.__call__ takes off.

		# Every ``Resource`` instance pairs up with a ``Handler`` instance.
		# This handler, resource pair will be responsible to handle all
		# incoming request of a certain API endpoint.
		"""
		self.DEFAULT_EMITTER_FORMAT = 'json'
		# Instantiate Handler instance
		self.handler = handler()

		if getattr(self.handler, 'model', None):
			TYPEMAPPER[self.handler] = self.handler.model


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
		

	# TODO: study what this does
	@vary_on_headers('Authorization')
	def __call__(self, request, *args, **kwargs):
		"""
		Initiates the serving of the request that has just been received.
		It analyzes the request, executes it, serializes the response, and
		serves it.
		"""
		connection.queries = []

		# AUTHENTICATION
		# **************
		# Does the user have the right to access this resource?
		authenticated = self.authenticate(request)
		if not authenticated:  
			return HttpResponseForbidden()

		# METHOD ALLOWED?
		# ***************
		request_method = request.method.upper()
		if not request_method in self.handler.allowed_methods:
			# TODO: 
			# Or use the ResponseFactory?
			return HttpResponseNotAllowed(self.handler.allowed_methods)
 
		# CLEAN UP REQUEST, and transform request body to python data structure
		# *****************
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

		# EXECUTE REQUEST
		# ***************
		# Call the handler's request() method, which starts the actual
		# execution of the received request.
		try:			
			result = self.handler.request(request, *args, **kwargs)
			# It's already in {data: <result>} data structure
		except Exception, e:
			# If an exception was raised, call the ``error_handler`` method to
			# format it nicely.
			result = self.error_handler(e, request)

		# OUTPUT
		# ********
		# Determine the emitter format
		emitter_format = self.determine_emitter_format(request, *args, **kwargs)
		emitter_class, content_type = Emitter.get(emitter_format)

		fields = self.handler.get_requested_fields(request)

		# If the ``result`` is an HttpResponse object (happens only in the case
		# of errors), and it contains a non-string message(like in the case of
		# ValidationError), then use the emitter to return it.
		if isinstance(result, HttpResponse) and not result._is_string:
			status_code = result.status_code
			# Description of the error
			result = result._container
		# Else if it is an ``HttpResponse object`` but with a string message,
		# simply return the Http Error that occured.
		elif isinstance(result, HttpResponse):
			return result

		# create instance of the emitter class
		serializer = emitter_class(result, TYPEMAPPER, self.handler, fields)
		# serialize
		serialized_result = serializer.render(request)

		try:
			status_code
		except:
			status_code = 200

		# Construct HTTP response		
		response = HttpResponse(serialized_result, mimetype=content_type, status=status_code)
		
		#if 'format' in request.GET and request.GET.get('format') == 'excel':
		#	date = datetime.date.today()
		#	response['Content-Disposition'] = 'attachment; filename=Smart.pr-export-%s.xls' % date
			
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
		"""
		if isinstance(e, (ValidationError, TypeError)):
			return HttpResponseBadRequest(dict(
				type='validation',
				message='Invalid operation requested',
				errors=e.messages,
			))

		elif isinstance(e, (NotImplementedError, ObjectDoesNotExist)):
			return HttpResponseGone()

		elif isinstance(e, MethodNotAllowed):
			return HttpResponseNotAllowed(e.permitted_methods)

		elif isinstance(e, Http404):
			raise HttpResponseNotFound()

		elif isinstance(e, HttpStatusCode):
			return e.response

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

		




