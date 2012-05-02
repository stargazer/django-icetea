class MethodNotAllowed(Exception):
	"""
	Raised when a request tries to access a method not allowed by the handler.
	"""
	def __init__(self, *permitted_methods):
		self.permitted_methods = permitted_methods

class UnprocessableEntity(Exception):
    """
    Raised when the request is semantically incorrect. Only raised for
    semanticlly incorrect querystring parameters.
    """
    def __init__(self, errors):
        self.errors = [errors,]

class MimerDataException(Exception):
    """
    Raised if the content_type and data don't match
    """
    pass
 
