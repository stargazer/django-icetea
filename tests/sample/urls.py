from django.conf.urls import patterns, include, url
from django.contrib import admin

import app.urls

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^api/', include(app.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
