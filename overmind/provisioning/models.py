from django.db import models, transaction
from provisioning.controllers import ProviderController
from provisioning.provider_meta import PROVIDERS
import logging, datetime
import simplejson as json
from IPy import IP

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
    ready   = models.BooleanField(default=False)
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
    
    @transaction.commit_on_success()
    def import_nodes(self):
        '''Sync nodes present at a provider with Overmind's DB'''
        if not self.supports('list'): return
        self.create_connection()
        nodes = self.conn.get_nodes()
        # Import nodes not present in the DB
        for node in nodes:
            try:
                n = Node.objects.get(provider=self, node_id=str(node.id))
            except Node.DoesNotExist:
                # Create a new Node
                logging.info("import_nodes(): adding %s ..." % node)
                n = Node(
                    name       = node.name,
                    node_id    = str(node.id),
                    provider   = self,
                    created_by = 'imported by Overmind',
                )
                try:
                    n.image = Image.objects.get(
                        image_id=node.extra.get('imageId'), provider=self)
                except Image.DoesNotExist:
                    n.image = None
                locs = Location.objects.filter(provider=self)
                if len(locs) == 1:
                    n.location = locs[0]
                else:
                    n.location = None
                try:
                    size_id = node.extra.get('instancetype') or\
                        node.extra.get('flavorId')
                    n.size = Size.objects.get(size_id=size_id, provider=self)
                except Size.DoesNotExist:
                    n.size = None
            n.save()
            # Import/Update node info
            for i in range(0, len(node.public_ips)):
                n.create_ip(ip=node.public_ips[i], position=i, is_public=True)
            if len(node.private_ips):
                for i in range(0, len(node.private_ips)):
                    n.create_ip(ip=node.private_ips[i], position=i, is_public=False)
            n.state = get_state(node.state)
            n.save_extra_data(node.extra)
            n.save()
            logging.debug("import_nodes(): succesfully saved %s" % node.name)
        
        # Delete nodes in the DB not listed by the provider
        for n in Node.objects.filter(provider=self
            ).exclude(environment='Decommissioned'):
            found = False
            for node in nodes:
                if n.node_id == str(node.id):
                    found = True
                    break
            # This node was probably removed from the provider by another tool
            # TODO: Needs user notification
            if not found:
                logging.info("import_nodes(): Delete node %s" % n)
                n.decommission()
        logging.debug("Finished synching nodes")
    
    @transaction.commit_on_success()
    def import_images(self):
        '''Get all images from this provider and store them in the DB
        The transaction.commit_on_success decorator is needed because
        some providers have thousands of images, which take a long time
        to save to the DB as separated transactions
        '''
        if not self.supports('images'): return
        self.create_connection()
        for image in self.conn.get_images():
            try:
                # Update image if it exists
                img = Image.objects.get(image_id=str(image.id), provider=self)
            except Image.DoesNotExist:
                # Create new image if it didn't exist
                img = Image(
                    image_id = str(image.id),
                    provider = self,
                )
            img.name = image.name
            img.save()
            logging.debug(
                "Added new image '%s' for provider %s" % (img.name, self))
        logging.info("Imported all images for provider %s" % self)
    
    @transaction.commit_on_success()
    def import_locations(self):
        '''Get all locations from this provider and store them in the DB'''
        if not self.supports('locations'): return
        self.create_connection()
        for location in self.conn.get_locations():
            try:
                # Update location if it exists
                loc = Location.objects.get(location_id=str(location.id), provider=self)
            except Location.DoesNotExist:
                # Create new location if it didn't exist
                loc = Location(
                    location_id = location.id,
                    provider = self,
                )
            loc.name    = location.name
            loc.country = location.country
            loc.save()
            logging.debug(
                "Added new location '%s' for provider %s" % (loc.name, self))
        logging.info("Imported all locations for provider %s" % self)
    
    @transaction.commit_on_success()
    def import_sizes(self):
        '''Get all sizes from this provider and store them in the DB'''
        if not self.supports('sizes'): return
        self.create_connection()
        sizes = self.conn.get_sizes()
        
        # Go through all sizes returned by the provider
        for size in sizes:
            try:
                # Read size
                s = Size.objects.get(size_id=str(size.id), provider=self)
            except Size.DoesNotExist:
                # Create new size if it didn't exist
                s = Size(
                    size_id = str(size.id),
                    provider = self,
                )
            # Save/update size info
            s.name      = size.name
            s.ram       = size.ram
            s.disk      = size.disk or ""
            s.bandwidth = size.bandwidth or ""
            s.price     = size.price or ""
            s.save()
            logging.debug("Saved size '%s' for provider %s" % (s.name, self))
        
        # Delete sizes in the DB not listed by the provider
        for s in self.get_sizes():
            found = False
            for size in sizes:
                if s.size_id == str(size.id):
                    found = True
                    break
            # This size is probably not longer offered by the provider
            if not found:
                logging.debug("Deleted size %s" % s)
                s.delete()
        logging.debug("Finished synching sizes")
    
    def update(self):
        logging.debug('Updating provider "%s"...' % self.name)
        self.save()
        self.import_nodes()
    
    def check_credentials(self):
        if not self.supports('list'): return
        self.create_connection()
        self.conn.get_nodes()
        return True
    
    def get_sizes(self):
        return self.size_set.all()
    
    def get_images(self):
        return self.image_set.all()
    
    def get_fav_images(self):
        return self.image_set.filter(favorite=True).order_by('-last_used')
    
    def get_locations(self):
        return self.location_set.all()
    
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
    image_id  = models.CharField(max_length=20)
    name      = models.CharField(max_length=30)
    provider  = models.ForeignKey(Provider)
    favorite  = models.BooleanField(default=False)
    last_used = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        unique_together  = ('provider', 'image_id')


class Location(models.Model):
    '''Location model'''
    location_id = models.CharField(max_length=20)
    name        = models.CharField(max_length=20)
    country     = models.CharField(max_length=20)
    provider    = models.ForeignKey(Provider)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        unique_together  = ('provider', 'location_id')


class Size(models.Model):
    '''Location model'''
    size_id   = models.CharField(max_length=20)
    name      = models.CharField(max_length=20)
    ram       = models.CharField(max_length=20)
    disk      = models.CharField(max_length=20)
    bandwidth = models.CharField(max_length=20, blank=True)
    price     = models.CharField(max_length=20, blank=True)
    provider  = models.ForeignKey(Provider)
    
    def __unicode__(self):
        return "%s (%sMB)" % (self.name, self.ram)
    
    class Meta:
        unique_together  = ('provider', 'size_id')


class NodeIP(models.Model):
    INET_FAMILIES = (
        ('inet4', 4),
        ('inet6', 6),
    )
    node = models.ForeignKey('Node', related_name='ips')
    address = models.CharField(max_length=50)   # For IPv6 support, not fully supported in django < 1.3.2 (IIRC)
    is_public = models.BooleanField(default=True)
    version = models.IntegerField(choices=INET_FAMILIES, default=4)
    position = models.IntegerField()

    def __unicode__(self):
        return "%s" % (self.address)

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
    node_id     = models.CharField(max_length=50)
    provider    = models.ForeignKey(Provider)
    image       = models.ForeignKey(Image, null=True, blank=True)
    location    = models.ForeignKey(Location, null=True, blank=True)
    size        = models.ForeignKey(Size, null=True, blank=True)
    
    state       = models.CharField(
        default='Begin', max_length=20, choices=STATE_CHOICES
    )
    hostname    = models.CharField(max_length=25, blank=True)
    _extra_data = models.TextField(blank=True)
    
    # Overmind related fields
    environment = models.CharField(
        default='Production', max_length=2, choices=ENVIRONMENT_CHOICES
    )
    created_by   = models.CharField(max_length=25)
    destroyed_by = models.CharField(max_length=25, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    destroyed_at = models.DateTimeField(null=True)

    @property
    def public_ips(self):
        return self.ips.filter(is_public=True).all()


    @property
    def private_ips(self):
        return self.ips.filter(is_public=False).all()

    # Backward compatibility properties
    @property
    def public_ip(self):
        public_ips = self.ips.filter(is_public=True).filter(version=4)
        if len(public_ips):
            return public_ips[0].address
        return ''

    @property
    def private_ip(self):
        private_ips = self.ips.filter(is_public=False)
        if len(private_ips):
            return private_ips[0].address
        return ''

    # helper for related ips creation
    def create_ip(self, ip, position, is_public):
        ipaddr = IP(ip)
        return NodeIP.objects.create(
            address=ipaddr.strFullsize(), position=position, version=ipaddr.version(),
            is_public=is_public, node=self
        )

    class Meta:
        unique_together  = (('provider', 'name'), ('provider', 'node_id'))
    
    def __unicode__(self):
        return "<" + str(self.provider) + ": " + self.name + " - " + self.public_ip + " - " + str(self.node_id) + ">"
    
    def save_extra_data(self, data):
        self._extra_data = json.dumps(data)
    
    def extra_data(self):
        if self._extra_data == '':
            return {}
        return json.loads(self._extra_data)
    
    def reboot(self):
        '''Returns True if the reboot was successful, otherwise False'''
        if not self.provider.supports('reboot'):
            return True
        
        ret = self.provider.reboot_node(self)
        if ret:
            logging.debug('Rebooted %s' % self)
        else:
            logging.warn('Could not reboot node %s' % self)
        return ret
    
    def destroy(self, username):
        '''Returns True if the destroy was successful, otherwise False'''
        if self.provider.supports('destroy'):
            ret = self.provider.destroy_node(self)
            if ret:
                logging.info('Destroyed %s' % self)
            else:
                logging.error("controler.destroy_node() did not return True: %s.\nnot calling Node.delete()" % ret)
                return False
        self.decommission()
        self.destroyed_by = username
        self.destroyed_at = datetime.datetime.now()
        self.save()
        return True
    
    def decommission(self):
        '''Rename node and set its environment to decomissioned'''
        self.state = 'Terminated'
        # Rename node to free the name for future use
        counter = 1
        newname = "DECOM" + str(counter) + "-" + self.name
        while(len(Node.objects.filter(
                provider=self.provider,name=newname
            ).exclude(
                id=self.id
            ))):
            counter += 1
            newname = "DECOM" + str(counter) + "-" + self.name
        self.name = newname
        
        # Mark as decommissioned and save
        self.environment  = 'Decommissioned'
        self.save()
