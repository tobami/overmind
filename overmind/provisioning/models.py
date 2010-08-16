from django.db import models


class Provider(models.Model):
    name                = models.CharField(unique=True, max_length=30)
    account             = models.CharField(max_length=30)
    key1                = models.CharField(max_length=40)
    key2                = models.CharField(max_length=40)
    default_image_32bit = models.CharField(max_length=40)
    default_image_64bit = models.CharField(max_length=40)

    classname = models.CharField(max_length=32, editable=False, null=True)

    def save(self):
        self.classname = self.__class__.__name__
        self.save_base()
    
    def get_concrete(self):
        return self.__getattribute__(self.classname.lower())
    
    def __unicode__(self):
        return self.name


class ProviderEC2(Provider):
    def __init__(self, *args, **kwargs):
        self._meta.get_field('key1').verbose_name = "AWS Access Key ID"
        self._meta.get_field('key2').verbose_name = "AWS Secret Access Key"
        super(Provider, self).__init__(*args, **kwargs)
    
    class Meta:
        verbose_name = "EC2 account"

class Instance(models.Model):
    STATE_CHOICES = (
        (u'BI', u'Bidding'),
        (u'PE', u'Pending'),
        (u'BO', u'Booting'),
        (u'CO', u'Configuring'),
        (u'OP', u'Operational'),
        (u'SD', u'Shutting-Down'),
        (u'DE', u'Decommissioning'),
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
    name              = models.CharField(unique=True, max_length=20)
    instance_id       = models.CharField(max_length=20)
    owner             = models.CharField(max_length=20)
    state             = models.CharField(max_length=2, choices=STATE_CHOICES)
    production_state  = models.CharField(
        max_length=2, choices=PRODUCTION_STATE_CHOICES
    )
    
    classname = models.CharField(max_length=32, editable=False, null=True)

    def save(self):
        self.classname = self.__class__.__name__
        self.save_base()
    
    def get_concrete(self):
        return self.__getattribute__(self.classname.lower())
    
    def __unicode__(self):
        return str(self.provider) + ": " + self.name


class InstanceEC2(Instance):
    provider          = models.ForeignKey("ProviderEC2")
    reservation_id    = models.CharField(max_length=20)
    ami               = models.CharField(max_length=20)
    aki               = models.CharField(max_length=20)
    ari               = models.CharField(max_length=20)
    public_dns        = models.CharField(max_length=20)
    private_dns       = models.CharField(max_length=20)
    launch_key        = models.CharField(max_length=20)
    security_group    = models.CharField(max_length=20)
    machine_type      = models.CharField(max_length=20)
    local_launch_time = models.DateTimeField(auto_now_add=True)
    region            = models.CharField(max_length=20)
    availability_zone = models.CharField(max_length=20)
    hostname          = models.CharField(max_length=20)
    internal_ip       = models.CharField(max_length=20)
    external_ip       = models.CharField(max_length=20)
    
    class Meta:
        verbose_name    = "EC2 Instance"
