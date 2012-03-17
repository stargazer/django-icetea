==================
Django-IceTea
==================

``django-icetea`` is a package built on top of `Django <https://www.djangoproject.com/>`_ and provides the necessary abstractions for creating REST APIs.

It has been influenced by the architecture of `django-piston
<https://bitbucket.org/jespern/django-piston/wiki/Home>`_ and
`piston-perfect <https://github.com/smartpr/piston-perfect>`_. 

For this reason, I've decided to build ``django-icetea``. It is slim, readable
and easy to use, with its main focus being stability and maintainability.

Enjoy!!

Installation
--------------
If you use ``zc.buildout``, installing ``Django-IceTea`` is very simple. 

In your Django project's ``setup.py``, add ``django-icetea`` in section
``install_requires``. 

Then from your project's buildout configuration file, use
a tool like ``mr.developer`` to checkout the code from the github repository,
install the python egg, and expose ``Django-IceTea`` to your project's
namespace.

TODO::
    Add to PyPi

Usage
--------------
Say we have a Project which has pulled ``Django-Icetea``. Let's assume we have
an app called ``foo``, with a model ``foomodel``

We want to define API handlers, which will either act as ``Model handlers``,
and thus giving us CRUD operations out of the box, or ``Base handlers``, for
which we will need to define the functionality in a more manual way.

Other than defining the business logic, handlers also act as means of
representation. For example, ``ModelHandler`` classes, define how the
corresponding model will be represented within that handler, but also in cases
that it is nested in the responses of other handlers.

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

Available for all handlers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``read``, ``create``, ``update``, ``delete``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


If any of these parameters is ``True``, then the handler allows ``GET``,
``POST``, ``PUT`` and ``DELETE`` requests respectively.

If instead they are defined as methods, eg::

    def read(self, request, *args, **kwargs):
        pass

Then the corresponding action is enabled, and the default functionality is
overwritten.      

``request_fields``
~~~~~~~~~~~~~~~~~~~

    Indicates which querystring parameter will act as a a request-level field
    selector. If ``True``, then the selector is ``field``. If ``False``, there will be no field selection. Default is ``True``.

``order``
~~~~~~~~~~~
    
    Indicates which querystring parameter will act as the order-type selector
    on the result set of the requested operation.
    If ``True``, then the parameter is ``order``. If ``False``, no order-type
    selection can be performed. Default is ``False``.
    The order logic, should be implemented in the handler's ``order_data``
    method.

``slice``
~~~~~~~~~~~

    Indicates which querystring parameter will be used to request slicing of
    the result set of the requested operation.
    If ``True``, then the parameter is ``slice``. If ``False``, no slicing will
    be possible. Default is ``False``.
    The slicing notation follows Python's ``list slice syntax``, of
    ``start:stop:step``.   

``filters``
~~~~~~~~~~~~~~
    TODO::
        Should only be available for ModelHandler classes!!!


    A dictionary of ``filter name``: ``filter_operation`` couples. ``filter
    name`` defines the querystring parameter used to apply the filtering on the
    current request. ``filter_operation`` corresponds to a Django lookup
    filter, which will be applied on the request's resuls data.

``authentication``
~~~~~~~~~~~~~~~~~~~~
    
    If ``True``, only authenticated users can access the handler. The ``Django
    authenticataion`` is used. Default value is ``False``.

``allowed_out_fields``
~~~~~~~~~~~~~~~~~~~~~~~
    
    Tuple of fields, which indicates the fields that the handler is allowed to
    output. In the case of ``ModelHandler``, it symbolizes model fields, whereas in the case of ``BaseHandler`` classes, it only has sense if the handler returns dictionaries, or lists of dictionaries, and it indicates the dictionary keys that the handler is allowed to output.
    
    The actual fields that a request will eventually output, is a function of
    this parameter, as well as the request-level field selection, indicated by
    the ``field``.

``allowed_in_fields``
~~~~~~~~~~~~~~~~~~~~~~~~
    
    Tuple of fields, which indicates the fields that the handler allowed to
    take from the incoming request body. In the case of ``ModelHandler``
    classes, no primary keys or related keys are allowed.

Available only for handlers that extend ModelHandler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``model``
~~~~~~~~~~~~~
    
    The database model which the Handler exposes.


``exclude_nested``
~~~~~~~~~~~~~~~~~~~~~~

    Fields which should be excluded when the model is nested in another
    handler's response.





