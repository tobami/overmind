from django.db import models

PROVIDER_CHOICES = (
    (u'EC2', u'EC2'),
    (u'Rackspace', u'Rackspace'),
)

PROVIDER_META = {
    'EC2': {'access_key': 'AWS Access Key ID', 'secret_key': 'AWS Access Key ID'},
    'Rackspace': {'access_key': 'Rackspace User', 'secret_key': 'Rackspace Key'},
}

class Provider(models.Model):
    name          = models.CharField(unique=True, max_length=30)
    access_key    = models.CharField("Access Key", max_length=30)
    secret_key    = models.CharField("Secret Key", max_length=30, blank=True)
    default_image = models.CharField(max_length=40)
    provider_type = models.CharField(
        default='EC2', max_length=10, choices=PROVIDER_CHOICES
    )
    
    def save(self, *args, **kwargs):
        self._meta.get_field('access_key').verbose_name = \
            PROVIDER_META[self.provider_type]['access_key']
        self._meta.get_field('secret_key').verbose_name = \
            PROVIDER_META[self.provider_type]['secret_key']
        super(Provider, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return self.provider_type + " " + self.name


class Instance(models.Model):
    STATE_CHOICES = (
        (u'BE', u'Begin'),
        (u'PE', u'Pending'),#from libcloud/deltacloud
        (u'RE', u'Rebooting'),#from libcloud/deltacloud
        (u'CO', u'Configuring'),
        (u'RU', u'Running'),#from libcloud/deltacloud
        (u'TE', u'Terminated'),#from libcloud
        (u'ST', u'Stopping'),
        (u'SO', u'Stopped'),#standard for clouds
        (u'SA', u'Stranded'),
    )
    PRODUCTION_STATE_CHOICES = (
        (u'PR', u'Production'),
        (u'ST', u'Stage'),
        (u'TE', u'Test'),
        (u'DE', u'Decommisioned'),
    )
    # Standard instance fields
    instance_id       = models.CharField(max_length=20)
    name              = models.CharField(unique=True, max_length=20)
    provider          = models.ForeignKey(Provider)
    owner             = models.CharField(max_length=20)#needed?
    state             = models.CharField(
        default='BE', max_length=2, choices=STATE_CHOICES
    )
    realm             = models.CharField(max_length=20)#region for EC2
    machine_type      = models.CharField(max_length=20)#needed?
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
