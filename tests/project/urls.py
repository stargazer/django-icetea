from django.conf.urls.defaults import *
from django.contrib import admin, databrowse

import project.app.urls

admin.autodiscover()

urlpatterns = patterns('',
    (r'^api/', include(project.app.urls)),
    (r'^admin/', include(admin.site.urls)),
)
