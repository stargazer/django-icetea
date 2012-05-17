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
    def __init__(self, errors, params=None):
        self.errors = [errors,]
        
        # Similarly to ValidationError, we give it an extra optional argument
        # ``params``
        if params:
            self.params = params

class MimerDataException(Exception):
    """
    Raised if the content_type and data don't match
    """
    pass

class ErrorList(Exception):
    """
    Raised only for the following requests:
     * Bulk create
     * Plural update
     * Plural delete

    In the first case, it indicates which request body data instances caused
    validation errors, causing the request to fail.
    In the second case, it indicates which dataset instances failed to validate
    correctly, causing the request to fail.
    In the third case, it indicates which dataset instances cannot be deleted,
    causing the request to fail
    """
    def __init__(self, error_list):
        self.error_list = error_list

class ValidationErrorList(ErrorList):
    pass

class UnprocessableEntityList(ErrorList):
    pass
