def coerce_put_post(request):
	if request.method.upper() == 'PUT':
		if hasattr(request, '_post'):
			del request._post
			del request._files
		try:
			request.method='POST'
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
    TYPES = dict()
    
    def __init__(self, request):
        self.request = request
        
    def is_multipart(self):
        content_type = self.content_type()

        if content_type is not None:
            return content_type.lstrip().startswith('multipart')

        return False

    def loader_for_type(self, ctype):
        """
        Gets a function ref to deserialize content
        for a certain mimetype.
        """
        for loadee, mimes in Mimer.TYPES.iteritems():
            for mime in mimes:
                if ctype.startswith(mime):
                    return loadee
                    
    def content_type(self):
        """
        Returns the content type of the request in all cases where it is
        different than a submitted form - application/x-www-form-urlencoded
        """
        type_formencoded = "application/x-www-form-urlencoded"

        ctype = self.request.META.get('CONTENT_TYPE', type_formencoded)
        
        if type_formencoded in ctype:
            return None
        
        return ctype

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
        ctype = self.content_type()
        self.request.content_type = ctype
        
        if not self.is_multipart() and ctype:
            loadee = self.loader_for_type(ctype)
            
            if loadee:
                try:
                    self.request.data = loadee(self.request.raw_post_data)
                        
                    # Reset both POST and PUT from request, as its
                    # misleading having their presence around.
                    self.request.POST = self.request.PUT = dict()
                except (TypeError, ValueError):
                    # This also catches if loadee is None.
                    raise ValidationError('Invalid request body')
            else:
                self.request.data = None

        return self.request
                
    @classmethod
    def register(cls, loadee, types):
        cls.TYPES[loadee] = types
        
    @classmethod
    def unregister(cls, loadee):
        return cls.TYPES.pop(loadee)

