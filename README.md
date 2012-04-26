# django-icetea

``django-icetea`` is a package built on top of [Django](https://www.djangoproject.com/) and provides the necessary abstractions for creating REST APIs.

It has been influenced by the architecture of [django-piston](https://bitbucket.org/jespern/django-piston/wiki/Home) and [piston-perfect](https://github.com/smartpr/piston-perfect).

I have decided to build ``django-icetea``, in order to have an API framework with tight foundations, consistent and intuitive behaviour, *readable code*, and of course, easy to use.

## Installation

``django-icetea`` is registered in [PyPI](http://pypi.python.org/pypi/django-icetea/), so 
installing it is as easy as listing it under your project's dependencies, and pulling it on build time.

If you use ``zc.buildout``, you only need to do the following: 

> In your Django project's ``setup.py``, add  ``django-icetea`` in section
> ``install_requires``: 

``` python
setup(
    ...
    ...
    install_requires=(
        ...
        ...
        "django-icetea",
    )
    ...
)

```

Running the buildout should take care of everything, and make package
``icetea`` available in your project.

### Settings parameters
In your application's ``settings.py`` file, you can specify the following
parameters related to ``django-icetea``:

* ``ICETEA_ERRORS``: With ``True``, enables the sending of emails to the
applications's admins, in the case of Server Errors. Default is ``True``.

* ``ICETEA_DISPLAY_ERRORS``: With ``True``, returns well-formed error messages in the case of
Server Errors. It requires that ``DEBUG=True``. Default is ``True``.

## Philosophy

``django-icetea`` aims to provide the abstractions for providing out-of-the-box 
functionality for creating APIs. It strives to keep things clear and explicit,
without any unnecessary magic behind the scenes.

It is very extensible, and the default behaviour can be overridden, extended
and modified at will.

As in any project though, some assumptions have to be made, and some
conventions need to be predefined. 

For example, although *HTTP* is an
application protocol, it has been built mostly for interaction with Web
browsers. When applied in more generic request-response schemes, there are
cases where the protocol itself does not really indicate the correct way of
doing things. For this reason, I mostly view *HTTP* as the transmission means
for requests and responses. It is unaware of business logic, and therefore it
lacks the means of mapping application specific semantice or errors to *HTTP
Responses*. 

A specific case in which the *HTTP* protocol doesn't really specify the
behaviour, is the following:

> Say we need to create a model instance; We issue a *POST* request to the
> server API, and we expect a response which will indicate *if* the
> resource has been created, and if yes, return the resource.
> The server first needs to validate the data it has received. If the data
> doesn't validate, then it needs to return a ``400 Bad Request``. If the data
> validates, but upon creation the database fails, what do we do? Do we
> return ``400 Bad Request``? No way. This will confuse the user and indicate
> that the data provided were invalid. The request was validated successfully,
> so this is not the case, Do we return a Successful response ``200 OK``,
> and empty data? I choose for the latter. 

In anycase developing an API is all about consistent and unambiguous
communication between the client and the server. This has been one of my main
goals with this project. If different applications require different semantics,
*django-icetea*'s code can easily be modified to support them.

Moreover, following the [Principle of the least astonishment](http://en.wikipedia.org/wiki/Principle_of_least_astonishment) which is what *Python* in general, and *Django* in particular *try* to do, I
have tried to follow the general behavior that *Django* users are familiar
with. An example of this is the ``validation`` method of ``django-icetea``. It
cleans the data, creates model instances (without committing them to the
database) and validates them using the model's ``full-clean`` method. Once this
is done, we are certain that we are dealing with perfectly valid model
instances, which we can safely write to the database. This means that we don't
have the need to do all these steps manually, since they are offered by
*django-icetea* out of the box. It is exactly how
validation for Django *Modelform* works, and how most *Django* developers are
used to doing things.. 
The means have changed (REST API instead of Forms), but the procedure is still the
same.

## Short Introduction

*django-icetea* offers 2 types of handlers:

* ``ModelHandler``: Used to expose *Django* models to the API. Offers CRUD
  functionality out of the box.

* ``BaseHandler``: Used to expose data that don't map on a model. Most of the
  functionality will need to be written manually.  

### Glossary

``Singular Request``: A request that refers to a single resource. 

``Plural Request``: A request that refers to a group of resource instances (usually the
instances that the client has the right to view).

``Bulk Request``: Request with an array of data in its request body. It only makes
sense for *POST* requests, and aims to create multiple instances in one request.

### Assumptions

The only assumption that *django-icetea* makes is that singular requests are
denoted by the keyword argument ``id``. So for example a GET request of the
following form ``/resource/<id>/`` requests the resource with ``id=<id>``.

This is essential mostly for security related checks, which mainly control
whether the request is plural, and if such a request has been explicitly
allowed.

### Incoming Requests

The ``Content-type`` header for incoming requests should be
``application/json``. This is currently the only request body format that
*django-icetea* recognizes.

### Outgoing responses

The outgoing responses of *django-icetea* can be of one of the following
formats:

*   ``application/json``
*   ``text/xml``
*   ``text/html``
*   ``application/vnd.ms-excel``

The default is ``application/json``.
Please not that in the case of outputting ``json``, or ``xml``, it is easy to serialize
nested data structures in the response. However in the case of ``html`` and
especially 
``xls``
format, there should (probably) be application specific semantics applied to the output
emitters.

### Status codes

* ``200 OK``: Request was served successfully
* ``400 Bad Request``: Validation error in request body 
* ``403 Forbidden``: Server refuses to server the request, because the client is
  not authenticated 
* ``405 Method Not Allowed``: The request was performed on a resource that does not
  support that type of method
* ``410 Gone``: The resource is not available (either deleted, or not accessible)
* ``422 Unprocessable Entity``: The request was valid, but could not be
  processed due to invalid semantics (eg. A request to DELETE a resource could
  not be carried out, because of some dependencies on the resource)
* ``500 Internal Server Error``


### Tests

``django-icetea`` comes with its own test suite, found in the module
``tests.py``. This module defines Base Test Classes, which are used to test
``django-icetea`` itself, and can also be used to test any API
implementation.

### CSRF tokens

Django uses *CSRF tokens*, in order to deal with web browsers' 
[CSRF vulnerability](http://www.squarefree.com/securitytips/web-developers.html#CSRF). 
Django's *CsrfViewMiddleware* inserts a *CSRF token* as a hidden field in every form using the 
*POST method*, before sending the form to the web browser. For every subsequent 
*POST request* from the web browser, the same middleware checks the token, to ensure that 
it contains the expected value. If not a *403 Forbidden* response is returned.

However, since *django-icetea* is an API and does not make use of forms, the
CSRF token doesn't make a lot of sense. So by default *django-icetea* views are
*CSRF exempted*, meaning they don't require the CSRF token.


## Usage

Say we have a Project which has pulled ``django-icetea``. Let's assume we have
an app called ``foo``, with a model ``FooModel``.
                
We want to define 2 API handlers, to expose the model ``FooModel`` to the API,
as well as some other non-model data.

Other than defining the business logic, handlers also act as means of
representation. For example, ``ModelHandler`` classes, define how the
corresponding model will be represented within that handler(which fields should
be exposed), but also in cases that it is nested in the responses of other handlers.

### foo/handlers.py

TODO: Example with a BaseHandler

Here we define our API handler, which is the implementer of the business
logic

``` python
from models import foomodel
from icetea.handlers import ModelHandler

class FooHandler(ModelHandler):
    authentication = True
    model = FooModel

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
```    
    

### foo/urls.py

We need to create resources(equivalent to Django views), which will initiate
the serving of API requests

``` python
from djanco.conf.urls.defaults import *
from handlers import FooHandler
from icetea.resource import Resource

foo_handler = Resource(FooHandler)

urlpatterns = patterns('',
    url(r'^foo/$ ', foo_handler),
)
```

## Handler level attributes

### Relevant for all handlers

#### read, create, update, delete

If any of these parameters is ``True``, then the handler allows ``GET``,
``POST``, ``PUT`` and ``DELETE`` requests respectively.

If instead they are defined as methods, eg::

``` python
def read(self, request, *args, **kwargs):
    pass
```

Then the corresponding action is enabled, and the default functionality is
overridden.

#### bulk_create

If ``True`` enables bulk-POST requests. Default is ``False``. See section *Notes* for more
information.

#### plural_update
If ``True``, enables plural PUT requests, which means updating multiple
resources in one request. It is a potentially catastrophic operation, and for
this reason is should be explicitly allowed. Default is ``False``.

#### plural_delete
If ``True`` enables plural DELETE requests, which means deleting multiple
resources in one request. It is a potentially catastrophic operation, and for
this reason it should be explicitly allowed. Default is ``False``.

#### request_fields

Indicates which querystring parameter will act as a a request-level field
selector. If ``True``, then the selector is ``field``. If ``False``, there will be no field selection. Default is ``True``.

#### order
    
Indicates which querystring parameter will act as the order-type selector
on the result set of the requested operation.
If ``True``, then the parameter is ``order``. If ``False``, no order-type
selection can be performed. Default is ``False``.
The order logic, should be implemented in the handler's ``order_data``
method.

#### slice

Indicates which querystring parameter will be used to request slicing of
the result set of the requested operation.
If ``True``, then the parameter is ``slice``. If ``False``, no slicing will
be possible. Default is ``False``.
The slicing notation follows Python's ``list slice syntax``, of
``start:stop:step``.                                                          

#### authentication
    
If ``True``, only authenticated users can access the handler. The ``Django
authenticataion`` is used. Default value is ``False``.

#### allowed_out_fields
    
Tuple of fields, which indicates the fields that the handler is allowed to
output. In the case of ``ModelHandler``, it symbolizes model fields, whereas in the case of ``BaseHandler`` classes, it only has sense if the handler returns dictionaries, or lists of dictionaries, and it indicates the dictionary keys that the handler is allowed to output.
    
The actual fields that a request will eventually output, is a function of
this parameter, as well as the request-level field selection, indicated by
the ``field``.

#### allowed_in_fields
    
Tuple of fields, which indicates the fields that the handler allowed to
take from the incoming request body. In the case of ``ModelHandler``
classes, no primary keys or related keys are allowed.

### Relevant only handlers extending ModelHandler

#### model
    
The database model which the Handler exposes.
                       
#### filters

A dictionary of ``filter name``: ``filter_operation`` couples. ``filter
name`` defines the querystring parameter used to apply the filtering on the
current request. ``filter_operation`` corresponds to a Django lookup
filter, which will be applied on the request's resuls data. 

#### exclude_nested

Fields which should be excluded when the model is nested in another
handler's response.

#### excel_filename

The filename to be given to the attachment, if the the request needs to output
to ``excel`` format. It can either be a string or a handler method that returns a
string. Default value is ``file.xls``

## Notes

### Bulk POST requests

``Bulk POST requests`` refers to a single ``POST`` request which attempts to create
multiple data objects. The specifications of ``REST`` or ``HTTP`` don't specify
any standard behaviour for such requests, and instead discourage its use. The
reason is the poor semantics of such requests. 

For example, how would the API signal an error one one of the data objects in 
the request body? How would it signal a database error, when all the data
objects in the request body were valid?

I chose the following behavior:

* Any error in the request body, will return a ``Bad Request`` response.
  For example if the data in the request body refer to Django models, if
  even one of the models fails to validate, the response will be ``Bad
  Request``.

  (Similarly a ``POST`` request for a single instance, returns ``Bad request``
  if the request body does not contain valid data) 

* If the request body is valid, the response is ``OK``, and its body
  contains a list of all the successfully added model instances. If one model
  instance failed to be created (due for example to a database error),
  although it contained valid data, it will not be part of the response
  data.

  (Similarly a POST request for a single instance, returns an ``OK``
  response, and the model instance in the request body. If the model
  instance failed to be created, although it was valid, we return an ``OK``
  response, with ``null`` in the response body)

This is in my opinion the most intuitive behavior. However I think that it all
depends on the requirements of each application, and the clients using the API.
So feel free to modify the existing behavior.

By default ``bulk POST requests`` are disabled. They can be enabled by setting
``bulk_create = True`` in the handler class.

### Building inheritable handlers... Metaclass magic

In this subsection, the term ``operation`` means one of ``read``, ``create``,
``update``, ``delete``.

When a handler sets ``read = True``, basically it says to the system *I want to
inherit the standard ``read`` functionality. Please provide me with it*. This
works with some metaclass magic. Because, clearly some magic needs to be in
please in order to convert the boolean attribute ``read``, to a method.  

The way metaclasses work, is that when a class is initialized, the Python
interpreter scans its own member attributes, and *then* runs the code of the
metaclass. In this case, what the metaclass does, is remove all those
operations that have been defined with ``True``, like `read = True``, in order
to make space for them to be inherited. The metaclass runs on class
initialization, whereas the [Python
MRO](http://www.python.org/getit/releases/2.3/mro/) runs on runtime.

For this reason, when a handler class is defined, in order to provide
inheritable behaviour for other handlers, unless it defines the operations as
methods, it needs to provide them as ``read = True``. This way its metaclass
will remove these attributes and make "space", for it and classes that inherit
from it, to inherit the behaviour that these operations define. Of course the
handlers that inherit from a base handler, will need to first explicitly allow
an operation, in case they want to inherit its functionality.
                                                                
So the way to see it when building handlers:

>    Setting ``read = True``, means that the handler itself and handlers that
>    inherit from it, will inherit the ``read`` functionality, given that they
>    allow so.
>    Setting ``read = False``, or not setting the ``read`` attribute at all, will block
>    the ``read`` functionality for the handler and handlers that inherit from it.
    

