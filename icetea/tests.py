import sys
from django.test import TestCase
from django.test import Client
from django.utils import simplejson as json

class BaseTest(TestCase):
    """
    Base Test Class.
    Don't inherit directly from this class, but from one of its subclasses.

    Mandatory class attributes that need to be defined:
     * ``fixtures``
     * ``USERNAME``
     * ``PASSWORD``
     * ``endpoints``
    """

    #fixtures = ['fixtures_all',]

    #USERNAME = 'user1'
    #PASSWORD = 'pass1'

    #endpoints = {
    #    AccountHandler: '/api/accounts/',
    #    ClientHandler:  '/api/clients/',
    #    ContactHandler: '/api/contacts/',
    #}

    def setUp(self):
        self.browser = Client()        
        self.browser.login(
            username=self.USERNAME,
            password=self.PASSWORD,
        )   
        self.method_mapping = {
            'read': self.browser.get,
            'create': self.browser.post,
            'update': self.browser.put,
            'delete': self.browser.delete,
        }

    def request(self, type, endpoint, payload):
        """
        @param type: request type
        @param endpoint: api endpoint url
        @payload: request body
        """
        if type in ('create', 'update'):
            payload=json.dumps(payload)

        method = self.method_mapping[type]
        response = method(
            endpoint,
            data=payload,
            content_type='application/json',
        )
        return response


class TestResponseStatusBase(BaseTest):
    def execute(self, type, handler, test_data):
        print '\n'
        # Print test information
        sys.stdout.write("Info: {name}, {handler}, {type}".format(
            name=self.__class__.__name__, 
            handler=handler.__name__,
            type=type,            
        ))
        sys.stdout.write("\n--------------------------------------------------------------------\n")

        # Print headings
        sys.stdout.write("{endpoint:30}{payload:50}{expected:10}{actual:10}".format(
            endpoint="API Endpoint", 
            payload="Payload",
            expected="Expected",
            actual="Actual",
        ))
        sys.stdout.write("\n")

        # Perform test and print results
        for suffix, payload, expected_code in test_data:            
            # construct endpoint
            endpoint = self.endpoints[handler] + suffix
            # execute request
            response = self.request(type, endpoint, payload)
            sys.stdout.write("{endpoint:30}{payload:50}{expected:10}{actual:10}".format(
                endpoint=endpoint, 
                payload=payload,
                expected=str(expected_code),
                actual=str(response.status_code),
            ))
            sys.stdout.write("\n")
            assert expected_code == response.status_code


class TestResponseContentBase(BaseTest):
    """
    Class responsible for testing response code, and response content
    """
    def analyze(self, response):
        """
        Returns the type and length of the ``response``

        Status code 200: 'populated_dict', 'empty_dict', 'populated_list', 'empty_list'
        Status code 400: 'bad_request'
        Status code 405: 'not_allowed'
        Status code 410: 'gone'
        Status code 403: 'not_authorized'
        Status code: 422: 'unprocessable'
        """
        type = length = None
        if response.status_code == 200:
            content = json.loads(response.content)['data']
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
        elif response.status_code == 410:
            type = 'gone'
        elif response.status_code == 400:
            type = 'bad_request'  
        elif response.status_code == 403:
            type = 'not_authorized'
        elif response.status_code == 422:
            type = 'unprocessable'
        
        return type, length

    def execute(self, type, handler, test_data):
        print '\n'
        # Print test information
        sys.stdout.write("Info: {name}, {handler}, {type}".format(
            name=self.__class__.__name__, 
            handler=handler.__name__,
            type=type,            
        ))
        sys.stdout.write("\n--------------------------------------------------------------------\n")

        # Print headings
        sys.stdout.write(\
"{endpoint:30}{payload:50}{expected_response:18}{actual_response:18}{expected_length:13}{actual_length:13}".format(
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
            sys.stdout.write(\
"{endpoint:30}{payload:50}{expected_response:18}{actual_response:18}{expected_length:<13}{actual_length:<13}".format(
                    endpoint=endpoint, 
                    payload=payload,
                    expected_response=expected_response,
                    actual_response=actual_response,
                    expected_length=expected_length,
                    actual_length=actual_length,
                )
            )
            sys.stdout.write("\n")

            assert expected_response == actual_response
            assert expected_length == actual_length



