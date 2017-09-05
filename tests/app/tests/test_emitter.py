from django.test import TestCase

from icetea.handlers import BaseHandler
from icetea.emitters import Emitter

from app.handlers import AccountHandler, ClientHandler, ContactHandler
from app.models import Account, Client


class FooHandler(BaseHandler):
    pass


class TestEmitterWithDict(TestCase):

    def setUp(self):
        self.handler = FooHandler()

    def test_construct(self):
        """
        A nested dictionary should return the same nested dictionary if no
        fields are specified.
        """
        payload = {"a": 1, "b": 2, "c": {"d": 3}}
        e = Emitter(self.handler, payload, fields=())
        result = e.construct()
        self.assertEqual(result, payload)

    def test_construct_with_matching_fields(self):
        """
        A nested dictionary with fields specified should return the only those
        fields in the parent dictionary.
        """
        payload = {"a": 1, "b": 2, "c": {"d": 3}}
        e = Emitter(self.handler, payload, fields=("c"))
        result = e.construct()
        self.assertEqual(result, {"c": {"d": 3}})

    def test_construct_with_nonmatching_fields(self):
        """
        A nested dictionary with fields specified should return the only those
        fields in the parent dictionary.
        """
        payload = {"a": 1, "b": 2, "c": {"d": 3}}
        e = Emitter(self.handler, payload, fields=("d"))
        result = e.construct()
        self.assertEqual(result, {})


class TestEmitterWithSequence(TestCase):

    def setUp(self):
        self.handler = FooHandler()

    def test_construct(self):
        payload = (1, 2, 3)
        e = Emitter(self.handler, payload, fields=())
        result = e.construct()
        self.assertEqual(result, [1, 2, 3])

    def test_construct_with_dict(self):
        payload = ({"a": 1}, {"b": 2}, {"c": 3})
        e = Emitter(self.handler, payload, fields=())
        result = e.construct()
        self.assertEqual(result, list(payload))


class TestEmitterWithModel(TestCase):

    def setUp(self):
        self.client = Client.objects.create(name="klm")
        self.account = Account.objects.create(client=self.client)

        self.account_handler = AccountHandler()
        self.client_handler = ClientHandler()
        self.contact_handler = ContactHandler()

        # Hack into typemapper
        Emitter.TYPEMAPPER[self.account_handler] = self.account_handler.model
        Emitter.TYPEMAPPER[self.client_handler] = self.client_handler.model
        Emitter.TYPEMAPPER[self.contact_handler] = self.contact_handler.model

    def test_construct(self):
        e = Emitter(self.client_handler, self.client, fields=["name"])

        self.assertEqual({"name": u"klm"}, e.construct())

    def test_construct_fk(self):
        e = Emitter(self.account_handler, self.account,
                    fields=["client", "client_id"])

        # Ensure Django 1.6 behaviour is maintained. When a foreign key field,
        # i.e. client_id is included in `allowed_out_fields` the numeric value
        # should be emmited instead of an object representation.
        self.assertEqual(
            {
                "client": {
                    "name": "klm"
                },
                "client_id": self.client.id
            },
            e.construct(),
        )


class TestEmitterWithQuerySet(TestCase):
    pass
