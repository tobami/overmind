from django.db import models
from overmind.provisioning.controllers import ProviderController

PROVIDER_META = {
    #'Dummy': {'access_key': 'DAccess Key', 'secret_key': None},
    'Dummy_libcloud': {'access_key': 'Dummy Access Key', 'secret_key': None},
    'EC2_US_WEST': {'access_key': 'AWS Access Key ID', 'secret_key': 'AWS Secret Key ID'},
    'EC2_US_EAST': {'access_key': 'AWS Access Key ID', 'secret_key': 'AWS Secret Key ID'},
    'EC2_EU_WEST': {'access_key': 'AWS Access Key ID', 'secret_key': 'AWS Secret Key ID'},
    'Rackspace': {'access_key': 'Rackspace User', 'secret_key': 'Rackspace Key'},
}

provider_meta_keys = PROVIDER_META.keys()
provider_meta_keys.sort()
PROVIDER_CHOICES = ([(key, key) for key in provider_meta_keys])

class Provider(models.Model):
    name           = models.CharField(unique=True, max_length=25)
    provider_type  = models.CharField(
        default='EC2_US_EAST', max_length=20, choices=PROVIDER_CHOICES
    )
    access_key     = models.CharField("Access Key", max_length=100)
    secret_key     = models.CharField("Secret Key", max_length=100, blank=True)
    #default_image  = models.CharField(blank=True, max_length=40)
    #default_realm  = models.CharField(blank=True, max_length=20)
    
    def save(self, *args, **kwargs):
        self._meta.get_field('access_key').verbose_name = \
            PROVIDER_META[self.provider_type]['access_key']
        if PROVIDER_META[self.provider_type]['secret_key'] is not None:
            self._meta.get_field('secret_key').verbose_name = \
                PROVIDER_META[self.provider_type]['secret_key']
        # Check that it is a valid account
        controller = ProviderController(self)
        controller.get_nodes()
        super(Provider, self).save(*args, **kwargs)
    
    def import_nodes(self):
        p = ProviderController(self)
        nodes = p.get_nodes()
        for node in nodes:
            inst = Instance(
                name        = node.name,
                instance_id = node.uuid,
                provider    = self,
                public_ip   = node.public_ip[0],
            )
            inst.save()
    
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
        controller = ProviderController(self)
        return controller.spawn_new_instance(data)
    
    def __unicode__(self):
        return self.name


class Instance(models.Model):
    STATE_CHOICES = (
        (u'BE', u'Begin'),
        (u'PE', u'Pending'),
        (u'RE', u'Rebooting'),
        (u'CO', u'Configuring'),
        (u'RU', u'Running'),
        (u'TE', u'Terminated'),
        (u'ST', u'Stopping'),
        (u'SO', u'Stopped'),
        (u'SA', u'Stranded'),
    )
    PRODUCTION_STATE_CHOICES = (
        (u'PR', u'Production'),
        (u'ST', u'Stage'),
        (u'TE', u'Test'),
        (u'DE', u'Decommisioned'),
    )
    # Standard instance fields
    name              = models.CharField(unique=True, max_length=25)
    instance_id       = models.CharField(max_length=50)
    provider          = models.ForeignKey(Provider)
    state             = models.CharField(
        default='BE', max_length=2, choices=STATE_CHOICES
    )
    hostname          = models.CharField(max_length=20)
    internal_ip       = models.CharField(max_length=20)
    public_ip         = models.CharField(max_length=20)
    
    # Overmind related fields
    production_state  = models.CharField(
        default='PR', max_length=2, choices=PRODUCTION_STATE_CHOICES
    )
    unique_together   = ('instance_id', 'provider')
    
    def __unicode__(self):
        return str(self.provider) + ": " + self.name + " - " + self.public_ip + " - " + self.instance_id

    def reboot(self):
        '''Returns True if the reboot was successful, otherwise False'''
        controller = ProviderController(self.provider)
        return controller.reboot_node(self)
    
    def destroy(self):
        '''Returns True if the destroy was successful, otherwise False'''
        controller = ProviderController(self.provider)
        return controller.destroy_node(self)
