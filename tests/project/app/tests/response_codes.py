from project.app.handlers import AccountHandler, ClientHandler, ContactHandler
from project.app.tests.base import TestResponseStatusBase

"""
Fixtures:
    Client 1
        Account1, Account2, Account3, Account4, Account5
        Contact1, Contact2, Contact3, Contact4, Contact5
    Client 2
        Account6
        Contact6
    Client 3
        Account7
        Contact7
    Client 4
        Account8
        Contact8
    Client 5
        Account9
        Contact9
"""  

class TestResponseStatus(TestResponseStatusBase):    
    def test_ClientHandler_read_plural(self):
        handler = ClientHandler
        type = 'read'
        test_data = (
            ('',  {},     self.OK),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_read_singular(self):
        handler = ClientHandler
        type = 'read'
        test_data = (
            # Accessible
            ('1/',    {},     self.OK),
            # Inaccessible
            ('2/',    {},     self.E_GONE),
            ('3/',    {},     self.E_GONE),
            ('4/',    {},     self.E_GONE),
            ('5/',    {},     self.E_GONE),
            # Non existent
            ('6/',    {},     self.E_GONE),
            ('7/',    {},     self.E_GONE),
            ('8/',    {},     self.E_GONE),
            ('9/',    {},     self.E_GONE),
            ('10/',    {},     self.E_GONE),
            ('100/',    {},     self.E_GONE),
            ('1000/',    {},     self.E_GONE),
            ('10000/',    {},     self.E_GONE),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_post_plural(self):
        """
        Handler does not allow POST. So all these should give a 405 response
        """
        handler = ClientHandler
        type = 'create'
        test_data = (
            ('',    {},     self.E_NOT_ALLOWED),
            ('',    {'name': 'lalala'},     self.E_NOT_ALLOWED),
            ('',    {'parameter': 'lalala'},     self.E_NOT_ALLOWED),
            ('',    ('parameter'),     self.E_NOT_ALLOWED),
            ('',    [{}, {}],     self.E_NOT_ALLOWED),
            ('',    [{'param1':'lalala'}, {'param2':'lololo'}],     self.E_NOT_ALLOWED),
        )
        self.execute(type, handler, test_data)

    def test_ClientHandler_post_singular(self):
        """
        There is no such thing as a singular POST. 
        In anycase though, the handler does not allow POST requests.
        """
        handler = ClientHandler
        type = 'create'
        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, self.E_NOT_ALLOWED),
            ('1/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            # Resource exists but is not accessible
            ('2/',  {}, self.E_NOT_ALLOWED),
            ('2/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('3/',  {}, self.E_NOT_ALLOWED),
            ('3/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            # Resource does not exist
            ('5/',  {}, self.E_NOT_ALLOWED),
            ('5/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('6/',  {}, self.E_NOT_ALLOWED),
            ('6/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('7/',  {}, self.E_NOT_ALLOWED),
            ('7/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('10/',  {}, self.E_NOT_ALLOWED),
            ('10/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('100/',  {}, self.E_NOT_ALLOWED),
            ('100/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('1000/',  {}, self.E_NOT_ALLOWED),
            ('1000/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
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
            ('',    {},     self.E_NOT_ALLOWED),
            ('',    {'name': 'lalala'},     self.E_NOT_ALLOWED),
            ('',    {'parameter': 'lalala'},     self.E_NOT_ALLOWED),
            ('',    ('parameter'),     self.E_NOT_ALLOWED),
            ('',    [{}, {}],     self.E_NOT_ALLOWED),
            ('',    [{'param1':'lalala'}, {'param2':'lololo'}],     self.E_NOT_ALLOWED),
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
            ('1/',  {}, self.E_NOT_ALLOWED),
            ('1/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            # Resource exists but is not accessible
            ('2/',  {}, self.E_NOT_ALLOWED),
            ('2/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('3/',  {}, self.E_NOT_ALLOWED),
            ('3/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            # Resource does not exist
            ('5/',  {}, self.E_NOT_ALLOWED),
            ('5/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('6/',  {}, self.E_NOT_ALLOWED),
            ('6/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('7/',  {}, self.E_NOT_ALLOWED),
            ('7/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('10/',  {}, self.E_NOT_ALLOWED),
            ('10/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('100/',  {}, self.E_NOT_ALLOWED),
            ('100/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('1000/',  {}, self.E_NOT_ALLOWED),
            ('1000/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
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
            ('',  {},     self.E_NOT_ALLOWED),
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
            ('1/',    {},     self.E_NOT_ALLOWED),
            # Inaccessible
            ('2/',    {},     self.E_NOT_ALLOWED),
            ('3/',    {},     self.E_NOT_ALLOWED),
            ('4/',    {},     self.E_NOT_ALLOWED),
            ('5/',    {},     self.E_NOT_ALLOWED),
            # Non existent
            ('6/',    {},     self.E_NOT_ALLOWED),
            ('7/',    {},     self.E_NOT_ALLOWED),
            ('8/',    {},     self.E_NOT_ALLOWED),
            ('9/',    {},     self.E_NOT_ALLOWED),
            ('10/',    {},     self.E_NOT_ALLOWED),
            ('100/',    {},     self.E_NOT_ALLOWED),
            ('1000/',    {},     self.E_NOT_ALLOWED),
            ('10000/',    {},     self.E_NOT_ALLOWED),
        )
        self.execute(type, handler, test_data)
 
    def test_AccountHandler_read_plural(self):
        pass
    def test_AccountHandler_read_singular(self):
        pass
    def test_AccountHandler_create_plural(self):
        pass
    def test_AccountHandler_create_singular(self):
        pass
    def test_AccountHandler_update_plural(self):
        pass
    def test_AccountHandler_update_singular(self):
        pass
    def test_AccountHandler_delete_plural(self):
        pass
    def test_AccountHandler_delete_singular(self):
        pass                                                   


    def test_ContactHandler_read_plural(self):
        handler = ContactHandler
        type = 'read'
        test_data = (
            ('',  {},     self.OK),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_read_singular(self):
        handler = ContactHandler
        type = 'read'
        test_data = (
            # Resource exists and is Accessible
            ('1/',    {},     self.OK),
            ('2/',    {},     self.OK),
            ('3/',    {},     self.OK),
            ('4/',    {},     self.OK),
            ('5/',    {},     self.OK),
            # Resource exists but is inaccessible
            ('6/',    {},     self.E_GONE),
            ('7/',    {},     self.E_GONE),
            ('8/',    {},     self.E_GONE),
            ('9/',    {},     self.E_GONE),
            # Resource does not exist
            ('10/',    {},     self.E_GONE),
            ('100/',    {},     self.E_GONE),
            ('1000/',    {},     self.E_GONE),
            ('10000/',    {},     self.E_GONE),
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_create_plural(self):       
        handler = ContactHandler
        type = 'create'

        test_data = (
            ('',    {},     self.OK),
            ('',    {'name': 'Randy', 'surname': 'Frombelize'},     self.OK),
            ('',    {'gender': 'M'},     self.OK),
            ('',    {'gender': 'F'},     self.OK),           
            # Invalid values for ``gender``
            ('',    {'gender': 'm'},     self.E_BAD_REQUEST),
            ('',    {'gender': 'f'},     self.E_BAD_REQUEST),
            ('',    {'gender': 'v'},     self.E_BAD_REQUEST),
            ('',    {'gender': 'bi'},     self.E_BAD_REQUEST),
            # Handler forbids bulk-POST requests
            ('',    [{}, {}],     self.E_BAD_REQUEST),
            ('',    [{'gender':'M'}, {}],     self.E_BAD_REQUEST),
            ('',    [{'name':'Randy'}, {'name': 'Harry'}],     self.E_BAD_REQUEST),
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
            ('1/',  {}, self.E_NOT_ALLOWED),
            ('1/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            # Resource exists but is not accessible
            ('2/',  {}, self.E_NOT_ALLOWED),
            ('2/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('3/',  {}, self.E_NOT_ALLOWED),
            ('3/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('3/',    [{}, {}],     self.E_NOT_ALLOWED),
            # Resource does not exist
            ('5/',  {}, self.E_NOT_ALLOWED),
            ('5/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('6/',  {}, self.E_NOT_ALLOWED),
            ('6/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('7/',  {}, self.E_NOT_ALLOWED),
            ('7/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('10/',  {}, self.E_NOT_ALLOWED),
            ('10/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('100/',  {}, self.E_NOT_ALLOWED),
            ('100/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
            ('1000/',  {}, self.E_NOT_ALLOWED),
            ('1000/',  {'name': 'lalalala'}, self.E_NOT_ALLOWED),
        )            
        self.execute(type, handler, test_data)
 

    def test_ContactHandler_update_plural(self):    
        """
        The handler forbids plural PUT requests.
        So the API should respond with a 405 error
        """
        handler = ContactHandler
        type = 'update'

        test_data = (
            ('',    {},     self.E_NOT_ALLOWED),
            ('',    {'name': 'Randy', 'surname': 'Frombelize'},     self.E_NOT_ALLOWED),
            ('',    {'gender': 'M'},     self.E_NOT_ALLOWED),
            ('',    {'gender': 'F'},     self.E_NOT_ALLOWED),           
            # Invalid values for ``gender``
            ('',    {'gender': 'm'},     self.E_NOT_ALLOWED),
            ('',    {'gender': 'f'},     self.E_NOT_ALLOWED),
            ('',    {'gender': 'v'},     self.E_NOT_ALLOWED),
            ('',    {'gender': 'bi'},     self.E_NOT_ALLOWED),
            # Handler forbids bulk-POST requests
            ('',    [{}, {}],     self.E_NOT_ALLOWED),
            ('',    [{'gender':'M'}, {}],     self.E_NOT_ALLOWED),
            ('',    [{'name':'Randy'}, {'name': 'Harry'}],     self.E_NOT_ALLOWED),
        )
        self.execute(type, handler, test_data)
 
    def test_ContactHandler_update_singular(self):
        handler = ContactHandler
        type = 'update'
 
        test_data = (
            # Resource exist and is accessible
            ('1/',  {}, self.OK),
            ('1/',  {'name': 'lalalala'}, self.OK),
            ('2/',  {}, self.OK),
            ('2/',  {'name': 'lalalala'}, self.OK),
            ('3/',  {'gender': 'M'}, self.OK),
            ('3/',  {'name': 'lalala', 'gender': 'F'}, self.OK),
            # ``gender``
            ('4/',  {'name': 'lalalala', 'gender': 'f'}, self.E_BAD_REQUEST),
            ('4/',  {'name': 'lalala', 'gender': 'm'}, self.E_BAD_REQUEST),
            # ``gender``        
            ('4/',  {'gender': 'm'}, self.E_BAD_REQUEST),
            # ``list in request body
            ('5/',    [{}, {}],     self.E_BAD_REQUEST),
            # Resource exists but is inaccessible
            ('6/',  {}, self.E_GONE),
            ('6/',  {'name': 'lalalala'}, self.E_GONE),
            ('7/',  {}, self.E_GONE),
            ('7/',  {'name': 'lalalala'}, self.E_GONE),
            ('10/',  {}, self.E_GONE),
            ('10/',  {'name': 'lalalala'}, self.E_GONE),
            ('100/',  {}, self.E_GONE),
            ('100/',  {'name': 'lalalala'}, self.E_GONE),
            ('1000/',  {}, self.E_GONE),
            ('1000/',  {'name': 'lalalala'}, self.E_GONE),
        )            
        self.execute(type, handler, test_data)
    
    def test_ContactHandler_delete_plural(self):
        """
        The handler forbids plural DELETE requests.
        So we should get a 405 Error.
        """
        handler = ContactHandler
        type = 'delete'
        test_data = (
            ('',  {},     self.E_NOT_ALLOWED),
        )
        self.execute(type, handler, test_data)

    def test_ContactHandler_delete_singular(self):
        handler = ContactHandler
        type = 'delete'
        test_data = (
            # Resource exists and is Accessible
            ('1/',    {},     self.OK),
            ('2/',    {},     self.OK),
            ('3/',    {},     self.OK),
            ('4/',    {},     self.OK),
            ('5/',    {},     self.OK),
            # Resource exists but is inaccessible
            ('6/',    {},     self.E_GONE),
            ('7/',    {},     self.E_GONE),
            ('8/',    {},     self.E_GONE),
            ('9/',    {},     self.E_GONE),
            # Resource does not exist
            ('10/',    {},     self.E_GONE),
            ('100/',    {},     self.E_GONE),
            ('1000/',    {},     self.E_GONE),
            ('10000/',    {},     self.E_GONE),
        )
        self.execute(type, handler, test_data)
 
