from piston.handler import BaseHandler
from piston.utils import rc
from libcloud.types import InvalidCredsException
from overmind.provisioning.provider_meta import PROVIDERS
from overmind.provisioning.models import Provider, Node, get_state
from overmind.provisioning.forms import ProviderForm, NodeForm
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
        for field in self.fields:
            if field == 'id': continue
            if field not in attrs:
                resp = rc.BAD_REQUEST
                resp.write(': field %s missing' % field)
                return resp
        
        # Validate keys
        for field in ['access_key', 'secret_key']:
            if attrs[field] == "":
                if PROVIDERS[attrs['provider_type']][field] is not None:
                    resp = rc.BAD_REQUEST
                    resp.write(': %s is a required field' % field)
                    return resp
            elif PROVIDERS[attrs['provider_type']][field] is None:
                resp = rc.BAD_REQUEST
                resp.write(': %s must be empty' % field)
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
                access_key=attrs['access_key'],
                secret_key=attrs['secret_key']
            )
            try:
                provider.save()
                provider.import_nodes()
                return provider
            except InvalidCredsException:
                provider.delete()
                resp = rc.BAD_REQUEST
                resp.write(': Invalid Credentials')
                return resp
    
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
        
        # Provider exists
        try:
            provider = Provider.objects.get(id=provider_id)
            if not provider.supports('create'):
                return rc.NOT_IMPLEMENTED
        except Provider.DoesNotExist:
            resp = rc.BAD_REQUEST
            resp.write(': Provider with id="%s" does not exist' % provider_id)
            return resp
        
        # Modify REST "provider_id" to "provider" (expected form field)
        data = copy.deepcopy(request.POST)
        data['provider'] = data['provider_id']
        del data['provider_id']
        form = NodeForm(provider.id, data)
        
        if form.is_valid():
            try:
                n = Node.objects.get(
                    provider=provider, name=form.cleaned_data['name']
                )
                #error = 'A node with that name already exists'
                return rc.DUPLICATE_ENTRY
            except Node.DoesNotExist:
                data_from_provider = provider.create_node(form)
                if data_from_provider is None:
                    #error = 'Could not create Node'
                    return rc.INTERNAL_ERROR
                else:
                    node = form.save(commit = False)
                    node.uuid      = data_from_provider['uuid']
                    node.public_ip = data_from_provider['public_ip']
                    node.state     = get_state(data_from_provider['state'])
                    node.save()
                    logging.info('New node created %s' % node)
                    #return HttpResponse('<p>success</p>')
                    return node
        else:
            resp = rc.BAD_REQUEST
            for k, v in form.errors.items():
                error = v[0]
                if type(error) != unicode:
                    error = error.__unicode__()
                resp.write("\n" + k + ": " + error)
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
        id = kwargs.get('id')
        if id is None:
            return rc.BAD_REQUEST
        
        try:
            node = self.model.objects.get(id=id)
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
