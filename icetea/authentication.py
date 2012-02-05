from django.http import HttpResponseForbidden

class NoAuthentication():
	def is_authenticated(self, request):
		return True

class DjangoAuthentication():
	"""
	Authenticator. Blocks all request with non-authenticated sessions.
	"""
	def is_authenticated(self, request):
		return request.user.is_authenticated()
	
	def challenge(self):
		return HttpResponseForbidden()
		
