from icetea.handlers import ModelHandler, BaseHandler
from project.app.models import Client, Account, Contact

                                    
class ClientHandler(ModelHandler):
    model = Client
    authentication = True

    read = True
    
    allowed_out_fields= (    
        'name',
        'accounts',
        'contacts',
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
        for item in isinstance(request.data, dict) and [request.data] or \
            request.data:
            item['client_id'] = request.user.account.client.id
        
        super(ClientModelHandler, self).\
            validate(request, *args, **kwargs)

class AccountHandler(ClientModelHandler):
    model = Account
    authentication = True

    read = True
    create = True
    update = True
    delete = True

    allowed_out_fields = (
        'id', 
        'first_name',
        'last_name',
        'client',
        # fake model field
        'datetime_now',
    )
    allowed_in_fields = (
        'username',
        'password',
        'first_name',
        'last_name',
        'email_address',
    )

    exclude_nested = (
        # Saves us from an infinite loop (Recursion depth exceeded)
        'client',
    )


class ContactHandler(ClientModelHandler):
    model = Contact
    authentication = True

    read = True
    create = True
    update = True
    delete = True
    bulk_create = True
    plural_delete = True
    plural_update = True

    filters = dict(
        id='id__in',
    )

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

class InfoHandler(BaseHandler):
    """
    I implement this handler, in order to test the emitter_format = html,
    keyword argument, in the url mapper.
    """
    read = True

    allowed_out_fields = (
        'name',
        'surname',
    )

    def data_set(self, request, *args, **kwargs):
        return """
            <html>
                <body>
                name=name1 <br>
                surname=surname1 <br>
                id=1 <br>
                <br>            
                name=name2 <br>
                surname=surname2 <br>
                id=2 <br>
                </body>
            </html>                       
        """
        



