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
    def compute_signature(url, qs, method):

        # Remove the ``signature`` parameter from the querystring, sort the
        # querystring parameters to alphabetic order based on key, and
        # reconstruct the querystring.
        query = parse_qs(qs)
        query.pop('signature', None)
        query = query.items()
        query.sort()
        strings = ['%s=%s' % (key, value[0]) for key, value in query]
        querystring = '&'.join(strings)

        # Construct the full url
        if querystring:
            url = '%s?%s' % (url, querystring)

        # Message to hash
        message = '%s%s' % (method, url)
        # Hash key
        key = settings.SECRET_KEY
        
        hmac_object = hmac.new(key, message, sha1)
        return hmac_object.hexdigest()

    def is_authenticated(self, request):
        url = '%s://%s%s' % (
            request.is_secure() and 'https' or 'http',                
            request.get_host(),
            request.path,
        )
        
        # retrieve signature from querystring
        signature = request.GET.get('signature', '')
        
        # Compute the signature for this incoming rquest
        computed_signature = HTTPSignatureAuthentication.compute_signature(
            url,
            request.META['QUERY_STRING'],
            request.method.upper(),
        )

        if computed_signature == signature:
            return True
        return False

    def challenge(self):
        pass
		
