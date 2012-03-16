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
--------------
Not available yet...

Usage
--------------
Say we have a Project which has pulled ``Django-Icetea``. Let's assume we have
an app called ``foo``, with a model ``foomodel``

We want to define API handlers, which will either act as ``Model handlers``,
and thus giving us CRUD operations out of the box, or ``Base handlers``, for
which we will need to define the functionality in a more manual way.

foo/handlers.py
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
    
    

foo/urls.py
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


All Handler level attributes
-------------------------------
Available only for handlers that extend ModelHandler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``read``
``create``
``update``
``delete``

If any of these parameters is ``True``, then the handler allows ``GET``,
``POST``, ``PUT`` and ``DELETE`` requests respectively.

If instead they are defined as methods, eg::
    def read(self, request, *args, **kwargs):
        pass

Then the corresponding action is enabled, and the default functionality is
overwritten.      

``request_fields``::

    Indicates which querystring parameter will act as a a request-level field
    selector. If ``True``, then the selector is ``field``. If ``False``, there will be no field selection. Default is ``True``.

``order``::
    
    Indicates which querystring parameter will act as the order-type selector
    on the result set of the requested operation.
    If ``True``, then the parameter is ``order``. If ``False``, no order-type
    selection can be performed. Default is ``False``.
    The order logic, should be implemented in the handler's ``order_data``
    method.

``slice``::

    Indicates which querystring parameter will be used to request slicing of
    the result set of the requested operation.
    If ``True``, then the parameter is ``slice``. If ``False``, no slicing will
    be possible. Default is ``False``.
    The slicing notation follows Python's ``list slice syntax``, of
    ``start:stop:step``.   

``filters``
``authentication``:

``allowed_out_fields``
``allowed_in_fields``

Available for all handlers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``model``
``exclude_nested``






