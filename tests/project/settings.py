DEBUG = True

DATABASES = {
    'default': {
            'ENGINE':   'django.db.backends.sqlite3',
            'NAME':     '/tmp/icetea.db',
    }
}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth', 
    'django.contrib.contenttypes', 
    'django.contrib.sessions', 
    'django.contrib.admin',
    'django_extensions',
    'project.app',
)

ROOT_URLCONF = 'project.urls'


