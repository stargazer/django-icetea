# django-icetea

``django-icetea`` is a package built on top of [Django](https://www.djangoproject.com/) and provides abstractions for creating REST APIs.

It has been influenced by the architecture of [django-piston](https://bitbucket.org/jespern/django-piston/wiki/Home) and [piston-perfect](https://github.com/smartpr/piston-perfect).

I decided to build ``django-icetea``, in order to have an API framework with tight foundations, consistent and intuitive behaviour, *readable code*, and of course, easy to use.

## Installation

``django-icetea`` is registered in [PyPI](http://pypi.python.org/pypi/django-icetea/), so 
installing it is as easy as running:

    pip install django-icetea

However, I would suggest using the latest version from github. The master branch is always stable.

### Settings parameters
In your application's ``settings.py`` file, you can specify the following
parameters related to ``django-icetea``:

* ``ICETEA_ERRORS``: With ``True``, enables the sending of emails to the
applications's admins, in the case of Server Errors. Default is ``True``.

* ``ICETEA_DISPLAY_ERRORS``: With ``True``, returns well-formed error messages in the case of
Server Errors. It requires that ``DEBUG=True``. Default is ``True``.

## Documentation

The code is thoroughly documented. Use [epydoc](http://epydoc.sourceforge.net/) to parse it and generate a
document out of it. For example, in order to create an *html* page with the
documentation, ``cd`` into the *django-icetea* folder, and issue:

    epydoc --html icetea -o docs

This will create folder *docs*. Open the file *index.html* for the whole code
documentation.

## Philosophy

``django-icetea`` aims to provide the abstractions for providing out-of-the-box 
functionality for creating APIs. It strives to keep things clear and explicit,
without any unnecessary magic behind the scenes.

It is very extensible, and the default behaviour can be overridden, extended
and modified at will.

As in any project though, some assumptions have to be made, and some
conventions need to be predefined. 

For example, although *HTTP* is an
application protocol, it is mostly used for interaction with Web
browsers. When applied in more generic request/response schemes, there are
scenarios that the protocol itself does not indicate the correct behavior.
For this reason, I mostly view *HTTP* as the means of transmission
for requests and responses. It is unaware of business logic, and therefore it
lacks the means of mapping application specific semantics or errors to *HTTP
Responses*. 

A specific case in which the *HTTP* protocol doesn't really specify the
behaviour, is the following:

> Say we need to create a model instance; We issue a *POST* request to the
> API, and we expect a response which will indicate *if* the
> resource has been created, and if yes, return the resource.
> The server first needs to validate the data it has received. If the data
> are invalid, the API should return a ``400 Bad Request`` response. If the data
> are valid, but upon creation the database fails, what do we do? Do we
> return ``400 Bad Request``? No way. This will confuse the user and indicate
> that the data provided were invalid. The request was validated successfully,
> so this is not the case, Do we return a Successful response ``200 OK``,
> and empty data? I choose for the latter. This indicates that the data were
> indeed valid, but the resource failed to be created.

In anycase developing an API is all about consistent and unambiguous
communication between the client and the server. This has been one of my main
goals with this project. If different applications require different semantics,
*django-icetea*'s code can easily be modified to support them.

Moreover, following the [Principle of the least astonishment](http://en.wikipedia.org/wiki/Principle_of_least_astonishment) which is what *Python* in general, and *Django* in particular encourage, I
have tried to follow the general behavior that *Django* users are familiar
with. An example of this is the ``validation`` method of the ``ModelHandler`` class (in the ``handlers.py`` module). It
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

``Singular Request``: A request that refers to a single resource. The resource
is usually identified by the url. For example a *GET/PUT/DELETE* request on ``/resource/<id>/`` is a
singular request.

``Plural Request``: A request that affects(retrieves or modifies) a group of resources (usually a subset or all the resources that the client has the right to view). It could be plural GET, plural PUT,
or plural DELETE.

``Bulk Request``: Request with an array of data in its request body. It only makes
sense for *POST* requests, and aims to create multiple instances in one request. For Bulk POST requests there
is no recommended behavior or semantics, so we defined our own semantics, in order to make sure
that the functionality is predictable and makes the most sense. More details
can be seen in section [Bulk POST requests](https://github.com/stargazer/django-icetea#bulk-post-requests).

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
data structures in the response. However in the case of ``html`` and
especially ``xls`` format, there should (probably) be application specific semantics applied to the output
emitters.

### Status codes

The Status codes have the following meanings:

*   ``200 OK``: Request was served successfully
*   ``403 Forbidden``: The client is not authenticated
*   ``405 Method Not Allowed``: The request method was performed on a resource that does not support that method
*   ``410 Gone``: The resource is not available
*   ``422 UnprocessableEntity``: The request was valid but could not be processed due to the semantics of the resource (for example, a *DELETE* request on a resource that belongs to the authenticated client. We might choose not to allow deletion of the specific resource if its field *x* has a specific value. In that case we respond with a *422 UnprocessableEntity* response).

For a very detailed description of the expected responses for any
kind of request, please check section [Request and response protocol](https://github.com/stargazer/django-icetea#request-and-response-protocol).


### Tests

``django-icetea`` comes with its own test suite, found in the ``tests.py`` module. This module defines Base Test Classes, which are used to test ``django-icetea`` itself, and can also be used to test any API implementation.

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

Say we have an API built on top of ``django-icetea``. Let's assume we have
a Django app called ``foo``, with a model ``FooModel``.
                
We want to define 2 API handlers; One that exposes the model ``FooModel``,
and another one that exposes some other non-model data.

Other than defining the business logic, handlers also act as means of
representation. For example, ``ModelHandler`` classes, define how the
corresponding model will be represented within that handler(which fields should
be exposed), but also in cases that it is nested in the responses of other handlers.

### foo/handlers.py

TODO: Example with a BaseHandler

Here we define our API handler, which is the implementer of the business
logic

``` python
from foo.models import foomodel
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
from foo.handlers import FooHandler
from icetea.resource import Resource

foo_handler = Resource(FooHandler)

urlpatterns = patterns('',
    url(r'^foo/$ ', foo_handler),
    url(r'^foo/(?P<id>\d+)/$ ', foo_handler),
)
```

## Handler level attributes

### Relevant for all handlers

#### read, create, update, delete

If any of these parameters is ``True``, then the handler allows ``GET``,
``POST``, ``PUT`` and ``DELETE`` requests respectively.

If instead they are defined as methods, eg:

``` python
def read(self, request, *args, **kwargs):
    pass
```

Then the corresponding action is enabled, and the default functionality is
overridden by the method we defined.

#### bulk_create

If ``True`` enables bulk-POST requests. Default is ``False``. See section [Notes](https://github.com/stargazer/django-icetea#notes) for more information.

Requires that ``create = True``.

When enabled, you should anticipate on ``400 Bad Request`` responses, with a list in their body.

#### plural_update
If ``True``, enables plural PUT requests, which means updating multiple
resources in one request. It is a potentially catastrophic operation, and for
this reason is should be explicitly allowed. Default is ``False``.

Requires that ``update = True``.

When enabled, you should anticipate on ``400 Bad Request`` responses, with a list in their body.

#### plural_delete
If ``True`` enables plural DELETE requests, which means deleting multiple
resources in one request. It is a potentially catastrophic operation, and for
this reason it should be explicitly allowed. Default is ``False``.

Requires that ``delete=True``.

When enabled, you should anticipate on ``422 Unprocessable Entity`` responses, with a list in their body.

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
The slicing notation follows Python's *slice notation*, of ``start:stop:step``.                                                          

#### authentication
    
If ``True``, only authenticated users can access the handler. The *Django
authentication* is used. Default value is ``False``.

#### allowed_out_fields
    
Tuple of fields, which indicates the fields that the handler is allowed to
output. 

In the case of a ``ModelHandler``, it indicates model fields.

In the case of a ``BaseHandler``, it only has sense if the handler returns dictionaries, or lists of dictionaries, and it indicates the dictionary keys that the handler is allowed to output.
    
The actual fields that a request will eventually output, is a function of
this parameter, as well as the request-level field selection, indicated by
the ``field``.

#### allowed_in_fields
    
Tuple of fields, which indicates the fields that the handler is allowed to
take from the incoming request body. In the case of ``ModelHandler``
classes, no primary keys or related keys are allowed.

### Relevant only for handlers extending ModelHandler

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

### Adding extra (fake) fields on a ModelHandler

It's possible that we want to add fake fields on the output of a ``ModelHandler``. 
By *fake* I mean fields that are not actual physical model fields, but simply extra 
information that we wish to include on the API handler's output. Doing so is very easy.

In the model class,  you simply need to define the ``fake_fields`` tuple, with the
names of the fake fields. Then we define the class method
``compute_fake_fields(self, field)``, which should return the values of the fake fields.

For example:

``` python
fake_fields = ('num_tweets', 'num_retweets',)

def _compute_fake_fields(self, field):
    if field == 'num_tweets':
        return self.tweets.count()            

    elif field == 'num_retweets':
        return Retweet.objects.filter(tweet__in=self.tweets.all()).count()
```
The method ``_compute_fake_fields`` is invoked by the ``Emitter`` class, which
constructs the output of the handler. The ``field`` parameter is the field name
that is evaluated. So the ``_compute_fake_fields`` method should be able to compute
all the field names in the ``fake_fields`` tuple.

From this point on, the API handlers can treat these fields as normal model fields.
Meaning, they can be included in the tuples ``allowed_out_fields``,
``exclude_nested``, etc, depending on how you want to treat them.

### Bulk POST requests

*Bulk POST request* refers to a single ``POST`` request which attempts to create
multiple resources. The specifications of ``REST`` or ``HTTP`` don't specify
any standard behaviour for such requests, and instead discourage its use, due
to poor semantics.

For example, how would the API signal an error on one of the data objects in 
the request body? Or, how would it signal a database error, when all the data
objects in the request body were valid?

I chose the following behavior:

* Any error in the request body, will return a ``Bad Request`` response.
  For example when the data in the request body refer to Django models, if
  even one of the models fails to validate, the response will be ``400 Bad
  Request``. The response body will include a list, with all the objects that
  could not be validated. Every object should have an ``index`` parameter, that
  specifies a zero-bazed index of the request body parameter that could not be
  validated.

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

By default *bulk POST requests* are disabled. They can be enabled by setting
``bulk_create = True`` in the handler class.

### Building inheritable handlers... Metaclass magic

In this subsection, the term ``operation`` means one of ``read``, ``create``,
``update``, ``delete``.

When a handler class sets ``read = True``, basically it says to the system:

> I want to inherit the standard ``read`` functionality. Please provide me with it.

This works with some metaclass magic. Clearly some magic needs to be in
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
will remove these attributes and make "space", for classes that inherit
from it, to inherit the behaviour that these operations define. Of course the
handlers that inherit from a base handler, will need to first explicitly allow
an operation, in case they want to inherit its functionality.
                                                                
So the way to see it when building handlers:

>    Setting ``read = True``, means that the handler itself and handlers that
>    inherit from it, will inherit the ``read`` functionality, given that they
>    allow so.
>
>    Setting ``read = False``, or not setting the ``read`` attribute at all, will block
>    the ``read`` functionality for the handler and handlers that inherit from it.
    
### Request and response protocol

Here we describe the responses (status code and response body) for all types of
HTTP requests, successful or not.
 
*   GET
    *   Singular
        *   Successful:
            *   Status code: 200
                *   Response body: Dictionary
        * Errors:
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty
            *   Status code: 410   
                *   Response body: Empty

    *   Plural
        *   Successful:
            *   Status code: 200
                *   Response body: List
        *   Errors:                
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty

*   POST
    *   Refers to single resource (Dictionary in request body)
        *   Successful:
            *   Status code: 200
                *   Response body: Dictionary
                *   Response body: ``null`` (Happens in the case when a
                    database failure prevents the data object from being
                    written to the database)
        *   Errors:            
            *   Status code: 400
                *   Response body: Dictionary
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty
            *   Status code: 422
                *   Response body: Dictionary
    *   Bulk (List in request body)
        *   Successful
            *   Status code: 200
                *   Response body: List
        *   Errors                    
            *   Status code: 400
                *   Response body: List (list items are dictionaries. Every
                    dictionary should have an``index`` parameter which defines a
                    zero-based index of the request body instance that was
                    invalid)
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty
            *   Status code: 422
                *   Response body: List (list items are dictionaries. Every
                    dictionary should have an ``index`` parameter which defines a
                    zero-based index of the request body instance that caused
                    the error)

*   PUT
    *   Singular
        *   Successful
            *   Status code: 200
                *   Response body: Dictionary
        *   Errors
            *   Status code: 400
                *   Response body: Dictionary
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty
            *   Status code: 410
                *   Response body: Empty
            *   Status code: 422
                *   Response body: Dictionary
    *   Plural
        *   Successful                
            *   Status code: 200
                *   Response body: List
        *   Errors
            *   Status code: 400
                *   Response body: List (list items are dictionaries. Every
                    dictionary should provide an ``id`` parameter which defines
                    the ``id`` of the (model) instance that was invalid)
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty
            *   Status code: 422
                *   Response body: List (list items are dictionaries. Every
                    dictionary should provide an ``id`` parameter which defines
                    the ``id` of the (model) instance that caused the error)

*   DELETE
    *   Singular
        *   Successful
            *   Status code: 200
                *   Response body: Dictionary
        *   Errors                    
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty
            *   Status code: 410
                *   Response body: Empty
            *   Status code: 422
                *   Response body: Dictionary
    *   Plural
        *   Successful
            *   Status code: 200
                *   Response body: List
        *   Errors
            *   Status code: 403
                *   Response body: Empty
            *   Status code: 405
                *   Response body: Empty
            *   Status code: 422
                *   Response body: List (list items are dictionaries. Every
                    dictionary should provide an ``id`` parameter which defined
                    the ``id`` of the (model) instance that caused the error)
 
#### Note
In the presence of errors, if the response body is a dictionary or a list,
every error instance(*one* in the case of dictionary, *multiple* in the case of a
list) will contain the following keys:

*   ``errors``: It will be a dictionary of {``field``: [``error``]} pairs where possible,
    or a list of strings describing the errors.
*   ``type``  : Error type

In the case of a list of errors, every item will contain the key ``index``, or
``id``, which will specify which request body item, or which data model instance caused the corresponding error.


##### Examples

``` python
# Error response of a POST request for a single resource
{
    "errors": {
        "text": [
            "This field cannot be blank"
        ]
    },
    "type": "Validation Error"
}

```

``` python
# Error response of a Bulk POST request
[
    {
        "index": 0,
        "errors": {
            "gender": [
                "Value u'bi' is not a valid choice."
            ], 
            "email": [
                "Invalid Email"
            ]
        },
        "type": "Validation Error"
    },
    {
        "index": 3,
        "errors":   {
            "postcode": [
                "Invalid Postcode"
            ]
        "type": "Validation Error"
        }
    }
]    

```

``` python
# Error response of a plural DELETE request
[
    {
        "id": 2,
        "errors": [
            "Instance cannot be deleted"
        ],
        "type": "Unprocessable Entity Error"
    },
    {
        "id": 4,
        "errors": [
            "Instance cannot be deleted"
        ],
        "type": "Unprocessable Entity Error"
    }
]    

``` 
