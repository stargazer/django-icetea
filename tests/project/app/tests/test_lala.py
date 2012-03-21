from django.test import TestCase
from django.test import Client

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

class BaseTest(TestCase):
    fixtures = ['fixtures_all',]

    USERNAME = 'user1'
    PASSWORD = 'pass1'

    def setUp(self):
        self.browser = Client()        
        self.browser.login(
            username=self.USERNAME,
            password=self.PASSWORD,
        )                


class Test1(BaseTest):

    def test_a(self):
        return True
