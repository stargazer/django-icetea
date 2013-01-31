from project.app.handlers import AccountHandler, ClientHandler, ContactHandler,\
InfoHandler
from icetea.tests import TestResponseContentBase, TestResponseFieldsBase

"""
The fixtures used have the following form: 
    Client 1
        Owns Account instances: 1,2,3,4,5
        Owns Contact instances: 1,2,3,4,5
        Owns File instances: 1,2,3,4,5
    Client 2
        Owns Account instances: 6
        Owns Contact instances: 6
        Owns File instances: 6
    Client 3
        Owns Account instances: 7
        Owns Contact instances: 7
        Owns File instances: 7
    Client 4
        Owns Account instances: 8
        Owns Contact instances: 8
        Owns File instances: 8
    Client 5
        Owns Account instances: 9
        Owns Contact instances: 
        Owns File instances: 9
"""  

class TestResponseContent(TestResponseContentBase):
    """
    Testing response codes, response content type, and amount of resources
    returned.
    """
    fixtures = ['fixtures_all']
    USERNAME = 'user1'
    PASSWORD = 'pass1'
    endpoints = {
        AccountHandler: '/api/accounts/',
        ClientHandler:  '/api/clients/',
        ContactHandler: '/api/contacts/',
        InfoHandler: '/api/info/',
    }

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
            ('aaaaaa/',    {},     'gone', None),
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
            ('aaaaaa/', {'name': 'lalala'}, 'not_allowed', None),
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
            ('aaaaa/',  {'name': 'lalalala'}, 'not_allowed', None),
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
            ('aaaaaa/',    {},     'not_allowed', None),
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
            ('aaaaa/',    {}, 'gone', None),
        )
        self.execute(type, handler, test_data)
 
    def test_AccountHandler_create_plural(self):
        handler = AccountHandler
        type = 'create'
        test_data = (
            # ``username`` and ``password`` not provided.
            ('',    {},     'bad_request',  1),
            ('',    {'name': 'Randy', 'surname': 'Frombelize'}, 'bad_request', 1),
            # ``username`` already taken.
            ('',    {'username': 'user1', 'password': 'pass'},  'bad_request', 1),
            ('',    {'username': 'user2', 'password': 'pass'},  'bad_request', 1),
            ('',    {'username': 'user3', 'password': 'pass'},  'bad_request', 1),
            # Successful
            ('',    {'username': 'userlalala', 'password': 'pass'},  'populated_dict',   1),
            # Handler forbids bulk-POST requests
            ('',    [{}, {}],     'bad_request', 1),
            ('',    [{'username': 'user1', 'password': 'pass'},{}], 'bad_request',  1), 
            ('',    [{'name':'Randy'}, {'name': 'Harry'}],   'bad_request', 1),
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
            ('aaaaa/',  {'name': 'lalalala'}, 'not_allowed', None),
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
            ('2/',  {'username': 'user1'}, 'bad_request', 1),
            # Success
            ('2/',  {'username': 'userlololo'}, 'populated_dict', 1),
            # Unnecessary params are cut, since not included in
            # ``allowed_in_fields``
            ('2/',  {'email':'email@domain.com', 'name': 'lalala', 'gender': 'F'}, 'populated_dict', 1),
            ('4/',  {'name': 'lalalala', 'gender': 'f'}, 'populated_dict', 1),
            ('4/',  {'name': 'lalala', 'gender': 'm'}, 'populated_dict', 1),
            ('4/',  {'gender': 'm'}, 'populated_dict', 1),
            # ``list in request body
            ('5/',    [{}, {}],     'bad_request', 1),
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
            ('aaaaa/',  {'name': 'lalalala'}, 'gone', None),
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
            ('5/',    {},     'forbidden', None),
            ('4/',    {},     'forbidden', None),
            ('3/',    {},     'forbidden', None),
            ('6/',    {},     'forbidden', None),
            ('7/',    {},     'forbidden', None),
            ('8/',    {},     'forbidden', None),
            ('10/',    {},     'forbidden', None),
            ('100/',    {},     'forbidden', None),
            ('1000/',    {},     'forbidden', None),
            ('aaaaa/',    {},     'forbidden', None),
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
            ('aaaaaa/',    {}, 'gone', None),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_singular_excel(self):
        """
        Testing output to excel for singular GET requests
        """
        handler = ContactHandler
        type = 'read'
        test_data = (
             # Resource exists and is Accessible
            ('1/?format=excel',    {},   'attachment', None),
            ('2/?format=excel',    {},   'attachment', None),
            ('3/?format=excel',    {},   'attachment', None),
            ('4/?format=excel',    {},   'attachment', None),
            ('5/?format=excel',    {},   'attachment', None),
            # Resource exists but is inaccessible
            ('6/?format=excel',    {},     'gone', None),
            ('7/?format=excel',    {},     'gone', None),
            ('8/?format=excel',    {},     'gone', None),
            ('9/?format=excel',    {},     'gone', None),
            # Resource does not exist
            ('10/?format=excel',    {},    'gone', None),
            ('100/?format=excel',    {},   'gone', None),
            ('1000/?format=excel',    {},  'gone', None),
            ('10000/?format=excel',    {}, 'gone', None),
            ('aaaaaa/?format=excel',    {}, 'gone', None),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_plural(self):
        handler = ContactHandler
        type = 'read'
        test_data = (
            ('',  {},     'populated_list', 5),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_plural_excel(self):
        """
        Testing output to excel for plural GET requests
        """
        handler = ContactHandler
        type = 'read'
        test_data = (
            ('?format=excel',  {},     'attachment', None),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_filter_id(self):
        """
        Plural DELETE request, applying the filter ``id``.
        """
        handler = ContactHandler
        type = 'read'
        test_data = (
            # Will only remove the 2 contacts with the given IDs
            ('?id=1&id=2',  {},  'populated_list', 2),
            # Will not remove the contact, since it's already removed
            ('?id=1',  {},  'populated_list', 1),
            # Semantic error on querystring, returns a 422 error.
            ('?id=',  {},  'unprocessable', 1),
            ('?id=&id=1&id=2',  {},  'unprocessable', 1),
            ('?id=lalalala',  {},  'unprocessable', 1),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_create_plural(self):       
        handler = ContactHandler
        type = 'create'

        test_data = (
            # Testing Invalid payload
            ('',    'non_json_payload', 'bad_request', 1),

            ('',    {},     'populated_dict', 1),
            ('',    {'name': 'Randy', 'surname': 'Frombelize'},  'populated_dict', 1),
            ('',    {'gender': 'M'},   'populated_dict', 1),
            ('',    {'gender': 'F'},   'populated_dict', 1),           
            # Invalid values for ``gender``
            ('',    {'gender': 'm'},   'bad_request', 1),
            ('',    {'gender': 'f'},   'bad_request', 1),
            ('',    {'gender': 'v'},   'bad_request', 1),
            ('',    {'gender': 'bi'},  'bad_request', 1),
            # Handler allows bulk-POST requests
            ('',    [{}, {}],     'populated_list', 2),
            ('',    [{'gender':'M'}, {}],  'populated_list', 2),
            # Invalid value for gender
            ('',    [{'gender':'bi'}, {}],  'bad_request', 1),
            ('',    [{'name':'Randy', 'gender':'bi'}, {'name': 'Harry'}], 'bad_request', 1),
            ('',    [{'gender':'bi'}, {'gender': 'trans'}], 'bad_request', 2),
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
            ('aaaaaa/',  {'name': 'lalalala'}, 'not_allowed', None),
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
            ('',    {'gender': 'm'},     'bad_request', 5),
            ('',    {'gender': 'f'},     'bad_request', 5),
            ('',    {'gender': 'v'},     'bad_request', 5),
            ('',    {'gender': 'bi'},    'bad_request', 5),
            # Why length=5? Because it's a plural update, that tried to update
            # all 5 Contact instances.

            # Handler forbids bulk-PUT requests
            ('',    [{}, {}],     'bad_request', 1),
            ('',    [{'gender':'M'}, {}],     'bad_request', 1),
            ('',    [{'name':'Randy'}, {'name': 'Harry'}],     'bad_request', 1),
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
            #   ``gender``
            ('4/',  {'name': 'lalalala', 'gender': 'f'}, 'bad_request', 1),
            ('4/',  {'name': 'lalala', 'gender': 'm'}, 'bad_request', 1),
            #   ``gender``        
            ('4/',  {'gender': 'm'}, 'bad_request', 1),
            #   ``list in request body
            ('5/',    [{}, {}],     'bad_request', 1),
            # Resource exists but is inaccessible
            ('6/',  {}, 'gone', None),
            ('6/',  {'name': 'lalalala'}, 'gone', None),
            ('6/',  {'gender': 'bi'}, 'gone', None),
            ('6/',  {}, 'gone', None),
            ('6/',  {'name': 'lalalala'}, 'gone', None),
            ('6/',    [{}, {}],     'bad_request', 1),
            # Resource does not exist
            ('100/',  {}, 'gone', None),
            ('100/',  {'name': 'lalalala'}, 'gone', None),
            ('100/',  {}, 'gone', None),
            ('100/',    [{}, {}],     'bad_request', 1),
            ('100/',  {'gender': 'bi'}, 'gone', None),
            ('100/',  {'name': 'lalalala'}, 'gone', None),
            ('100/',  {}, 'gone', None),
            ('100/',  {'name': 'lalalala'}, 'gone', None),
            ('aaa/',  {'name': 'lalalala'}, 'gone', None),
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

    def test_ContactHandler_delete_plural_filter_id(self):
        """
        Plural DELETE request, applying the filter ``id``.
        """
        handler = ContactHandler
        type = 'delete'
        test_data = (
            # Will only remove the 2 contacts with the given IDs
            ('?id=1&id=2',  {},  'populated_list', 2),
            # Will not remove the contact, since it's already removed
            ('?id=1',  {},  'empty_list', None),
            # Semantic error on querystring, returns a 422 error.
            ('?id=',  {},  'unprocessable', 1),
            ('?id=&id=1&id=2',  {},  'unprocessable', 1),
            ('?id=lalalala',  {},  'unprocessable', 1),
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
            ('aaaaa/',    {},     'gone', None),
        )
        self.execute(type, handler, test_data)

    def test_InfoHandler_read_singular(self):
        handler = InfoHandler
        type = 'read'
        test_data = (
            ('1/', {}, 'html', None),
            ('2/', {}, 'html', None),
        )
        self.execute(type, handler, test_data)

    def test_InfoHandler_read_plural(self):
        handler = InfoHandler
        type = 'read'
        test_data = (
            ('', {}, 'html', None),
        )
        self.execute(type, handler, test_data)

 
class TestResponseFields(TestResponseFieldsBase):
    """
    Testing whether the JSON responses contain all the fields they should.
    """
    fixtures = ['fixtures_all']
    USERNAME = 'user1'
    PASSWORD = 'pass1'
    endpoints = {
        AccountHandler: '/api/accounts/',
        ClientHandler:  '/api/clients/',
        ContactHandler: '/api/contacts/',
        InfoHandler: '/api/info/',
    }

    def test_ClientHandler_read_plural(self):
        handler = ClientHandler
        type = 'read'
        test_data = (
            ('', {}, ('name', 'accounts', 'contacts')),
            # When none of the given field exist, all the fields are returned
            ('?field=whatever', {}, ('name', 'accounts', 'contacts')),
            ('?field=name', {}, ('name',)),
            ('?field=accounts', {}, ('accounts',)),
            ('?field=contacts', {}, ('contacts',)),
            ('?field=contacts&field=accounts', {}, ('contacts', 'accounts')),
        )                
        self.execute(type, handler, test_data)

    def test_ClientHandler_read_singular(self):
        handler = ClientHandler
        type = 'read'
        test_data = (
            ('1/', {}, ('name', 'accounts', 'contacts',)),         
            # When none of the given field exist, all the fields are returned
            ('1/?field=whatever', {}, ('name', 'accounts', 'contacts')),         
            ('1/?field=name', {}, ('name',)),         
            ('1/?field=accounts', {}, ('accounts',)),         
            ('1/?field=contacts&field=accounts', {}, ('contacts', 'accounts')),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_create_plural(self):
        """
        Handler does not allow POST requests, so the data will be empty in this
        response.
        """
        handler = ClientHandler
        type = 'create'
        test_data = (
            ('', {}, ()),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_create_singular(self):
        """
        There is no such thing as a singular POST. 
        In anycase though, the handler does not allow POST requests.
        So the data part of the response will be empty always.
        """
        handler = ClientHandler
        type = 'create'
        test_data = (
            ('1/',  {}, ()),
            ('2/',  {}, ()),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_update_plural(self):
        """
        Handler does not allow PUT requests, so the data will be empty in this
        response.
        """
        handler = ClientHandler
        type = 'update'
        test_data = (
            ('', {}, ()),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_update_singular(self):
        """
        Handler does not allow PUT requests, so the data will be empty in this
        response.
        """
        handler = ClientHandler
        type = 'update'
        test_data = (
            ('1/', {}, ()),
            ('2/', {}, ()),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_delete_plural(self):
        """
        Handler does not allow DELETE requests, so the data will be empty in this
        response.
        """
        handler = ClientHandler
        type = 'delete'
        test_data = (
            ('', {}, ()),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_delete_singular(self):
        """
        Handler does not allow DELETE requests, so the data will be empty in this
        response.
        """
        handler = ClientHandler
        type = 'delete'
        test_data = (
            ('1/', {}, ()),
            ('2/', {}, ()),
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_read_plural(self):
        handler = AccountHandler
        type = 'read'
        test_data = (
            ('', {}, 
                ('id', 'first_name', 'last_name', 'client', 'datetime_now')),                
            ('?field=whatever', {}, 
                ('id', 'first_name', 'last_name', 'client', 'datetime_now')),                
            ('?field=id', {}, ('id',)),                
            ('?field=client', {}, ('client',)),                
            ('?field=datetime_now', {}, ('datetime_now',)),                
            ('?field=client&field=id', {}, ('client', 'id')),                
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_read_singular(self):
        handler = AccountHandler
        type = 'read'
        test_data = (
            ('1/', {}, 
                ('id', 'first_name', 'last_name', 'client', 'datetime_now')),
            ('1/?field=whatever', {}, 
                ('id', 'first_name', 'last_name', 'client', 'datetime_now')),
            ('1/?field=id', {}, ('id',)),
            ('1/?field=client', {}, ('client',)),
            ('1/?field=datetime_now', {}, ('datetime_now',)),
            ('1/?field=client&field=id', {}, ('client', 'id')),
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_create_plural(self):
        handler = AccountHandler
        type = 'create'
        test_data = (
            # Fails
            ( '', {}, (),),
            # Successful                
            (   
                '',
                {'username': 'userlalala', 'password': 'pass'},
                ('id', 'first_name', 'last_name', 'client', 'datetime_now'),    
            ),
            # Successful                
            (   
                '?field=id&field=client',
                {'username': 'userlalolo', 'password': 'pass'},
                ('id', 'client'),    
            ),
            # Successful                
            (   
                '?field=id&field=datetime_now',
                {'username': 'userlilili', 'password': 'pass'},
                ('id', 'datetime_now'),    
            ),
        )
        self.execute(type, handler, test_data)
    
    def test_AccountHandler_create_singular(self):
        """
        There is no such thing as a singular POST. All these requests will
        fail, and the data response will therefore be empty.
        """
        handler = AccountHandler
        type = 'create'
        test_data = (
            ('1/', {}, ()),                
            ('1/', {'username': 'user', 'password': 'pass'}, ()),                
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_update_plural(self):
        """
        Handler forbids plural PUT requests. All there requests will fail, and
        the data response will therefore be empty.
        """
        handler = AccountHandler
        type = 'update'
        test_data = (
            ('', {}, ()),                
            ('', {'first_name': 'name', 'last_name': 'surname'}, ()),                
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_update_singular(self):
        handler = AccountHandler
        type = 'update'
        
        test_data = (
            ('1/', {}, 
                ('first_name', 'last_name', 'id', 'client', 'datetime_now')),
            ('1/?field=whatever', {}, 
                ('first_name', 'last_name', 'id', 'client', 'datetime_now')),
            ('1/?field=id&field=client', {}, 
                ('id', 'client',)),                
            ('1/?field=datetime_now', {}, 
                ('datetime_now',)),                
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_delete_plural(self):
        """
        Handler forbids plural DELETe requests. All these requests will fail,
        and the data response will therefore be empty.
        """
        handler = AccountHandler
        type = 'delete'
        test_data = (
            ('', {}, ()),                
        )
        self.execute(type, handler, test_data)

    def test_AccountHandler_delete_singular(self):
        """
        I am logged in as account with id=1. If I delete this resource, I won't
        be able to issue more requests to the API handler. So instead I delete
        other Account resources of the same client.
        """
        handler = AccountHandler
        type = 'delete'

        test_data = (
            ('2/', {}, 
                ('first_name', 'last_name', 'id', 'client', 'datetime_now')),                
            # This fails because we already deleted the resource
            ('2/', {}, ()),                

            ('3/?field=whatever', {}, 
                ('first_name', 'last_name', 'id', 'client', 'datetime_now',)),                
            ('4/?field=id&field=last_name', {}, 
                ('id', 'last_name',)),                
            ('5/?field=client&field=datetime_now', {}, 
                ('client', 'datetime_now')),                
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_read_singular(self):
        handler = ContactHandler
        type = 'read'
        test_data = (
             # Resource exists and is Accessible
            ('1/',    {},
                ('client', 'name', 'surname', 'gender')),
            ('1/?field=whatever',    {},
                ('client', 'name', 'surname', 'gender')),
            ('1/?field=whatever&field=name',    {},
                ('name',)),
            ('1/?field=client&field=name',    {},
                ('client', 'name')),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_plural(self):
        handler = ContactHandler
        type = 'read'
        test_data = (
            ('',  {}, 
                ('client', 'name', 'surname', 'gender')),
            ('?field=whatever',  {}, 
                ('client', 'name', 'surname', 'gender')),
            ('?field=whatever&field=name',  {}, 
                ('name',)),
            ('?field=client&field=name',  {}, 
                ('client', 'name',)),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_filter_id(self):
        """
        Plural GET request, applying the filter ``id``.
        """
        handler = ContactHandler
        type = 'read'
        test_data = (
            ('?id=1',  {},                                 
                ('client', 'name', 'surname', 'gender')),
            ('?id=1&id=2',  {},  
                ('client', 'name', 'surname', 'gender')),
            ('?id=3&field=client&field=name',  {},  
                ('client', 'name',)),
            ('?id=4&field=whatever',  {},  
                ('client', 'name', 'surname', 'gender')),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_create_plural(self):       
        handler = ContactHandler
        type = 'create'

        test_data = (
            ('',    {},
                ('client', 'name', 'surname', 'gender')),

            ('?field=whatever',    {'name': 'Randy', 'surname': 'Frombelize'},  
                ('client', 'name', 'surname', 'gender')),


            ('?field=whatever&field=name',    {'name': 'Randy', 'surname': 'Frombelize'},  
                ('name',)),

            ('?field=name&field=client',    {'name': 'Randy', 'surname': 'Frombelize'},  
                ('client', 'name',)),
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_create_singular(self):
        """
        There is no such thing as a singular POST, so the data response will
        always be empty
        """                                   
        handler = ContactHandler
        type = 'create'

        test_data = (
            ('1/',  {}, ()),
            ('2/',  {'name': 'lalalala'},  ()),
        )            
        self.execute(type, handler, test_data)

    def test_ContactHandler_update_plural(self):    
        """
        The handler allows plural PUT requests.
        """
        handler = ContactHandler
        type = 'update'

        test_data = (
            ('',    {},     
                ('client', 'name', 'surname', 'gender')),

            ('?field=whatever',  {'name': 'Randy', 'surname': 'Frombelize'}, 
                ('client', 'name', 'surname', 'gender')),

            ('?field=name&field=client',    {'gender': 'M'},     
                ('client', 'name')),
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_update_singular(self):
        handler = ContactHandler
        type = 'update'
 
        test_data = (
            # Resource exist and is accessible
            ('1/',  {},
                ('client', 'name', 'surname', 'gender')),

            ('1/?field=whatever', {},
                ('client', 'name', 'surname', 'gender')),

            ('1/?field=client', {},
                ('client',)),

            ('1/?field=client&field=name', {},
                ('client', 'name',)),
        )            
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_delete_plural(self):
        """
        The handler allows plural DELETE requests.
        """
        handler = ContactHandler
        type = 'delete'
        test_data = (
            ('',  {},  
                ('client', 'name', 'surname', 'gender')),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_delete_plural_filter_id(self):
        """
        Plural DELETE request, applying the filter ``id``.
        """
        handler = ContactHandler
        type = 'delete'
        test_data = (
            ('?id=1&id=2',  {},  
                ('client', 'name', 'surname', 'gender')),
            ('?id=3&field=whatever',  {},  
                ('client', 'name', 'surname', 'gender')),
            ('?id=4&id=5&field=client&field=name',  {},  
                ('client', 'name',)),
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_delete_singular(self):
        handler = ContactHandler
        type = 'delete'
        test_data = (
            ('1/',    {},     
                ('client', 'name', 'surname', 'gender')),
            ('2/?field=whatever',    {},     
                ('client', 'name', 'surname', 'gender')),
            ('3/?field=client&field=name&field=surname',    {},     
                ('client', 'name', 'surname',)),
        )
        self.execute(type, handler, test_data)
 
