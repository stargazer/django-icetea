import json

from django.core.exceptions import ValidationError


def coerce_put_post(request):
    if request.method.upper() == 'PUT':
        if hasattr(request, '_post'):
            del request._post
            del request._files
        try:
            request.method = 'POST'
            request._load_post_and_files()
            request.method = 'PUT'
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'
        request.PUT = request.POST


def translate_mime(request):
    request = Mimer(request).translate()


class Mimer(object):
    # Keeps mappings of {method: MimeType}.
    # It is used to decode incoming data in the request body, to python data
    # structures, if the given 'Content-Type' is actually supported.
    TYPES = {}

    @classmethod
    def register(cls, loadee, types):
        cls.TYPES[loadee] = types

    @classmethod
    def unregister(cls, loadee):
        return cls.TYPES.pop(loadee)

    def __init__(self, request):
        self.request = request

    def _content_type(self):
        """
        Returns the content type of the request
        """
        return self.request.META.get('CONTENT_TYPE', None)

    def _is_multipart(self):
        content_type = self._content_type()

        if content_type is not None:
            return content_type.lstrip().startswith('multipart')

        return False

    def _loader_for_type(self, content_type):
        """
        Gets a function ref to deserialize content
        for a certain mimetype.
        """
        for loadee, mimes in Mimer.TYPES.iteritems():
            for mime in mimes:
                if content_type.startswith(mime):
                    return loadee

    def translate(self):
        """
        Will look at the `Content-type` sent by the client, and maybe
        deserialize the contents into the format they sent. This will
        work for JSON, YAML, XML and Pickle. Since the data is not just
        key-value (and maybe just a list), the data will be placed on
        `request.data` instead, and the handler will have to read from
        there.

        It will also set `request.content_type` so the handler has an easy
        way to tell what's going on. `request.content_type` will always be
        None for form-encoded and/or multipart form data (what your browser sends.)
        """
        content_type = self._content_type()

        self.request.content_type = content_type

        if self._is_multipart():
            raise ValidationError('API cannot interpret multipart requests')

        if content_type is not None:
            loadee = self._loader_for_type(content_type)

            # Is there a loader for the given content type?
            if callable(loadee):
                try:
                    self.request.data = loadee(self.request)
                except (TypeError, ValueError):
                    raise ValidationError('Invalid request body')
                else:
                    # Reset both POST and PUT from request, as its
                    # misleading having their presence around.
                    self.request.POST = {}
                    self.request.PUT = {}
            else:
                raise ValidationError(
                    'API cannot interpret the given Content-Type')
        else:
            raise ValidationError(
                'Please define a Content-Type that the API can interpret')

        return self.request


def mimer_for_form_encoded_data(request):
    """
    Mimer for application/x-www-form-urlencoded
    """
    return request.POST.dict()


def mimer_for_application_json(request):
    """
    Mimer for application/json
    """
    return json.loads(request.body)


# Registering mimer for application/x-www-form-urlencoded
Mimer.register(mimer_for_form_encoded_data, ('application/x-www-form-urlencoded',))

# Mimer for application/json data
Mimer.register(mimer_for_application_json, ('application/json',))
