from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext
from libcloud.types import InvalidCredsException

from provisioning.models import Action, Provider, Node, get_state, Image
from provisioning.forms import ProviderForm, NodeForm, AddImageForm, ProfileEditForm
from provisioning.forms import UserCreationFormExtended, UserEditForm
from provisioning.provider_meta import PROVIDERS
import logging
import simplejson as json

@login_required
def overview(request):
    provider_list = Provider.objects.all()
    nodes = []
    #TODO: Optimize for hundreds of nodes
    for n in Node.objects.exclude(environment='Decommissioned'):
        datatable = "<table>"
        fields = [
            ['Created by', n.creator],
            ['Created at', n.timestamp.strftime('%Y-%m-%d %H:%M:%S')],
            ['Node ID', n.node_id],
            ['OS image', n.image],
            ['Location', n.location],
            ['Size', n.size],
        ]
        if n.size and n.size.price:
            fields.append(['Price', n.size.price + ' $/hour'])
        fields.append(['-----', '--'])
        if n.private_ip:
            fields.append(['private_ip', n.private_ip])
        
        for key, val in n.extra_data().items():
            fields.append([key, val])
        
        for field in fields:
            datatable += "<tr><td>" + field[0] + ":</td><td>" + str(field[1])
            datatable += "</td></tr></td>"
        datatable += "</table>"
        
        actions_list = []
        if n.state != 'Terminated' and \
            request.user.has_perm('provisioning.change_node'):
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
    
    variables = RequestContext(request, {
        'nodes': nodes,
        'provider_list': provider_list,
    })
    return render_to_response('overview.html', variables)

@permission_required('provisioning.add_provider')
def provider(request):
    providers = []
    provider_types = PROVIDERS.keys()
    provider_types.sort()
    for p in provider_types:
        providers.append([p, PROVIDERS[p]['display_name']])
    
    variables = RequestContext(request, {
        'provider_types': providers, 'user': request.user,
    })
    return render_to_response('provider.html', variables)

@permission_required('provisioning.add_provider')
def newprovider(request):
    error = None
    if request.method == 'POST':
        error, form, prov = save_new_provider(request.POST)
        if error is None:
            return HttpResponse('<p>success</p>')
    else:
        form = ProviderForm(request.GET.get("provider_type"))
    if error == 'form':
        error = None
    return render_to_response('provider_form.html',
        { 'form': form, 'error': error })

def save_new_provider(data):
    form = ProviderForm(data.get('provider_type'), data)
    return save_provider(form)

def update_provider(data, provider):
    form = ProviderForm(data.get('provider_type'), data, instance=provider)
    return save_provider(form)

def save_provider(form):
    error = None
    if form.is_valid():
        provider = None
        try:
            provider = form.save()
            #TODO: defer importing to a work queue
            provider.import_images()
            provider.import_locations()
            provider.import_sizes()
            provider.import_nodes()
        except InvalidCredsException:
            # Delete provider if InvalidCreds is raised (by EC2)
            # after it has been saved
            if provider:
                provider.delete()
            # Return form with InvalidCreds error
            error = 'Invalid account credentials'
        except Exception, e:#Unexpected error. Log
            error = e
            logging.error(error)
        else:
            logging.info('Provider saved %s' % provider.name)
            return None, form, provider
    else:
        error = 'form'
    return error, form, None

@login_required
def updateproviders(request):
    providers = Provider.objects.all()
    for provider in providers:
        if provider.supports('list'):
            provider.update()
    return HttpResponseRedirect('/overview/')

@permission_required('provisioning.delete_provider')
def deleteprovider(request, provider_id):
    provider = Provider.objects.get(id=provider_id)
    provider.delete()
    return HttpResponseRedirect('/overview/')

@permission_required('provisioning.add_node')
def node(request):
    '''Displays a provider selection list to call the node creation form'''
    variables = RequestContext(request, {
        'provider_list': Action.objects.get(name='create').provider_set.all(),
    })
    return render_to_response('node.html', variables)

@permission_required('provisioning.add_node')
def addimage(request):
    error = None
    if request.method == 'POST':
        form = AddImageForm(request.POST.get("provider"), request.POST)
        if form.is_valid():
            img = form.cleaned_data['image']
            img.favorite = True
            img.save()
            favimage = {'name': img.name, 'image_id': img.image_id, 'id': img.id}
            return HttpResponse(json.dumps(favimage))
    else:
        form = AddImageForm(request.GET.get("provider"))
    return render_to_response('image_form.html', { 'form': form, 'error': error })

@permission_required('provisioning.add_node')
def removeimage(request, image_id):
    if request.method == 'POST':
        try:
            image = Image.objects.get(id=image_id)
            image.favorite = False
            image.save()
            return HttpResponse("<p>SUCCESS</p>" % image)
        except Image.DoesNotExist:
            error = "<p>Image id %s does not exist</p>" % image_id
    else:
        error = "<p>Only POST Allowed</p>"
    return HttpResponse(error)

@permission_required('provisioning.add_node')
def newnode(request):
    error = None
    favcount = 0
    if request.method == 'POST':
        error, form, node = save_new_node(request.POST, request.user)
        if error is None:
            return HttpResponse('<p>success</p>')
    else:
        form = NodeForm(request.GET.get("provider"))
        favcount = Image.objects.filter(
            provider=request.GET.get("provider"),
            favorite=True
        ).count()
    if error == 'form':
        error = None
    return render_to_response('node_form.html',
        { 'form': form, 'favcount': favcount, 'error': error })

def save_new_node(data, user):
    provider_id = data.get("provider")
    if not provider_id:
        return 'Incorrect provider id', None, None
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
                node = Node.objects.get(
                    provider=provider, name=form.cleaned_data['name']
                )
                error = 'A node with that name already exists'
            except Node.DoesNotExist:
                error, data_from_provider = provider.create_node(form)
                if error is None:
                    node = form.save(commit = False)
                    node.node_id    = data_from_provider['node_id']
                    node.public_ip  = data_from_provider['public_ip']
                    node.private_ip = data_from_provider.get('private_ip', '')
                    node.state      = get_state(data_from_provider['state'])
                    node.creator    = user.username
                    node.save_extra_data(data_from_provider.get('extra', ''))
                    try:
                        node.save()
                        logging.info('New node created %s' % node)
                        # Mark image as recently used by saving it
                        if node.image is not None:
                            node.image.save()
                        return None, form, node
                    except Exception, e:
                        error = e
                        logging.error('Could not create node: %s' % e)
        else:
            error = 'form'
    return error, form, None

@permission_required('provisioning.change_node')
def rebootnode(request, node_id):
    node = Node.objects.get(id=node_id)
    result = node.reboot()
    return HttpResponseRedirect('/overview/')

@permission_required('provisioning.delete_node')
def destroynode(request, node_id):
    node = Node.objects.get(id=node_id)
    result = node.destroy()
    return HttpResponseRedirect('/overview/')

@login_required
def settings(request):
    variables = RequestContext(request, {
        'user_list': User.objects.all(),
    })
    return render_to_response('settings.html', variables)

def count_admin_users():
    '''Returns the number of users belonging to the Admin group
 or having superuser rights'''
    g = get_object_or_404(Group, name='Admin')
    admin_users_count = len(g.user_set.all())
    admin_users_count += len(User.objects.filter(is_superuser=True))
    return admin_users_count

@permission_required('auth.add_user')
def adduser(request):
    if request.method == 'POST':
        form = UserCreationFormExtended(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('<p>success</p>')
    else:
        form = UserCreationFormExtended()
    
    return render_to_response("registration/register.html",
        {'form': form, 'editing': False}
    )

@login_required
def edituser(request, id):
    edit_user = get_object_or_404(User, id=id)
    if not request.user.has_perm('auth.change_user') and request.user.id != int(id):
        # If user doesn't have auth permissions and he/she is not editting
        # his/her own profile don't allow the operation
        return HttpResponse("<p>Your don't have permissions to edit users</p>")
    
    if request.method == 'POST':
        if request.user.has_perm('auth.change_user'):
            admin   = Group.objects.get(name='Admin')
            oldrole = admin if admin in edit_user.groups.all() else False
            newrole = Group.objects.get(id=request.POST.get('group'))
            if oldrole is admin and newrole != admin and count_admin_users() <= 1:
                errormsg = "<p>Not allowed: you cannot remove admin rights"
                errormsg += " from the only admin user</p>"
                return HttpResponse(errormsg)
            form = UserEditForm(request.POST, instance=edit_user)
        else:
            form = ProfileEditForm(request.POST, instance=edit_user)
        
        if form.is_valid():
            form.save()
            return HttpResponse('<p>success</p>')
    else:
        if request.user.has_perm('auth.change_user'):
            form = UserEditForm(instance=edit_user)
        else:
            form = ProfileEditForm(instance=edit_user)
    
    variables = RequestContext(request, {
        'form': form, 'editing': True, 'edit_user': edit_user
    })
    return render_to_response("registration/register.html", variables)

@permission_required('auth.delete_user')
def deleteuser(request, id):
    user = get_object_or_404(User, id=id)
    if user.has_perm('auth.add_user') and count_admin_users() <= 1:
        return HttpResponse(
            "<p>Not allowed: You cannot delete the only admin user</p>")
    user.delete()
    return HttpResponse('<p>success</p>')
