from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from overmind.provisioning.models import Provider, Instance
from overmind.provisioning.forms import ProviderForm, InstanceForm
from libcloud.types import NodeState, InvalidCredsException


def overview(request):
    provider_list = Provider.objects.all()
    instance_list = Instance.objects.all()
    return render_to_response('overview.html', {
        'instance_list': instance_list,
        'provider_list': provider_list,
    })

def newprovider(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ProviderForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Check that the account is valid
            prov = form.save(commit = False)
            ## Check provider
            #TODO: Turn into models.Provider.check_credentials
            #TODO: Improve check.
            try:
                controller = ProviderController(prov)
            except InvalidCredsException:
                print "InvalidCredentials!"
                return render_to_response('provider.html', { 'form': form })
                #TODO: return a form error
                #NOTE: rackspace returns InvalidCredsException on class init but EC2 does not
            ## END Check
            newprovider = form.save()
            newprovider.import_nodes()
            
            return HttpResponseRedirect('/overview/') # Redirect after POST
    else:
        form = ProviderForm() # An unbound form

    return render_to_response('provider.html', { 'form': form })

def deleteprovider(request, provider_id):
    #TODO: Needs confirmation dialog (all nodes will be deleted, not destroyed)
    #TODO: turn into DELETE request? completely RESTify?
    provider = Provider.objects.get(id=provider_id)
    provider.delete()
    return HttpResponseRedirect('/overview/')

def node(request):
    return render_to_response('node.html', {
        'provider_list': Provider.objects.all(),
    })

def newnode(request):
    if request.method == 'POST':
        provider_id = request.POST.get("provider")
        form = InstanceForm(provider_id, request.POST)
        if form.is_valid():
            inst = form.save(commit = False)
            data_from_provider = inst.provider.spawn_new_instance(form)
            if data_from_provider is not None:
                #TODO: do extra things with data_from_provider
                inst.instance_id = data_from_provider['uuid']
                inst.public_ip   = data_from_provider['public_ip']
                inst.save()
                return HttpResponseRedirect('/overview/')
    else:
        if "provider" in request.GET:
            form = InstanceForm(request.GET.get("provider"), initial={'providier': request.GET.get("provider")})
        else:
            raise Exception
            #TODO: proper HttpError
    
    return render_to_response('node_form.html', { 'form': form })

def rebootnode(request, node_id):
    node = Instance.objects.get(id=node_id)
    result = node.reboot()
    #TODO: result true or false. Show message accordingly
    return HttpResponseRedirect('/overview/')

def deletenode(request, node_id):
    #TODO: turn into DELETE request? completely RESTify?
    #TODO: needs confirmation dialog
    node = Instance.objects.get(id=node_id)
    result = node.destroy()
    #TODO: result true or false. Show message accordingly
    if result: node.delete()
    return HttpResponseRedirect('/overview/')
