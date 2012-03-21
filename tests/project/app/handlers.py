from icetea.handlers import ModelHandler
from project.app.models import Client, Account, Contact

                                    
class ClientHandler(ModelHandler):
    model = Client
    authentication = True

    read = True
    
    allowed_out_fields= (    
        'name',
        'accounts',
    )

    allowed_in_fields = ()

    def working_set(self, request, *args, **kwargs):
        """
        Limit the working set only to the client to which the logged in user
        belongs to.
        """
        return super(ClientHandler, self).\
            working_set(request, *args, **kwargs).\
            filter(id=request.user.account.client_id)


class ClientModelHandler(ModelHandler):
    """
    Abstract Handler, that defines common behaviour for other handlers to
    inherit from.
    """
    read = True
    create = True
    update = True
    delete = True

    def working_set(self, request, *args, **kwargs):
        """
        Limits the working set to model instances that belong to the client
        of the logged in user.
        """
        return super(ClientModelHandler, self).\
            working_set(request, *args, **kwargs).\
            filter(client=request.user.account.client)

    def validate(self, request, *args, **kwargs):
        request.data['client_id'] = request.user.account.client.id
        super(ClientModelHandler, self).\
            validate(request, *args, **kwargs)

class AccountHandler(ClientModelHandler):
    model = Account
    authentication = True

    read = True

    allowed_out_fields = (
        'id', 
        'first_name',
        'last_name',
        'client',
    )

    exclude_nested = (
        # Saves us from an infinite loop (Recursion depth exceeded)
        'client',
    )

    allowed_in_fields = ()

class ContactHandler(ClientModelHandler):
    model = Contact
    authentication = True

    read = True
    create = True
    update = True
    delete = True

    allowed_out_fields = (
        'client', 
        'name',
        'surname',
        'gender',
    )

    allowed_in_fields = (
        'name',
        'surname',
        'gender',
    )

    exclude_nested = (
        'client',
    )


