from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from overmind.provisioning.models import Provider, Instance
from overmind.provisioning.forms import ProviderForm, InstanceForm
from overmind.provisioning.provider_meta import PROVIDERS
from libcloud.types import InvalidCredsException


def overview(request):
    provider_list = Provider.objects.all()
    instance_list = Instance.objects.all()
    return render_to_response('overview.html', {
        'instance_list': instance_list,
        'provider_list': provider_list,
    })

def provider(request):
    providers = []
    provider_types = PROVIDERS.keys()
    provider_types.sort()
    for p in provider_types:
        providers.append([p, PROVIDERS[p]['display_name']])
    
    return render_to_response('provider.html', {
        'provider_types': providers,
    })

def newprovider(request):
    if request.method == 'POST':
        provider_type = request.POST.get("provider_type")
        form = ProviderForm(provider_type, request.POST)
        if form.is_valid():
            try:
                newprovider = form.save()
            except TypeError:
                return render_to_response('provider_form.html', {
                    'form': form,
                    'error': 'Invalid account credentials',
                })
            except InvalidCredsException:
                return render_to_response('provider_form.html', {
                    'form': form,
                    'error': 'Invalid account credentials (exception)',
                })
            except Exception, e:
                # Unexpected error
                return render_to_response('provider_form.html', {
                    'form': form,
                    'error': e,
                })
            #TODO: defer importing to a work queue
            newprovider.import_nodes()
            
            return HttpResponse('<p>success</p>')
    else:
        if "provider_type" in request.GET:
            form = ProviderForm(request.GET.get("provider_type"))
        else:
            raise Exception
            #TODO: proper HttpError
    
    return render_to_response('provider_form.html', { 'form': form })

def updateproviders(request):
    providers = Provider.objects.all()
    for provider in providers:
        if provider.supports('list'):
            provider.update()
    return HttpResponseRedirect('/overview/')

def deleteprovider(request, provider_id):
    #TODO: turn into DELETE request? RESTify?
    provider = Provider.objects.get(id=provider_id)
    provider.delete()
    return HttpResponseRedirect('/overview/')

def node(request):
    return render_to_response('node.html', {
        'provider_list': Provider.objects.all(),
    })

def newnode(request):
    error = None
    if request.method == 'POST':
        provider_id = request.POST.get("provider")
        form = InstanceForm(provider_id, request.POST)
        if form.is_valid():
            provider = Provider.objects.get(id=provider_id)
            try:
                i = Instance.objects.get(
                    provider=provider, name=form.cleaned_data['name']
                )
                error = 'A node with that name already exists'
            except Instance.DoesNotExist:
                data_from_provider = provider.spawn_new_instance(form)
                if data_from_provider is None:
                    error = 'Could not create Node'
                else:
                    inst = form.save(commit = False)
                    inst.instance_id = data_from_provider['uuid']
                    inst.public_ip   = data_from_provider['public_ip']
                    inst.state   = data_from_provider['state']
                    inst.save()
                    return HttpResponse('<p>success</p>')

    else:
        form = InstanceForm(request.GET.get("provider"))
    
    return render_to_response('node_form.html', { 'form': form, 'error': error })

def rebootnode(request, node_id):
    node = Instance.objects.get(id=node_id)
    result = node.reboot()
    #TODO: result true or false. Show message accordingly
    return HttpResponseRedirect('/overview/')

def deletenode(request, node_id):
    #TODO: turn into DELETE request? completely RESTify?
    node = Instance.objects.get(id=node_id)
    result = node.delete()
    return HttpResponseRedirect('/overview/')
