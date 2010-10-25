from piston.handler import BaseHandler
from piston.utils import rc
from libcloud.types import InvalidCredsException

from provisioning.provider_meta import PROVIDERS
from provisioning.models import Provider, Node, get_state
from provisioning.views import save_new_node, save_new_provider
import copy, logging

# Unit tests are not working for HttpBasicAuthentication
# This is a hack until authentication is reimplemented as OAuth
# (waiting for a new piston version)
_TESTING = False

class ProviderHandler(BaseHandler):
    fields = ('id', 'name', 'provider_type', 'access_key')
    model = Provider
    
    def create(self, request):
        if not _TESTING and not request.user.has_perm('provisioning.add_provider'):
            return rc.FORBIDDEN
        
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        
        # Pass data to form Validation
        error, form, provider = save_new_provider(attrs)
        if error is None:
            return provider
        else:
            resp = rc.BAD_REQUEST
            if error == 'form':
                for k, v in form.errors.items():
                    formerror = v[0]
                    if type(formerror) != unicode:
                        formerror = formerror.__unicode__()
                    resp.write("\n" + k + ": " + formerror)
            else:
                resp.write("\n" + error)
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
        if not _TESTING and not request.user.has_perm('provisioning.change_provider'):
            return rc.FORBIDDEN
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        
        # Check that it is a valid provider
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
        if name is not None and name != provider.name:
            try:
                self.model.objects.get(name=name)
                return rc.DUPLICATE_ENTRY
            except self.model.DoesNotExist:
                provider.name = name
        
        # Get provider_type (not an update option)
        provider_type = provider.provider_type
        
        # Validate keys
        for field in ['access_key', 'secret_key']:
            if PROVIDERS[provider_type][field] is None or field not in attrs:
                continue
            field_value = attrs[field]
            if field_value == "":
                resp = rc.BAD_REQUEST
                resp.write(': %s cannot be empty' % param)
                return resp
            setattr( provider, field, field_value )
        
        provider.save()
        return provider
    
    def delete(self, request, *args, **kwargs):
        if not _TESTING and not request.user.has_perm('provisioning.delete_provider'):
            return rc.FORBIDDEN
        id = kwargs.get('id')
        if id is None:
            return rc.BAD_REQUEST
        try:
            prov = self.model.objects.get(id=id)
            prov.delete()
            return rc.DELETED
        except self.model.DoesNotExist:
            return rc.NOT_FOUND


class NodeHandler(BaseHandler):
    fields = ('id', 'name', ('provider', ('id', 'name', 'provider_type')),
        'uuid', 'public_ip', 'state', 'environment', 'extra_data')
    model = Node
    
    def create(self, request):
        if not _TESTING and not request.user.has_perm('provisioning.add_node'):
            return rc.FORBIDDEN
        if not hasattr(request, "data"):
            request.data = request.POST
        attrs = self.flatten_dict(request.data)
        
        # Modify REST "provider_id" to "provider" (expected form field)
        data = copy.deepcopy(request.POST)
        data['provider'] = data.get('provider_id','')
        if 'provider_id' in data: del data['provider_id']
        
        # Validate data and save new node
        error, form, node = save_new_node(data, request.user)
        if error is None:
            return node
        else:
            resp = rc.BAD_REQUEST
            if error == 'form':
                for k, v in form.errors.items():
                    formerror = v[0]
                    if type(formerror) != unicode:
                        formerror = formerror.__unicode__()
                    resp.write("\n" + k + ": " + formerror)
            else:
                resp.write("\n" + error)
            return resp
    
    def read(self, request, *args, **kwargs):
        id = kwargs.get('id')
        
        if id is None:
            # If name specified, return node
            name = request.GET.get('name')
            if name is not None:
                try:
                    return self.model.objects.get(name=name)
                except self.model.DoesNotExist:
                    return rc.NOT_FOUND
            # Else return a subset of nodes
            query = self.model.objects.all()
            provider_id = request.GET.get('provider_id')
            if provider_id is not None:
                query = query.filter(provider=provider_id)
            if request.GET.get('show_decommissioned') != 'true':
                query = query.exclude(environment='Decommissioned')
            return query
        else:
            # Return the selected node
            try:
                return self.model.objects.get(id=id)
            except self.model.DoesNotExist:
                return rc.NOT_FOUND
    
    def update(self, request, *args, **kwargs):
        if not _TESTING and not request.user.has_perm('provisioning.change_node'):
            return rc.FORBIDDEN
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
        if not _TESTING and not request.user.has_perm('provisioning.delete_node'):
            return rc.FORBIDDEN
        id = kwargs.get('id')
        if id is None:
            return rc.BAD_REQUEST
        try:
            node = self.model.objects.get(id=id)
            if node.environment == 'Decommissioned':
                return rc.NOT_HERE
            if node.provider.supports('destroy'):
                node.destroy()
            else:
                node.decommission()
            return rc.DELETED
        except self.model.DoesNotExist:
            return rc.NOT_FOUND
