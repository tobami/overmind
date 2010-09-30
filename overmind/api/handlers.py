from piston.handler import BaseHandler
from overmind.provisioning.provider_meta import PROVIDERS
from overmind.provisioning.models import Provider, Node
from piston.utils import rc


class ProviderHandler(BaseHandler):
    fields = ('id', 'name', 'provider_type', 'access_key', 'secret_key')
    model = Provider
    
    def create(self, request):
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        
        # Data validation
        for field in self.fields:
            if field == 'id': continue
            if field not in attrs:
                return rc.BAD_REQUEST
        if attrs['provider_type'] not in PROVIDERS.keys():
            return rc.NOT_FOUND
        for field in ['access_key', 'secret_key']:
            if attrs[field] == "":
                if PROVIDERS[attrs['provider_type']][field] is not None:
                    return rc.BAD_REQUEST
            elif PROVIDERS[attrs['provider_type']][field] is None:
                return rc.BAD_REQUEST
        
        # Look for duplicates
        try:
            self.model.objects.get(name=attrs['name'])
            return rc.DUPLICATE_ENTRY
        except self.model.DoesNotExist:
            provider = Provider(name=attrs['name'], 
                            provider_type=attrs['provider_type'],
                            access_key=attrs['access_key'],
                            secret_key=attrs['secret_key'])
            provider.save()
            provider.import_nodes()
            return provider
    
    def read(self, request, *args, **kwargs):
        id = kwargs.get('id')
        if id is None:
            return Provider.objects.all()
        else:
            try:
                p = self.model.objects.get(id=id)
                return p
            except self.model.DoesNotExist:
                return rc.NOT_FOUND
    
    def update(self, request, *args, **kwargs):
        id = kwargs.get('id')
        if id is None:
            return rc.BAD_REQUEST
        
        try:
            provider = self.model.objects.get(id=id)
        except self.model.DoesNotExist:
            return rc.NOT_FOUND
        attrs = self.flatten_dict(request.POST)
        name = attrs.get('name')
        if name is not None: provider.name = name
        
        # Validate
        for field in ['access_key', 'secret_key']:
            field_value = attrs.get(field)
            if field_value is None: continue
            if field_value == "":
                if PROVIDERS[attrs['provider_type']][field] is not None:
                    return rc.BAD_REQUEST
            elif PROVIDERS[attrs['provider_type']][field] is None:
                return rc.BAD_REQUEST
            
            setattr( provider, field, field_value )
        
        provider.save()
        return provider


class NodeHandler(BaseHandler):
    fields = ('id', 'name', ('provider', ('id', 'name', 'provider_type')),
        'uuid', 'public_ip', 'state', 'production_state')
    model = Node
    
    #TODO:Create with not implemented error
    
    def delete(self, request, *args, **kwargs):
        id = kwargs.get('id')
        
        if id is None:
            return rc.BAD_REQUEST
        try:
            node = self.model.objects.get(id=id)
            if not node.provider.supports('destroy'):
                return rc.NOT_IMPLEMENTED
            if node.production_state == 'DE':
                return rc.NOT_HERE
            node.destroy()
            return rc.DELETED
        except self.model.DoesNotExist:
            return rc.NOT_FOUND
