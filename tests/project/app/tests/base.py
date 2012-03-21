import sys
from django.test import TestCase
from django.test import Client
from django.utils import simplejson as json
from project.app.handlers import AccountHandler, ClientHandler, ContactHandler

class BaseTest(TestCase):
    fixtures = ['fixtures_all',]

    USERNAME = 'user1'
    PASSWORD = 'pass1'

    OK = 200
    E_BAD_REQUEST = 400
    E_GONE = 410
    E_NOT_ALLOWED = 405

    endpoints = {
        AccountHandler: '/api/accounts/',
        ClientHandler:  '/api/clients/',
        ContactHandler: '/api/contacts/',
    }

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
        sys.stdout.write("{endpoint:25}{payload:50}{expected:10}{actual:10}".format(
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
            sys.stdout.write("{endpoint:25}{payload:50}{expected:10}{actual:10}".format(
                endpoint=endpoint, 
                payload=payload,
                expected=str(expected_code),
                actual=str(response.status_code),
            ))
            sys.stdout.write("\n")
            assert expected_code == response.status_code
 
