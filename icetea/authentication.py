from django.http import HttpResponseForbidden
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import hmac
import binascii
import os
import time
import urllib
from hashlib import sha1
from urlparse import urlparse, urlunparse, parse_qs
from datetime import datetime
from datetime import timedelta


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
        @param url      : Full URI, including url encoded querystring
        (without ``signature`` parameter).
        @param method   : HTTP Method
        
        The signature recipe joins the ``url`` and ``method`` strings, hashes
        them with a key, and returns the result.
        """
        message = 'url=%s&method=%s' % (url, method.upper())
        key = settings.SECRET_KEY
        hmac_object = hmac.new(key, message, sha1)
        
        return hmac_object.hexdigest()

    @staticmethod
    def get_querystring(api_endpoint, method, expires_after, **params):
        """
        @param api_endpoint:  API endpoint to which the signed request will talk to
        @param method:        HTTP method
        @param expires_after: After how long it should expire (in hours)
        @param params:        Extra querystring parameters for request

        Returns the querystring of the signed request, including the signature
        parameter. The querystring is url-encoded.        
        """
        # generate nonce
        nonce = binascii.b2a_hex(os.urandom(15))
        # timestamp of expiration date & time
        expires = int(time.mktime(
            (datetime.now() + timedelta(hours=expires_after)).timetuple()
        ))

        # Querystring key-value pairs
        query = [
            ('nonce', nonce),
            ('expires', expires),
        ]
        # Add the rest key-value pairs
        if params:
            for key, value in params.items():
                query.append((key, value))

        # parse the query list, to a url encoded querystring
        querystring = urllib.urlencode(query)

        # Compute the full API url with the querystring        
        url = '%s?%s' % (
            api_endpoint,
            querystring,
        )            

        # compute signature
        signature = HTTPSignatureAuthentication.compute_signature(url, method)
        
        return querystring + '&signature=%s' % signature

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
		
