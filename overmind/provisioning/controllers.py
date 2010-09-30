from libcloud import types
from libcloud.base import NodeAuthPassword, NodeAuthSSHKey
from libcloud.providers import get_driver
from libcloud.deployment import SSHKeyDeployment
from overmind.provisioning import plugins
from django.conf import settings
import copy, logging


class ProviderController():
    name = None
    extra_param_name = None
    extra_param_value = None
    
    def __init__(self, provider):
        self.extra_param_name  = provider.extra_param_name
        self.extra_param_value = provider.extra_param_value
        self.provider_type = provider.provider_type
        # Get libcloud provider type
        try:
            driver_type = types.Provider.__dict__[self.provider_type]
            # Get driver from libcloud
            Driver = get_driver(driver_type)
            logging.debug('selected "%s" libcloud driver' % self.provider_type)
        except KeyError:
            # Try to load provider from plugins
            Driver = plugins.get_driver(self.provider_type)
            logging.debug('selected "%s" plugin driver' % self.provider_type)
        except Exception, e:
            logging.critical('ProviderController can\'t find a driver for %s' % self.provider_type)
            raise Exception, "Unknown provider %s" % self.provider_type
        
        # Providers with only one access key
        if provider.secret_key == "":
            self.conn = Driver(provider.access_key)
        # Providers with 2 keys
        else:
            self.conn = Driver(provider.access_key, provider.secret_key)
        
    def create_node(self, form):
        name   = form.cleaned_data['name']
        #TODO: get image, size, location id from the form image name
        image  = None
        flavor = None
        realm  = None
        #Choose correct image
        for img in self.get_images():
            image = img
            if image.id == form.cleaned_data['image']:
                break
        #Choose correct flavor
        for f in self.get_flavors():
            flavor = f
            if flavor.id == form.cleaned_data['flavor']:
                break
        #Choose correct realm
        for r in self.get_realms():
            realm = r
            if realm.id == form.cleaned_data['realm']:
                break
        
        # Choose node creation strategy
        features = self.conn.features.get('create_node', [])
        
        try:
            if "ssh_key" in features:
                # Pass on public key and we are done
                logging.debug("Provider feature: ssh_key. Pass on key")
                node = self.conn.create_node(
                    name=name, image=image, size=flavor, location=realm,
                    auth=NodeAuthSSHKey(settings.PUBLIC_KEY)
                )
            elif 'generates_password' in features:
                # Use deploy_node to deploy public key
                logging.debug("Provider feature: generates_password. Use deploy_node")
                pubkey = SSHKeyDeployment(settings.PUBLIC_KEY) 
                node = self.conn.deploy_node(
                    name=name, image=image, size=flavor, location=realm,
                    deploy=pubkey
                )
            elif 'password' in features:
                # Pass on password and use deploy_node to deploy public key
                pubkey = SSHKeyDeployment(settings.PUBLIC_KEY)
                rpassword = generate_random_password(15)
                logging.debug("Provider feature: password. Pass on password=%s to deploy_node" % rpassword)
                node = self.conn.deploy_node(
                    name=name, image=image, size=flavor, location=realm,
                    auth=NodeAuthPassword(rpassword), deploy=pubkey
                )
            else:
                # Create node without any extra steps nor parameters
                logging.debug("Provider feature: none. call create_node")
                #include all plugin form fields
                args = copy.deepcopy(form.cleaned_data)
                for field in ['name', 'image', 'flavor', 'realm']:
                    if field in args:
                        del args[field]#Avoid colissions with default args
                args[self.extra_param_name] = self.extra_param_value
                
                node = self.conn.create_node(
                    name=name, image=image, size=flavor, location=realm, **args
                )
        except Exception, e:
            logging.error('while creating node. %s: %s' % (type(e), e))
            return None
        
        return {
            'public_ip': node.public_ip[0],
            'uuid': node.uuid,
            'state': node.state,
            'extra': node.extra,
        }
    
    def reboot_node(self, node):
        #TODO: this is braindead. We should be able to do self.conn.get_node(uuid=uuid)
        for n in self.conn.list_nodes():
            if n.uuid == node.uuid:
                return self.conn.reboot_node(n)
        return False
    
    def destroy_node(self, node):
        #TODO: this is braindead. We should be able to do self.conn.get_node(uuid=uuid)
        for n in self.conn.list_nodes():
            if n.uuid == node.uuid:
                return self.conn.destroy_node(n)
        return False
    
    def get_nodes(self):
        return self.conn.list_nodes()
    
    def get_images(self):
        images = self.conn.list_images()
        #TODO: remove EC2 if block
        if self.provider_type.startswith("EC2"):
            images = [image for image in images if image.id.startswith('ami')]
        return images
    
    def get_flavors(self):
        return self.conn.list_sizes()
    
    def get_realms(self):
        return self.conn.list_locations()


def generate_random_password(length):
    import random, string
    chars = []
    chars.extend([i for i in string.ascii_letters])
    chars.extend([i for i in string.digits])
    chars.extend([i for i in '\'"!@#$%&*()-_=+[{}]~^,<.>;:/?'])

    return ''.join([random.choice(chars) for i in range(length)])
