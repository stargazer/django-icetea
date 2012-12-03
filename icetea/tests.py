import sys, inspect
from django.test import TestCase
from django.test import Client
from django.utils import simplejson as json

class BaseTest(TestCase):
    """
    Base Test Class.
    Don't inherit directly from this class, but from one of its subclasses.
    """    
    def setUp(self):
        self.browser = Client()        
        self.method_mapping = {
            'read': self.browser.get,
            'create': self.browser.post,
            'update': self.browser.put,
            'delete': self.browser.delete,
        }
        self.login()

    def login(self):
        self.browser.login(
            username=self.USERNAME,
            password=self.PASSWORD,
        )   

    def request(self, type, endpoint, payload):
        """
        @param type: request type
        @param endpoint: api endpoint url
        @payload: request body

        The value payload='non_json_payload', is used to simulate an invalid
        json payload. In this case, we won't try to dump the payload to a JSON
        object, therefore we will be testing the handler's response to invalid
        request bodies.
        """
        if type in ('create', 'update'):
            if not payload == 'non_json_payload':
                payload=json.dumps(payload)

        method = self.method_mapping[type]
        response = method(
            endpoint,
            data=payload,
            content_type='application/json',
        )
        return response

    def truncate(self, string, limit):
        """
        Truncates and returns the string I{string} to I{limit} characters.
        """
        string = str(string)

        if len(string) < (limit - 4):
            return string
        else:
            return string[:(limit - 4)] + "..."

class TestResponseFieldsBase(BaseTest):
    """
    This class implements tests for:

        * Response fields: Makes sure that the data part of a response,
         resulting from a valid request, contains all the expected fields. Nothing more, nothing else.
         This Test class should be used only with requests that return valid
         responses. It's goal is not to check the validity of requests, but the
         response fields of valid requests. For checking the validity of
         requests, see the next Test Class. Invalid requests don't contain any
         data, so in the scope of this test, their response will always be an
         empty tuple.

    How to use?

    Inherit from it, and define class attributes:

     * ``fixtures``: List of fixtures to be loaded
     * ``USERNAME``: Username for authenticated user
     * ``PASSWORD``: Password for authenticated user
     * ``endpoints``: Dictionary of pairs ``API Handler class: API url endpoint``

    For every test:

     * Define a class method whose name starts with ``test``
     * Set method attributes:

      * ``handler``
      * ``type``: Defines the API method to be tested. Equal to either
        ``read``, ``create``, ``update``, ``delete``

     * Create the ``test_data``, which is a list of tuples. Every tuple should
       contain:       

       * URL endpoint suffix. Should be a string.
       * Payload. Should be a a dictionary
       * Tuple with the fields that the response should contain.. 

     * Call ``self.execute(type, handler, test_data)``, which checks whether
       the test succeeds or not.               

    In order to see concrete examples, check the ``tests`` package under
    ``django-icetea`` folder, which used this class to test ``django-icetea``
    itself.  
    """
    # Length of test outputs
    LEN_ENDPOINT = 45
    LEN_PAYLOAD = 40
    LEN_EXPECTED = 60
    LEN_ACTUAL = 60


    def execute(self, type, handler, test_data):
        print '\n'
        # caller method name (method that called ``execute``)
        caller_method = inspect.stack()[1][3]
        # Print test information
        sys.stdout.write("Info: {name}, {caller}, {handler}, {type}".format(
            name=self.__class__.__name__, 
            caller=caller_method,
            handler=handler.__name__,
            type=type,            
        ))
        sys.stdout.write("\n--------------------------------------------------------------------\n")

        # Print headings
        sys.stdout.write(("{endpoint:%d}{payload:%d}{expected:%d}{actual:%d}" % (
            self.LEN_ENDPOINT,
            self.LEN_PAYLOAD,
            self.LEN_EXPECTED,
            self.LEN_ACTUAL,
        )).format(
            endpoint="API Endpoint", 
            payload="Payload",
            expected="Expected",
            actual="Actual",
        ))
        sys.stdout.write("\n")

        # Perform test and print results
        for suffix, payload, expected_fields in test_data:  
            expected_fields = set(expected_fields)

            # construct endpoint
            endpoint = self.endpoints[handler] + suffix
            # execute request
            response = self.request(type, endpoint, payload)
            if response.status_code == 200:
                
                if not 'application/json' in response.get('Content-Type', None):
                    raise AssertionError('Test is only valid for JSON responses')
                
                content = json.loads(response.content)
                data = content['data']

                actual_fields = set()
                if isinstance(data, list):
                    # data is a list of resources
                    data = data[0] # assume that all resources in the list of
                                   # results contain the same fields, so I only
                                   # check the first one.

                actual_fields.update(data.keys())                    
            
            else:
                actual_fields = set()

            sys.stdout.write(("{endpoint:%d}{payload:%d}{expected:%d}{actual:%d}" % (
                self.LEN_ENDPOINT,
                self.LEN_PAYLOAD,
                self.LEN_EXPECTED,
                self.LEN_ACTUAL,
            )).format(
                endpoint=self.truncate(endpoint, self.LEN_ENDPOINT), 
                payload=self.truncate((payload), self.LEN_PAYLOAD),
                expected=self.truncate(expected_fields, self.LEN_EXPECTED),
                actual=self.truncate(actual_fields, self.LEN_ACTUAL),
            ))
            sys.stdout.write("\n")
            assert expected_fields == actual_fields


class TestResponseContentBase(BaseTest):
    """
    This class implements tests for:

     * Response codes
     * Respose content type
     * Amount of resources returned

    Inherit from it, and define class attributes:

     * ``fixtures``: List of fixtures to be loaded
     * ``USERNAME``: Username for authenticated user
     * ``PASSWORD``: Password for authenticated user
     * ``endpoints``: Dictionary of pairs ``API Handler class: API url endpoint``

    For every test:

     * Define a class method whose name starts with ``test``
     * Set method attributes:

      * ``handler``
      * ``type``: Defines the API method to be tested. Equal to either
        ``read``, ``create``, ``update``, ``delete``

     * Create the ``test_data``, which is a list of tuples. Every tuple should
       contain:       

       * URL endpoint suffix. Should be a string.
       * Payload. Should be a a dictionary
       * Expected response type. Should be one of the following strings (the
         corresponding response codes are in parenthesis):

         * ``populated_dict``: (200 OK)
         * ``empty_dict``: (200 OK)
         * ``populated_list``: (200 OK)
         * ``empty_list``: (200 OK)
         * ``bad_request``: (400 Bad Request)
         * ``not_found``: (4o4 Not Found)
         * ``not_allowed``: (405 Method Not Allowed)
         * ``gone``: (410 Response Gone)
         * ``not_authorized``: (403 Not Authorized)
         * ``unprocessable``: (422 Unprocessable Entity)

       * Number of expected resources returned. ``None`` if not applicable.

     * Call ``self.execute(type, handler, test_data)``, which checks whether
       the test succeeds or not.               

    In order to see concrete examples, check the ``tests`` package under
    ``django-icetea`` folder, which used this class to test ``django-icetea``
    itself.               

    """
    # Lengths of test outputs
    LEN_ENDPOINT = 45 
    LEN_PAYLOAD = 40
    LEN_EXPECTED_RES = 25
    LEN_ACTUAL_RES = 25
    LEN_EXPECTED_LEN = 13
    LEN_ACTUAL_LEN = 13

    def analyze(self, response):
        """
        Returns the type and length of the ``response``

        Status code 200: 'populated_dict', 'empty_dict', 'populated_list',
        'empty_list', 'attachment', 'html'
        Status code 400: 'bad_request'
        Status code 405: 'not_allowed'
        Status code 404: 'not_found'
        Status code 410: 'gone'
        Status code 403: 'not_authorized'
        Status code: 422: 'unprocessable'

        400 and 422 responses, contain detailed information about what went wrong,
        and their responses can contain either a dictionary or list of
        dictionaries.

        When the error message is some generic string,  length=1
        When the error message is a dictionary, length=1
        When the error message is a list, length=len(list)
        """
        type = length = None
        if response.status_code == 200:
            try:
                content = json.loads(response.content)['data']
            except:
                if 'Content-Disposition' in response:
                    type = 'attachment'
                    length = None
                elif response.get('Content-Type', None) == 'text/html':
                    type = 'html'
                    length = None
            else:
                if isinstance(content, dict):
                    if len(content) == 0:
                        type = 'empty_dict'
                    else:   
                        type = 'populated_dict'    
                        # length is always 1 in this case
                        length = 1
                elif isinstance(content, list):
                    if len(content) == 0:
                        type = 'empty_list'
                    else:
                        type = 'populated_list'
                        length = len(content)

        elif response.status_code == 405:
            type = 'not_allowed'
        elif response.status_code == 404:
            type = 'not_found'
        elif response.status_code == 410:
            type = 'gone'
        elif response.status_code == 403:
            type = 'forbidden'
        elif response.status_code == 400:
            content = json.loads(response.content)
            type = 'bad_request' 
            if isinstance(content, dict):
                length = 1
            elif isinstance(content, list):
                length = len(content)
        elif response.status_code == 422:
            content = json.loads(response.content)
            type = 'unprocessable'
            if isinstance(content, dict):
                length = 1
            elif isinstance(content, list):
                length = len(content)
        
        return type, length

    def execute(self, type, handler, test_data):
        print '\n'
        # caller method name (method that called ``execute``)
        caller_method = inspect.stack()[1][3]
        # Print test information
        sys.stdout.write("Info: {name}, {caller}, {handler}, {type}".format(
            name=self.__class__.__name__, 
            caller=caller_method,
            handler=handler.__name__,
            type=type,            
        ))
        sys.stdout.write("\n--------------------------------------------------------------------\n")

        # Print headings
        sys.stdout.write((
            "{endpoint:%d}{payload:%d}{expected_response:%d}{actual_response:%d}{expected_length:%d}{actual_length:%d}" % (
                self.LEN_ENDPOINT, 
                self.LEN_PAYLOAD, 
                self.LEN_EXPECTED_RES,
                self.LEN_ACTUAL_RES, 
                self.LEN_EXPECTED_LEN,
                self.LEN_ACTUAL_LEN
            )
       ).format(
            endpoint="API Endpoint", 
            payload="Payload",
            expected_response="Expected",
            actual_response="Actual",
            expected_length="Expected",
            actual_length="Actual",
            )
        )
        sys.stdout.write("\n")
 
        # Perform test and print results
        for suffix, payload, expected_response, expected_length in test_data:     
            # construct endpoint
            endpoint = self.endpoints[handler] + suffix
            # execute request
            response = self.request(type, endpoint, payload)
            # analyze response
            actual_response, actual_length = self.analyze(response)
            sys.stdout.write((\
            "{endpoint:%d}{payload:%d}{expected_response:%d}{actual_response:%d}{expected_length:%d}{actual_length:%d}" % (
                self.LEN_ENDPOINT, 
                self.LEN_PAYLOAD,
                self.LEN_EXPECTED_RES,
                self.LEN_ACTUAL_RES,
                self.LEN_EXPECTED_LEN,
                self.LEN_ACTUAL_LEN,
            )).format(
                endpoint=self.truncate(endpoint, self.LEN_ENDPOINT),
                payload=self.truncate(payload, self.LEN_PAYLOAD),
                expected_response=self.truncate(expected_response, self.LEN_EXPECTED_RES), 
                actual_response=self.truncate(actual_response, self.LEN_ACTUAL_RES),
                expected_length=self.truncate(expected_length, self.LEN_EXPECTED_LEN),
                actual_length=self.truncate(actual_length, self.LEN_ACTUAL_LEN),
            ))
            sys.stdout.write("\n")

            assert expected_response == actual_response
            assert expected_length == actual_length



