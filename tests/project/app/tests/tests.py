from base import TestResponseStatusBase
from project.app.handlers import AccountHandler, ClientHandler, ContactHandler

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
    def test_plural_ClientHandler(self):
        handler = ClientHandler
        type = 'read'
        test_data = (
            ('',  {},     self.OK),
        )
        self.execute(type, handler, test_data)

    def test_singular_ClientHandler(self):
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

    


