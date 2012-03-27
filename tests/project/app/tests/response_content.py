from project.app.handlers import AccountHandler, ClientHandler, ContactHandler
from project.app.tests.base import TestResponseContentBase

"""
This test class, tests for:
* Correct Response codes
* Correct Response content
* Correct amount of resources returned, in case the request is successful.

In order to create more similar tests, do the following:
* Create a class that extends ``TestResponseContentBase``
* For every test:
    *   Create a method whose name starts with ``test``
    *   Set attributes:
        *   ``handler``: Equal to the API handler to test
        *   ``type``: Equal to either ``read``, ``create``, ``update``, ``delete``
    *   Create a list of tuples ``test_data``. Every tuple should have:
        *   API suffix
        *   Payload
        *   Expected response type
        *   Number of resources returned, or None   
    *   Run ``self.execute(type, handler, test_data)

The fixtures used have the following form: 
    Client 1
        Owns Account instances: 1,2,3,4,5
        Owns Contact instances: 1,2,3,4,5
    Client 2
        Owns Account instances: 6
        Owns Contact instances: 6
    Client 3
        Owns Account instances: 7
        Owns Contact instances: 7
    Client 4
        Owns Account instances: 8
        Owns Contact instances: 8
    Client 5
        Owns Account instances: 9
        Owns Contact instances: 
"""  

class TestResponseContent(TestResponseContentBase):
    def test_ClientHandler_read_plural(self):
        handler = ClientHandler
        type = 'read'
        test_data = (
            ('',  {},     'populated_list', 1),
        )
        self.execute(type, handler, test_data)
 
    def test_ClientHandler_read_singular(self):
        handler = ClientHandler
        type = 'read'
        test_data = (
            # Accessible
            ('1/',    {},     'populated_dict', 1),
            # Inaccessible
            ('2/',    {},     'gone', None),
            ('3/',    {},     'gone', None),
            ('4/',    {},     'gone', None),
            ('5/',    {},     'gone', None),
            # Non existent
            ('6/',    {},     'gone', None),
            ('7/',    {},     'gone', None),
            ('8/',    {},     'gone', None),
            ('9/',    {},     'gone', None),
            ('10/',    {},     'gone', None),
            ('100/',    {},     'gone', None),
            ('1000/',    {},     'gone', None),
            ('10000/',    {},     'gone', None),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_create_plural(self):
        """
        Handler does not allow POST. So all these should give a 405 response
        """
        handler = ClientHandler
        type = 'create'
        test_data = (
            ('',    {},     'not_allowed', None),
            ('',    {'name': 'lalala'},     'not_allowed', None),
            ('',    {'parameter': 'lalala'},     'not_allowed', None),
            ('',    ('parameter'),     'not_allowed', None),
            ('',    [{}, {}],     'not_allowed', None),
            ('',    [{'param1':'lalala'}, {'param2':'lololo'}],     'not_allowed', None),
        )
        self.execute(type, handler, test_data)
 
    def test_ClientHandler_create_singular(self):
        """
        There is no such thing as a singular POST. 
        In anycase though, the handler does not allow POST requests.
        """
        handler = ClientHandler
        type = 'create'
        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, 'not_allowed', None),
            ('1/',  {'name': 'lalalala'}, 'not_allowed', None),
            # Resource exists but is not accessible
            ('2/',  {}, 'not_allowed', None),
            ('2/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('3/',  {}, 'not_allowed', None),
            ('3/',  {'name': 'lalalala'}, 'not_allowed', None),
            # Resource does not exist
            ('5/',  {}, 'not_allowed', None),
            ('5/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('6/',  {}, 'not_allowed', None),
            ('6/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('7/',  {}, 'not_allowed', None),
            ('7/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('10/',  {}, 'not_allowed', None),
            ('10/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('100/',  {}, 'not_allowed', None),
            ('100/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('1000/',  {}, 'not_allowed', None),
            ('1000/',  {'name': 'lalalala'}, 'not_allowed', None),
        )            
        self.execute(type, handler, test_data)

    def test_ClientHandler_update_plural(self):
        """
        Handler forbids PUT requests.
        So they should all give 405 Error
        """
        handler = ClientHandler
        type = 'update'
        test_data = (
            ('',    {},     'not_allowed', None),
            ('',    {'name': 'lalala'},     'not_allowed', None),
            ('',    {'parameter': 'lalala'},     'not_allowed', None),
            ('',    ('parameter'),     'not_allowed', None),
            ('',    [{}, {}],     'not_allowed', None),
            ('',    [{'param1':'lalala'}, {'param2':'lololo'}],     'not_allowed', None),
        )
        self.execute(type, handler, test_data)
 
    def test_ClientHandler_update_singular(self):
        """
        Handler forbids PUT requests.
        So they should all give 405 Error
        """
        handler = ClientHandler
        type = 'update'
        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, 'not_allowed', None),
            ('1/',  {'name': 'lalalala'}, 'not_allowed', None),
            # Resource exists but is not accessible
            ('2/',  {}, 'not_allowed', None),
            ('2/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('3/',  {}, 'not_allowed', None),
            ('3/',  {'name': 'lalalala'}, 'not_allowed', None),
            # Resource does not exist
            ('5/',  {}, 'not_allowed', None),
            ('5/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('6/',  {}, 'not_allowed', None),
            ('6/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('7/',  {}, 'not_allowed', None),
            ('7/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('10/',  {}, 'not_allowed', None),
            ('10/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('100/',  {}, 'not_allowed', None),
            ('100/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('1000/',  {}, 'not_allowed', None),
            ('1000/',  {'name': 'lalalala'}, 'not_allowed', None),
        )            
        self.execute(type, handler, test_data)

    def test_ClientHandler_delete_plural(self):
        """
        Handler forbids DELETE requests.
        So they should all give 405 Error
        """
        handler = ClientHandler
        type = 'delete'
        test_data = (
            ('',  {},    'not_allowed',     None),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_delete_singular(self):
        """
        Handler forbids DELETE requests.
        So they should all give 405 Error
        """
        handler = ClientHandler
        type = 'delete'
        test_data = (
            # Accessible
            ('1/',    {},     'not_allowed', None),
            # Inaccessible
            ('2/',    {},     'not_allowed', None),
            ('3/',    {},     'not_allowed', None),
            ('4/',    {},     'not_allowed', None),
            ('5/',    {},     'not_allowed', None),
            # Non existent
            ('6/',    {},     'not_allowed', None),
            ('7/',    {},     'not_allowed', None),
            ('8/',    {},     'not_allowed', None),
            ('9/',    {},     'not_allowed', None),
            ('10/',    {},     'not_allowed', None),
            ('100/',    {},     'not_allowed', None),
            ('1000/',    {},     'not_allowed', None),
            ('10000/',    {},     'not_allowed', None),
        )
        self.execute(type, handler, test_data)


    def test_AccountHandler_read_plural(self):
        handler = AccountHandler
        type = 'read'
        test_data = (
            ('',    {},     'populated_list',   5),
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_read_singular(self):
        handler = AccountHandler
        type = 'read'
        test_data = (
             # Resource exists and is Accessible
            ('1/',    {},   'populated_dict', 1),
            ('2/',    {},   'populated_dict', 1),
            ('3/',    {},   'populated_dict', 1),
            ('4/',    {},   'populated_dict', 1),
            ('5/',    {},   'populated_dict', 1),
            # Resource exists but is inaccessible
            ('6/',    {},     'gone', None),
            ('7/',    {},     'gone', None),
            ('8/',    {},     'gone', None),
            ('9/',    {},     'gone', None),
            # Resource does not exist
            ('10/',    {},    'gone', None),
            ('100/',    {},   'gone', None),
            ('1000/',    {},  'gone', None),
            ('10000/',    {}, 'gone', None),
        )
        self.execute(type, handler, test_data)
 
    def test_AccountHandler_create_plural(self):
        handler = AccountHandler
        type = 'create'
        test_data = (
            # ``username`` and ``password`` not provided.
            ('',    {},     'bad_request',  None),
            ('',    {'name': 'Randy', 'surname': 'Frombelize'}, 'bad_request' ,None),
            # ``username`` already taken.
            ('',    {'username': 'user1', 'password': 'pass'},  'bad_request',  None),
            ('',    {'username': 'user2', 'password': 'pass'},  'bad_request',  None),
            ('',    {'username': 'user3', 'password': 'pass'},  'bad_request',  None),
            # Successful
            ('',    {'username': 'userlalala', 'password': 'pass'},  'populated_dict',   1),
            # Handler forbids bulk-POST requests
            ('',    [{}, {}],     'bad_request', None),
            ('',    [{'username': 'user1', 'password': 'pass'},{}],  'bad_request',  None),
            ('',    [{'name':'Randy'}, {'name': 'Harry'}],   'bad_request', None),
        )
        self.execute(type, handler, test_data)
 
    def test_AccountHandler_create_singular(self):
        """
        There is no such thing as a singular POST.
        We expect a 405 error for all requests.
        """
        handler = AccountHandler
        type = 'create'
                                       
        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, 'not_allowed', None),
            ('1/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('2/',  {}, 'not_allowed', None),
            ('2/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('3/',  {}, 'not_allowed', None),
            ('3/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('3/',    [{}, {}],     'not_allowed', None),
            # Resource exists but is not accessible
            ('5/',  {}, 'not_allowed', None),
            ('5/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('6/',  {}, 'not_allowed', None),
            ('6/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('7/',  {}, 'not_allowed', None),
            # Resource does not exist
            ('7/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('10/',  {}, 'not_allowed', None),
            ('10/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('100/',  {}, 'not_allowed', None),
            ('100/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('1000/',  {}, 'not_allowed', None),
            ('1000/',  {'name': 'lalalala'}, 'not_allowed', None),
        )            
        self.execute(type, handler, test_data)
 
    def test_AccountHandler_update_plural(self):
        handler = AccountHandler
        type = 'update'

        test_data = (
            ('',    {},     'not_allowed', None),
            ('',    {'name': 'Randy', 'surname': 'Frombelize'},     'not_allowed', None),
            ('',    {'username': 'user1'},     'not_allowed', None),
            ('',    {'username': 'userlololo'},     'not_allowed', None),           
            # Invalid value for ``gender``
            ('',    {'username': 'asdasda'},     'not_allowed', None),
            ('',    {'username': 'tttttt'},     'not_allowed', None),
            ('',    {'username': 'vvvvv'},     'not_allowed', None),
            ('',    {'username': 'pppppppp'},     'not_allowed', None),
            # Handler forbids bulk-POST requests
            ('',    [{}, {}],     'not_allowed', None),
            ('',    [{'username':'userlololo'}, {}],     'not_allowed', None),
            ('',    [{'first_name':'Randy'}, {'first_name': 'Harry'}],     'not_allowed', None),
        )
        self.execute(type, handler, test_data)
 
    def test_AccountHandler_update_singular(self):
        handler = AccountHandler
        type = 'update'
                                        
        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, 'populated_dict', 1),
            ('1/',  {'first_name': 'lalalala'}, 'populated_dict', 1),
            ('2/',  {},     'populated_dict', 1),
            # Fails. The username is taken
            ('2/',  {'username': 'user1'}, 'bad_request', None),
            # Success
            ('2/',  {'username': 'userlololo'}, 'populated_dict', 1),
            # Unnecessary params are cut, since not included in
            # ``allowed_in_fields``
            ('2/',  {'email':'email@domain.com', 'name': 'lalala', 'gender': 'F'}, 'populated_dict', 1),
            ('4/',  {'name': 'lalalala', 'gender': 'f'}, 'populated_dict', 1),
            ('4/',  {'name': 'lalala', 'gender': 'm'}, 'populated_dict', 1),
            ('4/',  {'gender': 'm'}, 'populated_dict', 1),
            # ``list in request body
            ('5/',    [{}, {}],     'bad_request', None),
            # Resource exists but is inaccessible
            # ``gender``        
            ('6/',  {}, 'gone', None),
            ('6/',  {'name': 'lalalala'}, 'gone', None),
            ('7/',  {}, 'gone', None),
            ('7/',  {'name': 'lalalala'}, 'gone', None),
            ('10/',  {}, 'gone', None),
            ('10/',  {'name': 'lalalala'}, 'gone', None),
            ('100/',  {}, 'gone', None),
            ('100/',  {'name': 'lalalala'}, 'gone', None),
            ('1000/',  {}, 'gone', None),
            ('1000/',  {'name': 'lalalala'}, 'gone', None),
        )            
        self.execute(type, handler, test_data)
                                

    def test_AccountHandler_delete_plural(self):
        """
        The handler forbids plural DELETE requests.
        So we should get a 405 error
        """
        handler = AccountHandler
        type = 'delete'

        test_data = (
            ('',  {},     'not_allowed', None),
        )
        self.execute(type, handler, test_data)
 

    def test_AccountHandler_delete_singular(self):
        """
        I am logged in with user id=1. If I remove this user, then I won't be
        able to issue any further requests. I will be getting a 403 error.
        """
        handler = AccountHandler
        type = 'delete'
        
        test_data = (
            # Resource exists and is Accessible
            ('2/',    {},     'populated_dict', 1),
            ('5/',    {},     'populated_dict', 1),
            # Resource exists but is inaccessible
            ('6/',    {},     'gone', None),
            ('7/',    {},     'gone', None),
            ('8/',    {},     'gone', None),
            ('9/',    {},     'gone', None),
            # Resource does not exist
            ('10/',    {},     'gone', None),
            ('100/',    {},     'gone', None),
            ('1000/',    {},     'gone', None),
            ('10000/',    {},     'gone', None),
            # Deleting the user with who I'm logged in...
            ('1/',    {},     'populated_dict', 1),
            # I should be getting a 403 error now
            ('5/',    {},     'not_authorized', None),
            ('4/',    {},     'not_authorized', None),
            ('3/',    {},     'not_authorized', None),
            ('6/',    {},     'not_authorized', None),
            ('7/',    {},     'not_authorized', None),
            ('8/',    {},     'not_authorized', None),
            ('10/',    {},     'not_authorized', None),
            ('100/',    {},     'not_authorized', None),
            ('1000/',    {},     'not_authorized', None),
        )
        self.execute(type, handler, test_data)

 


    def test_ContactHandler_read_singular(self):
        handler = ContactHandler
        type = 'read'
        test_data = (
             # Resource exists and is Accessible
            ('1/',    {},   'populated_dict', 1),
            ('2/',    {},   'populated_dict', 1),
            ('3/',    {},   'populated_dict', 1),
            ('4/',    {},   'populated_dict', 1),
            ('5/',    {},   'populated_dict', 1),
            # Resource exists but is inaccessible
            ('6/',    {},     'gone', None),
            ('7/',    {},     'gone', None),
            ('8/',    {},     'gone', None),
            ('9/',    {},     'gone', None),
            # Resource does not exist
            ('10/',    {},    'gone', None),
            ('100/',    {},   'gone', None),
            ('1000/',    {},  'gone', None),
            ('10000/',    {}, 'gone', None),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_plural(self):
        handler = ContactHandler
        type = 'read'
        test_data = (
            ('',  {},     'populated_list', 5),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_create_plural(self):       
        handler = ContactHandler
        type = 'create'

        test_data = (
            ('',    {},     'populated_dict', 1),
            ('',    {'name': 'Randy', 'surname': 'Frombelize'},  'populated_dict', 1),
            ('',    {'gender': 'M'},   'populated_dict', 1),
            ('',    {'gender': 'F'},   'populated_dict', 1),           
            # Invalid values for ``gender``
            ('',    {'gender': 'm'},   'bad_request', None),
            ('',    {'gender': 'f'},   'bad_request', None),
            ('',    {'gender': 'v'},   'bad_request', None),
            ('',    {'gender': 'bi'},  'bad_request', None),
            # Handler allows bulk-POST requests
            ('',    [{}, {}],     'populated_list', 2),
            ('',    [{'gender':'M'}, {}],  'populated_list', 2),
            # Invalid value for gender
            ('',    [{'gender':'bi'}, {}],  'bad_request', None),
            ('',    [{'name':'Randy', 'gender':'bi'}, {'name': 'Harry'}], 'bad_request', None),
            ('',    [{'name':'Randy'}, {'name': 'Harry'}],   'populated_list', 2),
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_create_singular(self):
        """
        There is no such thing as a singular POST, so the API responds with a
        405 error
        """                                   
        handler = ContactHandler
        type = 'create'

        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, 'not_allowed', None),
            ('1/',  {'name': 'lalalala'}, 'not_allowed', None),
            # Resource exists but is not accessible
            ('2/',  {}, 'not_allowed', None),
            ('2/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('3/',  {}, 'not_allowed', None),
            ('3/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('3/',    [{}, {}],     'not_allowed', None),
            # Resource does not exist
            ('5/',  {}, 'not_allowed', None),
            ('5/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('6/',  {}, 'not_allowed', None),
            ('6/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('7/',  {}, 'not_allowed', None),
            ('7/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('10/',  {}, 'not_allowed', None),
            ('10/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('100/',  {}, 'not_allowed', None),
            ('100/',  {'name': 'lalalala'}, 'not_allowed', None),
            ('1000/',  {}, 'not_allowed', None),
            ('1000/',  {'name': 'lalalala'}, 'not_allowed', None),
        )            
        self.execute(type, handler, test_data)

    def test_ContactHandler_update_plural(self):    
        """
        The handler allows plural PUT requests.
        """
        handler = ContactHandler
        type = 'update'

        test_data = (
            ('',    {},     'populated_list', 5),
            ('',  {'name': 'Randy', 'surname': 'Frombelize'}, 'populated_list', 5),
            ('',    {'gender': 'M'},     'populated_list', 5),
            ('',    {'gender': 'F'},     'populated_list', 5),           
            # Invalid values for ``gender``
            ('',    {'gender': 'm'},     'bad_request', None),
            ('',    {'gender': 'f'},     'bad_request', None),
            ('',    {'gender': 'v'},     'bad_request', None),
            ('',    {'gender': 'bi'},    'bad_request', None),
            # Handler forbids bulk-PUT requests
            ('',    [{}, {}],     'bad_request', None),
            ('',    [{'gender':'M'}, {}],     'bad_request', None),
            ('',    [{'name':'Randy'}, {'name': 'Harry'}],     'bad_request', None),
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_update_singular(self):
        handler = ContactHandler
        type = 'update'
 
        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, 'populated_dict', 1),
            ('1/',  {'name': 'lalalala'}, 'populated_dict', 1),
            ('2/',  {},     'populated_dict', 1),
            ('2/',  {'name': 'lalalala'}, 'populated_dict', 1),
            ('3/',  {'gender': 'M'}, 'populated_dict', 1),
            ('3/',  {'name': 'lalala', 'gender': 'F'}, 'populated_dict', 1),
            # ``gender``
            ('4/',  {'name': 'lalalala', 'gender': 'f'}, 'bad_request', None),
            ('4/',  {'name': 'lalala', 'gender': 'm'}, 'bad_request', None),
            # ``gender``        
            ('4/',  {'gender': 'm'}, 'bad_request', None),
            # ``list in request body
            ('5/',    [{}, {}],     'bad_request', None),
            # Resource exists but is inaccessible
            ('6/',  {}, 'gone', None),
            ('6/',  {'name': 'lalalala'}, 'gone', None),
            ('7/',  {}, 'gone', None),
            ('7/',  {'name': 'lalalala'}, 'gone', None),
            ('10/',  {}, 'gone', None),
            ('10/',  {'name': 'lalalala'}, 'gone', None),
            ('100/',  {}, 'gone', None),
            ('100/',  {'name': 'lalalala'}, 'gone', None),
            ('1000/',  {}, 'gone', None),
            ('1000/',  {'name': 'lalalala'}, 'gone', None),
        )            
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_delete_plural(self):
        """
        The handler allows plural DELETE requests.
        """
        handler = ContactHandler
        type = 'delete'
        test_data = (
            ('',  {},  'populated_list', 5),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_delete_singular(self):
        handler = ContactHandler
        type = 'delete'
        test_data = (
            # Resource exists and is Accessible
            ('1/',    {},     'populated_dict', 1),
            ('2/',    {},     'populated_dict', 1),
            ('3/',    {},     'populated_dict', 1),
            ('4/',    {},     'populated_dict', 1),
            ('5/',    {},     'populated_dict', 1),
            # Resource exists but is inaccessible
            ('6/',    {},     'gone', None),
            ('7/',    {},     'gone', None),
            ('8/',    {},     'gone', None),
            ('9/',    {},     'gone', None),
            # Resource does not exist
            ('10/',    {},     'gone', None),
            ('100/',    {},     'gone', None),
            ('1000/',    {},     'gone', None),
            ('10000/',    {},     'gone', None),
        )
        self.execute(type, handler, test_data)

 
