from django.conf.urls import *
from django.contrib import admin

import project.app.urls

admin.autodiscover()

urlpatterns = patterns('',
    (r'^api/', include(project.app.urls)),
    (r'^admin/', include(admin.site.urls)),
)
