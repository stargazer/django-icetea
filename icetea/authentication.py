from django.http import HttpResponseForbidden
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import hmac
from hashlib import sha1
from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qs
from datetime import datetime

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
    def compute_signature(url, method):
        """
        The signature recipe only takes into account the bare essentials. It's
        computed given the following ingredients:
        @param url      : Full URI, including all querystring parameters.
        @param method   : HTTP Method
        """
        message = 'url=%s&method=%s' % (url, method)
        key = settings.SECRET_KEY
        hmac_object = hmac.new(key, message, sha1)
        
        return hmac_object.hexdigest()

    def is_authenticated(self, request):
        """
        Checks whether the HTTP signed request can be authorized to proceed.
        """
        if not request.GET.get('signature', None):
            return False

        # Full request Uri, including querystring parameters
        url = request.build_absolute_uri()
        method = request.method.upper()
        
        # Assume that the signature parameter is the last one in the
        # querystring, and remove it.
        url, signature = url.split('&signature=')

        # Compute the signature for this incoming rquest
        computed_signature = HTTPSignatureAuthentication.compute_signature(
            url,
            method,
        )

        expires = request.GET.get('expires', None)
        if computed_signature == signature and\
        datetime.utcfromtimestamp(float(expires)) > datetime.now():
            return True
        return False

    def challenge(self):
        pass
		
