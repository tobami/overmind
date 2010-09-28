from django.db import models
from overmind.provisioning.controllers import ProviderController
from provider_meta import PROVIDERS

provider_meta_keys = PROVIDERS.keys()
provider_meta_keys.sort()
PROVIDER_CHOICES = ([(key, key) for key in provider_meta_keys])

STATES = {
    0: 'Running',
    1: 'Rebooting',
    2: 'Terminated',
    3: 'Pending',
    4: 'Unknown',
}

def get_state(state):
    if state not in STATES:
        state = 4
    return STATES[state]

class Action(models.Model):
    name = models.CharField(unique=True, max_length=20)
    show = models.BooleanField()
    
    def __unicode__(self):
        return self.name

class Provider(models.Model):
    name              = models.CharField(unique=True, max_length=25)
    provider_type     = models.CharField(
        default='EC2_US_EAST', max_length=25, choices=PROVIDER_CHOICES)
    access_key        = models.CharField("Access Key", max_length=100, blank=True)
    secret_key        = models.CharField("Secret Key", max_length=100, blank=True)
    
    extra_param_name  = models.CharField(
        "Extra parameter name", max_length=30, blank=True)
    extra_param_value = models.CharField(
        "Extra parameter value", max_length=30, blank=True)
    
    actions = models.ManyToManyField(Action)
    
    def save(self, *args, **kwargs):
        # Define proper key field names
        if PROVIDERS[self.provider_type]['access_key'] is not None:
            self._meta.get_field('access_key').verbose_name = \
                PROVIDERS[self.provider_type]['access_key']
        if PROVIDERS[self.provider_type]['secret_key'] is not None:
            self._meta.get_field('secret_key').verbose_name = \
                PROVIDERS[self.provider_type]['secret_key']
        if 'extra_param' in PROVIDERS[self.provider_type].keys():
            self.extra_param_name  = PROVIDERS[self.provider_type]['extra_param'][0]
            self.extra_param_value = PROVIDERS[self.provider_type]['extra_param'][1]
        
        # Check and save new provider
        try:
            controller = ProviderController(self)
            # Check that it is a valid account
            #controller.get_nodes()#TODO: try something different
            # Save
            super(Provider, self).save(*args, **kwargs)
            
            # Add supported actions
            for action_name in PROVIDERS[self.provider_type]['supported_actions']:
                try:
                    action = Action.objects.get(name=action_name)
                except Action.DoesNotExist:
                    raise Exception, 'Unsupported action "%s" specified' % action_name
                self.actions.add(action)
        except Exception, e:
            print type(e), e
            raise e
    
    def supports(self, action):
        try:
            self.actions.get(name=action)
            return True
        except Action.DoesNotExist:
            return False
    
    def import_nodes(self):
        if not self.supports('list'): return
        p = ProviderController(self)
        nodes = p.get_nodes()
        
        # Import nodes not present in the DB
        for node in nodes:
            try:
                i = Instance.objects.get(provider=self, public_ip=node.public_ip[0])
                pass# Don't import already existing instance
            except Instance.DoesNotExist:
                print "Add instance:", node.name
                new_instance = Instance(
                    name        = node.name,
                    instance_id = node.uuid,
                    provider    = self,
                    public_ip   = node.public_ip[0],
                    state       = get_state(node.state)
                )
                new_instance.save()
        
        # Update state and delete nodes in the DB not listed by the provider
        for i in Instance.objects.filter(provider=self):
            found = False
            for node in nodes:
                print i.provider.name, i.public_ip, node.public_ip[0]
                if i.public_ip == node.public_ip[0]:
                    print "matches. State=", get_state(node.state)
                    i.state = get_state(node.state)
                    found = True
                    break
            # This instance was probably removed from the provider by another tool
            # TODO: Needs user notification
            if not found:
                print "Delete instance", i.name
                i.delete()
    
    def update(self):
        self.save()
        self.import_nodes()
    
    def get_flavors(self):
        controller = ProviderController(self)
        return controller.get_flavors()
    
    def get_images(self):
        controller = ProviderController(self)
        return controller.get_images()
    
    def get_realms(self):
        controller = ProviderController(self)
        return controller.get_realms()
    
    def spawn_new_instance(self, data):
        # first save() so extra_param gets updated
        self.save()
        controller = ProviderController(self)
        return controller.spawn_new_instance(data)
    
    def __unicode__(self):
        return self.name


class Instance(models.Model):
    STATE_CHOICES = (
        (u'Begin', u'Begin'),
        (u'Pending', u'Pending'),
        (u'Rebooting', u'Rebooting'),
        (u'Configuring', u'Configuring'),
        (u'Running', u'Running'),
        (u'Terminated', u'Terminated'),
        (u'Stopping', u'Stopping'),
        (u'Stopped', u'Stopped'),
        (u'Stranded', u'Stranded'),
        (u'Unknown', u'Unknown'),
    )
    PRODUCTION_STATE_CHOICES = (
        (u'PR', u'Production'),
        (u'ST', u'Stage'),
        (u'TE', u'Test'),
        (u'DE', u'Decommisioned'),
    )
    # Standard instance fields
    name              = models.CharField(max_length=25)
    instance_id       = models.CharField(max_length=50)
    provider          = models.ForeignKey(Provider)
    state             = models.CharField(
        default='Begin', max_length=20, choices=STATE_CHOICES
    )
    public_ip         = models.CharField(max_length=25)
    internal_ip       = models.CharField(max_length=25, blank=True)
    hostname          = models.CharField(max_length=25, blank=True)
    
    # Overmind related fields
    production_state  = models.CharField(
        default='PR', max_length=2, choices=PRODUCTION_STATE_CHOICES
    )
    
    unique_together   = ('provider', 'name', )
    unique_together   = ('provider', 'instance_id')
    unique_together   = ('provider', 'public_ip')
    
    def __unicode__(self):
        return str(self.provider) + ": " + self.name + " - " + self.public_ip + " - " + self.instance_id
    
    def reboot(self):
        '''Returns True if the reboot was successful, otherwise False'''
        controller = ProviderController(self.provider)
        return controller.reboot_node(self)
    
    def destroy(self):
        '''Returns True if the destroy was successful, otherwise False'''
        if self.provider.supports('destroy'):
            controller = ProviderController(self.provider)
            ret = controller.destroy_node(self)
            if ret:
                self.delete()
            else:
                print "Not calling Instance.delete()"
                print "controler.destroy_node() did not return True: ",
                print ret
                return False
        else:
            self.delete()
        
        return True
