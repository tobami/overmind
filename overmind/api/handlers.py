from piston.handler import BaseHandler
from piston.utils import rc
from libcloud.types import InvalidCredsException
from overmind.provisioning.provider_meta import PROVIDERS
from overmind.provisioning.models import Provider, Node, get_state
from overmind.provisioning.views import save_new_node
import copy, logging


def validate_parameters(data, param):
    if data.get(param) is None:
        resp = rc.BAD_REQUEST
        resp.write(': Parameter "%s" is missing' % param)
        return resp
    elif data.get(param) == "":
        resp = rc.BAD_REQUEST
        resp.write(': Parameter "%s" is empty' % param)
        return resp
    else:
        return True

class ProviderHandler(BaseHandler):
    fields = ('id', 'name', 'provider_type', 'access_key', 'secret_key')
    model = Provider
    
    def create(self, request):
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        
        # Data validation
        # Correct provider
        resp = validate_parameters(attrs, 'provider_type')
        if resp is not True: return resp
        if attrs['provider_type'] not in PROVIDERS.keys():
            resp = rc.BAD_REQUEST
            resp.write(': wrong provider_type')
            return resp
        
        # All fields are present
        for field in ['name', 'provider_type']:
            if field == 'id': continue
            if field not in attrs:
                resp = rc.BAD_REQUEST
                resp.write(': field %s missing' % field)
                return resp
        
        # Validate keys
        for field in ['access_key', 'secret_key']:
            if PROVIDERS[attrs['provider_type']][field] is None: continue
            elif field not in attrs or attrs[field] == "":
                if PROVIDERS[attrs['provider_type']][field] is not None:
                    resp = rc.BAD_REQUEST
                    resp.write(': %s is a required field' % field)
                    return resp
        
        try:
            # Look for duplicates
            self.model.objects.get(name=attrs['name'])
            return rc.DUPLICATE_ENTRY
        except self.model.DoesNotExist:
            # Create new provider
            provider = Provider(
                name=attrs['name'], 
                provider_type=attrs['provider_type'],
                access_key=attrs.get('access_key', ''),
                secret_key=attrs.get('secret_key', ''),
            )
            try:
                provider.save()
                provider.import_nodes()
            except InvalidCredsException:
                if provider.id is not None: provider.delete()
                resp = rc.BAD_REQUEST
                resp.write(': Invalid Credentials')
                return resp
            
            return provider
    
    def read(self, request, *args, **kwargs):
        id = kwargs.get('id')
        
        if id is None:
            provider_type = request.GET.get('provider_type')
            name = request.GET.get('name')
            if provider_type is not None:
                return self.model.objects.filter(
                    provider_type=provider_type,
                )
            elif name is not None:
                try:
                    return self.model.objects.get(name=name)
                except self.model.DoesNotExist:
                    return rc.NOT_FOUND
            else:
                return self.model.objects.all()
        else:
            try:
                return self.model.objects.get(id=id)
            except self.model.DoesNotExist:
                return rc.NOT_FOUND
    
    def update(self, request, *args, **kwargs):
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        id = kwargs.get('id')
        if id is None:
            return rc.BAD_REQUEST
        
        try:
            provider = self.model.objects.get(id=id)
        except self.model.DoesNotExist:
            return rc.NOT_FOUND
        attrs = self.flatten_dict(request.POST)
        
        # Update name if present
        name = attrs.get('name')
        if name is not None:
            try:
                self.model.objects.get(name=name)
                return rc.DUPLICATE_ENTRY
            except self.model.DoesNotExist:
                node.name = name
        
        # Get provider_type (not an update option)
        provider_type = provider.provider_type
        
        # Validate keys
        for field in ['access_key', 'secret_key']:
            field_value = attrs.get(field)
            if field_value is None:
                continue
            if field_value == "":
                if PROVIDERS[provider_type][field] is not None:
                    return rc.BAD_REQUEST
            elif PROVIDERS[provider_type][field] is None:
                return rc.BAD_REQUEST
            setattr( provider, field, field_value )
        
        provider.save()
        return provider


class NodeHandler(BaseHandler):
    fields = ('id', 'name', ('provider', ('id', 'name', 'provider_type')),
        'uuid', 'public_ip', 'state', 'production_state')
    model = Node
    
    def create(self, request):
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        
        # provider_id is correct
        resp = validate_parameters(attrs, 'provider_id')
        provider_id = attrs.get('provider_id')
        if resp is not True: return resp
        
        # Modify REST "provider_id" to "provider" (expected form field)
        data = copy.deepcopy(request.POST)
        data['provider'] = data['provider_id']
        del data['provider_id']
        
        # Validate data and save new node
        error, form, node = save_new_node(data)
        if error is None:
            return node
        else:
            resp = rc.BAD_REQUEST
            if error == 'form':
                for k, v in form.errors.items():
                    formerror = v[0]
                    if type(error) != unicode:
                        formerror = formerror.__unicode__()
                    resp.write("\n" + k + ": " + formerror)
            else:
                resp.write("\n" + error)
            return resp
    
    def read(self, request, *args, **kwargs):
        id = kwargs.get('id')
        
        if id is None:
            provider_id = request.GET.get('provider_id')
            name = request.GET.get('name')
            if provider_id is not None:
                return self.model.objects.filter(
                    provider=provider_id,
                )
            elif name is not None:
                try:
                    return self.model.objects.get(name=name)
                except self.model.DoesNotExist:
                    return rc.NOT_FOUND
            else:
                return self.model.objects.all()
        else:
            try:
                return self.model.objects.get(id=id)
            except self.model.DoesNotExist:
                return rc.NOT_FOUND
    
    def update(self, request, *args, **kwargs):
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        id = kwargs.get('id')
        if id is None:
            return rc.BAD_REQUEST
        
        try:
            node = self.model.objects.get(id=id)
        except self.model.DoesNotExist:
            return rc.NOT_FOUND
        
        # Update name if present
        name = attrs.get('name')
        if name is not None and name != node.name:
            try:
                self.model.objects.get(name=name)
                return rc.DUPLICATE_ENTRY
            except self.model.DoesNotExist:
                node.name = name
        node.save()
        return node
    
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
