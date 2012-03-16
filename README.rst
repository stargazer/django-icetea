Django-IceTea
==================

``django-icetea`` is a package built on top of `Django <https://www.djangoproject.com/>`_ and provides the necessary abstractions for creating REST APIs.

It has been influenced by the architecture of `django-piston
<https://bitbucket.org/jespern/django-piston/wiki/Home>`_ and
`piston-perfect <https://github.com/smartpr/piston-perfect>`_. The combination of these 2 packages is actually a very stable
API infrastructure. However their code could, in my opinion at least, be way
more clear and maintainable.

For this reason, I've decided to build ``django-icetea``. It is slim, readable
and easy to use, with its main focus being stability and maintainability.

Enjoy!!

Installation
=============
Not available yet...

Usage
===========
Say we have a Project which has pulled ``Django-Icetea``. Let's assume we have
an app called ``foo``, with a model ``foomodel``

We want to define API handlers, which will either act as ``Model handlers``,
and thus giving us CRUD operations out of the box, or ``Base handlers``, for
which we will need to define the functionality in a more manual way.

app1/handlers.py
^^^^^^^^^^^^^^^^^^
Here we define our API handler, which is the implementer of the business
logic::

    from models import foomodel
    from icetea.handlers import ModelHandler

    class FooHandler(ModelHandler):
        authentication = True
        model = Foo

        read = True
        create = True

        allowed_out_fields = (
            'id',
            'field1', 
            'field2',
        )

        allowed_in_fields = (
            'field1',
            'field2',
        )
    
    

app1/urls.py
^^^^^^^^^^^^^^
We need to create resources(equivalent to Django views), which will initiate
the serving of API requests::

    from djanco.conf.urls.defaults import *
    from handlers import *

    from icetea.resource import Resource
    foo_resource = Resource(FooHandler)

    urlpatterns = patterns('',
        url(r'^foo/$ ', foo_resource),
    )






