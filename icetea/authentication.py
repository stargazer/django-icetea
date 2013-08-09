from django.http import HttpResponseForbidden
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import hmac
from hashlib import sha1

from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qs

class Authentication:
    pass

class NoAuthentication(Authentication):
	def is_authenticated(self, request):
		return True

class DjangoAuthentication(Authentication):
	"""
	Authenticator. Blocks all request with non-authenticated sessions.
	"""
	def is_authenticated(self, request):
		return request.user.is_authenticated()
	
	def challenge(self):
		return HttpResponseForbidden()

class HTTPSignatureAuthentication(Authentication):
    @staticmethod
    def compute_signature(url, method, nonce, expires):
        """
        Computes the signature, given the following ingredients:
        @param url       : URL of the API endpoint
        @oaram methodd   : HTTP Method
        @param nonce     : 
        @param expires:  :
        """
        message = '%s%s%s%s' % (url, method, nonce, expires)
        key = settings.SECRET_KEY
        hmac_object = hmac.new(key, message, sha1)
        
        return hmac_object.hexdigest()

    def is_authenticated(self, request):
        url = '%s://%s%s' % (
            request.is_secure() and 'https' or 'http',                
            request.get_host(),
            request.path,
        )
        method = request.method.upper()
        nonce = request.GET.get('nonce', None)
        expires = request.GET.get('expires', None)

        # Compute the signature for this incoming rquest
        computed_signature = HTTPSignatureAuthentication.compute_signature(
            url,
            request.method.upper(),
            request.GET.get('nonce'),
            request.GET.get('expires'),
        )

        if computed_signature == request.GET.get('signature'):
            return True
        return False

    def challenge(self):
        pass
		
