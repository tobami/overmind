from django.db import models, transaction
from provisioning.controllers import ProviderController
from provisioning.provider_meta import PROVIDERS
import logging
import simplejson as json

provider_meta_keys = PROVIDERS.keys()
provider_meta_keys.sort()
PROVIDER_CHOICES = ([(key, key) for key in provider_meta_keys])

# libcloud states mapping
STATES = {
    0: 'Running',
    1: 'Rebooting',
    2: 'Terminated',
    3: 'Pending',
    4: 'Unknown',
}

def get_state(state):
    if state not in STATES: state = 4
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
    conn    = None
    
    class Meta:
        unique_together = ('provider_type', 'access_key')
    
    def save(self, *args, **kwargs):
        # Define proper key field names
        if PROVIDERS[self.provider_type]['access_key'] is not None:
            self._meta.get_field('access_key').verbose_name = \
                PROVIDERS[self.provider_type]['access_key']
            self._meta.get_field('access_key').blank = False
        if PROVIDERS[self.provider_type]['secret_key'] is not None:
            self._meta.get_field('secret_key').verbose_name = \
                PROVIDERS[self.provider_type]['secret_key']
            self._meta.get_field('access_key').blank = False
        
        # Read optional extra_param
        if 'extra_param' in PROVIDERS[self.provider_type].keys():
            self.extra_param_name  = PROVIDERS[self.provider_type]['extra_param'][0]
            self.extra_param_value = PROVIDERS[self.provider_type]['extra_param'][1]
        
        # Check connection and save new provider
        self.create_connection()
        # If connection was succesful save provider
        super(Provider, self).save(*args, **kwargs)
        logging.debug('Provider "%s" saved' % self.name)

        # Add supported actions
        for action_name in PROVIDERS[self.provider_type]['supported_actions']:
            try:
                action = Action.objects.get(name=action_name)
            except Action.DoesNotExist:
                raise Exception, 'Unsupported action "%s" specified' % action_name
            self.actions.add(action)
    
    def supports(self, action):
        try:
            self.actions.get(name=action)
            return True
        except Action.DoesNotExist:
            return False
    
    def create_connection(self):
        if self.conn is None:
            self.conn = ProviderController(self)
    
    def import_nodes(self):
        if not self.supports('list'): return
        self.create_connection()
        nodes = self.conn.get_nodes()
        # Import nodes not present in the DB
        for node in nodes:
            try:
                n = Node.objects.get(provider=self, uuid=node.uuid)
            except Node.DoesNotExist:
                logging.info("import_nodes(): adding %s ..." % node)
                n = Node(
                    name      = node.name,
                    uuid      = node.uuid,
                    provider  = self,
                    creator   = 'imported by Overmind',
                )
            try:
                n.image = Image.objects.get(
                    image_id=node.extra.get('imageId'), provider=self)
            except Image.DoesNotExist:
                n.image = None
            # Import/Update node info
            n.public_ip = node.public_ip[0]
            n.state = get_state(node.state),
            n.save_extra_data(node.extra)
            n.save()
            logging.debug("import_nodes(): succesfully saved %s" % node.name)
        
        # Delete nodes in the DB not listed by the provider
        for n in Node.objects.filter(provider=self
            ).exclude(environment='Decommissioned'):
            found = False
            for node in nodes:
                if n.uuid == node.uuid:
                    found = True
                    break
            # This node was probably removed from the provider by another tool
            # TODO: Needs user notification
            if not found:
                n.state = 'Terminated'
                logging.info("import_nodes(): Delete node %s" % n)
                n.decommission()
        logging.debug("Finished synching")
    
    @transaction.commit_on_success()
    def import_images(self):
        '''Get all images from this provider and store them in the DB
        The transaction.commit_on_success decorator is needed because
        some providers have thousands of images, which take a long time
        to save to the DB as separated transactions
        '''
        self.create_connection()
        for image in self.conn.get_images():
            try:
                # Update image if it exists
                img = Image.objects.get(image_id=image.id, provider=self)
                img.name = image.name
            except Image.DoesNotExist:
                # Create new image if it didn't exist
                img = Image(
                    image_id = image.id,
                    name = image.name,
                    provider = self,
                )
            img.save()
            logging.debug(
                "Added new image '%s' for provider %s" % (img.name, self))
        logging.debug("Imported all images for provider %s" % self)
    
    def update(self):
        logging.debug('Updating provider "%s"...' % self.name)
        self.save()
        self.import_nodes()
    
    def get_flavors(self):
        self.create_connection()
        return self.conn.get_flavors()
    
    def get_images(self):
        return self.image_set.all()
    
    def get_realms(self):
        self.create_connection()
        return self.conn.get_realms()
    
    def create_node(self, data):
        self.create_connection()
        return self.conn.create_node(data)
    
    def reboot_node(self, node):
        self.create_connection()
        return self.conn.reboot_node(node)
    
    def destroy_node(self, node):
        self.create_connection()
        return self.conn.destroy_node(node)
    
    def __unicode__(self):
        return self.name


class Image(models.Model):
    '''OS image model'''
    image_id = models.CharField(max_length=20)
    name     = models.CharField(max_length=30)
    provider = models.ForeignKey(Provider)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        unique_together  = ('provider', 'image_id')


class Node(models.Model):
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
    ENVIRONMENT_CHOICES = (
        (u'Production', u'Production'),
        (u'Stage', u'Stage'),
        (u'Test', u'Test'),
        (u'Decommissioned', u'Decommissioned'),
    )
    # Standard node fields
    name        = models.CharField(max_length=25)
    uuid        = models.CharField(max_length=50)
    provider    = models.ForeignKey(Provider)
    image       = models.ForeignKey(Image, null=True, blank=True)
    
    state       = models.CharField(
        default='Begin', max_length=20, choices=STATE_CHOICES
    )
    public_ip   = models.CharField(max_length=25)
    internal_ip = models.CharField(max_length=25, blank=True)
    hostname    = models.CharField(max_length=25, blank=True)
    _extra_data = models.TextField(blank=True)
    
    # Overmind related fields
    environment = models.CharField(
        default='Production', max_length=2, choices=ENVIRONMENT_CHOICES
    )
    creator     = models.CharField(max_length=25)
    timestamp   = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together  = (('provider', 'name'), ('provider', 'uuid'))
    
    def __unicode__(self):
        return "<" + str(self.provider) + ": " + self.name + " - " + self.public_ip + " - " + self.uuid + ">"
    
    def save_extra_data(self, data):
        self._extra_data = json.dumps(data)
    
    def extra_data(self):
        if self._extra_data == '':
            return {}
        return json.loads(self._extra_data)
    
    def reboot(self):
        '''Returns True if the reboot was successful, otherwise False'''
        return self.provider.reboot_node(self)
    
    def destroy(self):
        '''Returns True if the destroy was successful, otherwise False'''
        if self.provider.supports('destroy'):
            ret = self.provider.destroy_node(self)
            if ret:
                logging.info('Destroyed %s' % self)
            else:
                logging.error("controler.destroy_node() did not return True: %s.\nnot calling Node.delete()" % ret)
                return False
        self.state = 'Terminated'
        self.decommission()
        return True
    
    def decommission(self):
        # Rename node to free the name for future use
        counter = 1
        newname = "DECOM" + str(counter) + "-" + self.name
        while(
            Node.objects.filter(
                provider=self.provider,name=newname
            ).exclude(
                id=self.id
            )):
            counter += 1
            newname = "DECOM" + str(counter) + "-" + self.name
        self.name = newname
        # Mark decommissioned and save
        self.environment = 'Decommissioned'
        self.save()
