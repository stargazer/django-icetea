from django.conf.urls import patterns, url
from icetea.resource import Resource

from .handlers import (ClientHandler, AccountHandler, ContactHandler,
                       InfoHandler)

client_handler = Resource(ClientHandler)
account_handler = Resource(AccountHandler)
contact_handler = Resource(ContactHandler)
info_handler = Resource(InfoHandler)

urlpatterns = patterns(
    '',
    url(r'^clients/$', client_handler),
    url(r'^clients/(?P<id>[^/]+)/$', client_handler),
    url(r'^accounts/$', account_handler),
    url(r'^accounts/(?P<id>\d+)/$', account_handler),
    url(r'^accounts/(?P<id>[^/]+)/$', account_handler),
    url(r'^contacts/$', contact_handler),
    url(r'^contacts/(?P<id>\d+)/$', contact_handler),
    url(r'^contacts/(?P<id>[^/]+)/$', contact_handler),
    url(r'^info/$', info_handler, {'emitter_format': 'html'}),
    url(r'^info/(?P<id>[^/]+)/$', info_handler, {'emitter_format': 'html'}),
)
