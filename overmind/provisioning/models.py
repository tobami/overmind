from django.db import models
from overmind.provisioning.controllers import ProviderController

PROVIDER_META = {
    'EC2_US_EAST': {'access_key': 'AWS Access Key ID', 'secret_key': 'AWS Access Key ID'},
    'EC2_EU_WEST': {'access_key': 'AWS Access Key ID', 'secret_key': 'AWS Access Key ID'},
    'Rackspace': {'access_key': 'Rackspace User', 'secret_key': 'Rackspace Key'},
}

provider_meta_keys = PROVIDER_META.keys()
provider_meta_keys.sort()
PROVIDER_CHOICES = ([(key, key) for key in provider_meta_keys])

class Provider(models.Model):
    name           = models.CharField(unique=True, max_length=25)
    provider_type  = models.CharField(
        default='EC2_US_EAST', max_length=10, choices=PROVIDER_CHOICES
    )
    access_key     = models.CharField("Access Key", max_length=30)
    secret_key     = models.CharField("Secret Key", max_length=30, blank=True)
    #default_image  = models.CharField(blank=True, max_length=40)
    #default_realm  = models.CharField(blank=True, max_length=20)
    
    def save(self, *args, **kwargs):
        self._meta.get_field('access_key').verbose_name = \
            PROVIDER_META[self.provider_type]['access_key']
        self._meta.get_field('secret_key').verbose_name = \
            PROVIDER_META[self.provider_type]['secret_key']
        super(Provider, self).save(*args, **kwargs)
    
    def get_flavors():
        controller = ProviderController(self)
        return controller.get_realms()
    
    def get_images():
        controller = ProviderController(self)
        return controller.get_images()
    
    def get_realms():
        controller = ProviderController(self)
        return controller.get_realms()
    
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
    #TODO: What should the instance_id legth be?
    instance_id       = models.CharField(max_length=20)
    provider          = models.ForeignKey(Provider)
    state             = models.CharField(
        default='BE', max_length=2, choices=STATE_CHOICES
    )
    hostname          = models.CharField(max_length=20)
    internal_ip       = models.CharField(max_length=20)
    external_ip       = models.CharField(max_length=20)
    
    # Overmind related fields
    production_state  = models.CharField(
        default='PR', max_length=2, choices=PRODUCTION_STATE_CHOICES
    )
    unique_together   = ('instance_id', 'provider')
    
    def __unicode__(self):
        return str(self.provider) + ": " + self.name + " - " + self.external_ip
