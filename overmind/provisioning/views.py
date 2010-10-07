from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from overmind.provisioning.models import Action, Provider, Node, get_state
from overmind.provisioning.forms import ProviderForm, NodeForm
from overmind.provisioning.provider_meta import PROVIDERS
from libcloud.types import InvalidCredsException
import logging

def overview(request):
    provider_list = Provider.objects.all()
    nodes = []
    #TODO: Optimize for hundreds of nodes
    for n in Node.objects.exclude(production_state='DE'):
        datatable = "<table>"
        fields = [
            ['uuid', n.uuid],
            ['timestamp', n.timestamp.strftime('%Y-%m-%d %H:%M:%S')],
        ]
        for k,v in n.get_extra_data().items():
            fields.append([k,v])
        
        for field in fields:
            datatable += "<tr><td>" + field[0] + ":</td><td>" + str(field[1]) + "</td></tr></td>"
        datatable += "</table>"
        
        actions_list = []
        if n.state != 'Terminated':
            actions = n.provider.actions.filter(show=True)
            
            if actions.filter(name='reboot'):
                actions_list.append({
                    'action': 'reboot',
                    'label': 'reboot',
                    'confirmation': 'Are you sure you want to reboot the node "%s"'\
                    % n.name,
                })
            
            if actions.filter(name='destroy'):
                actions_list.append({
                    'action': 'destroy',
                    'label': 'destroy',
                    'confirmation': 'This action will completely destroy the node %s'\
                    % n.name,
                })
            else:
                actions_list.append({
                    'action': 'destroy',
                    'label': 'delete',
                    'confirmation': 'This action will remove the node %s with IP %s' % (n.name, n.public_ip),
                })
        
        nodes.append({ 'node': n, 'data': datatable, 'actions': actions_list })
    
    return render_to_response('overview.html', {
        'nodes': nodes,
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
    error = None
    if request.method == 'POST':
        error, form, provider = save_new_provider(request.POST)
        if error is None: return HttpResponse('<p>success</p>')
    else:
        form = ProviderForm(request.GET.get("provider_type"))
    if error == 'form': error = None
    return render_to_response('provider_form.html', { 'form': form, 'error': error })

def save_new_provider(data):
    error = None
    form = None
    form = ProviderForm(data.get('provider_type'), data)
    if form.is_valid():
        newprovider = None
        try:
            newprovider = form.save()
            #TODO: defer importing to a work queue
            newprovider.import_nodes()
        except InvalidCredsException:
            # Delete provider if InvalidCreds is raised (by EC2)
            # after it has been saved
            if newprovider: newprovider.delete()
            # Return form with InvalidCreds error
            error = 'Invalid account credentials'
        except Exception, e:
            error = e
            logging.error(error)
        else:
            logging.info('New provider created %s' % newprovider.name)
            return None, form, newprovider
    else:
        error = 'form'
    return error, form, None

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
    '''Displays a provider selection list to call the appropiate node creation form'''
    return render_to_response('node.html', {
        'provider_list': Action.objects.get(name='create').provider_set.all(),
    })

def newnode(request):
    error = None
    if request.method == 'POST':
        error, form, node = save_new_node(request.POST)
        if error is None: return HttpResponse('<p>success</p>')
    else:
        form = NodeForm(request.GET.get("provider"))
    if error == 'form': error = None
    return render_to_response('node_form.html', { 'form': form, 'error': error })

def save_new_node(data):
    provider_id = data.get("provider")
    if not provider_id: return 'Incorrect provider id', None, None
    error = None
    form = None
    try:
        provider = Provider.objects.get(id=provider_id)
        form = NodeForm(provider_id, data)
    except Provider.DoesNotExist:
        error = 'Incorrect provider id'
    
    if form is not None:
        if form.is_valid():
            try:
                n = Node.objects.get(
                    provider=provider, name=form.cleaned_data['name']
                )
                error = 'A node with that name already exists'
            except Node.DoesNotExist:
                error, data_from_provider = provider.create_node(form)
                if error is None:
                    node = form.save(commit = False)
                    node.uuid      = data_from_provider['uuid']
                    node.public_ip = data_from_provider['public_ip']
                    node.state     = get_state(data_from_provider['state'])
                    node.save_extra_data(data_from_provider.get('extra', ''))
                    node.save()
                    logging.info('New node created %s' % node)
                    return None, form, node
        else:
            error = 'form'
    return error, form, None

def rebootnode(request, node_id):
    node = Node.objects.get(id=node_id)
    result = node.reboot()
    #TODO: result true or false. Show message accordingly
    return HttpResponseRedirect('/overview/')

def destroynode(request, node_id):
    node = Node.objects.get(id=node_id)
    result = node.destroy()
    return HttpResponseRedirect('/overview/')
