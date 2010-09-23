from libcloud import types
from libcloud.base import NodeAuthPassword, NodeAuthSSHKey
from libcloud.providers import get_driver
from libcloud.deployment import SSHKeyDeployment
from django.conf import settings

class ProviderController():
    def __init__(self, provider):
        self.provider = provider
        
        # Get libcloud provider type
        try:
            driver_type = types.Provider.__dict__[self.provider.provider_type]
        except KeyError:
            raise Exception, "Unknown provider %s" % self.provider.provider_type
        
        # Get driver from libcloud
        Driver = get_driver(driver_type)
        # Providers with only one access key
        if self.provider.secret_key == "":
            self.conn = Driver(self.provider.access_key)
        # Providers with 2 keys
        else:
            self.conn = Driver(self.provider.access_key, self.provider.secret_key)
    
    def spawn_new_instance(self, form):
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
        if image is None:
            #Abort: form image doesn't correspond to any provider image'
            return None
        #Choose correct flavor
        for f in self.get_flavors():
            flavor = f
            if flavor.id == form.cleaned_data['flavor']:
                break
        if flavor is None:
            #Abort: form flavor doesn't correspond to any provider flavor'
            return None
        #Choose correct realm
        for r in self.get_realms():
            realm = r
            if realm.id == form.cleaned_data['realm']:
                break
        if realm is None:
            #Abort: form realm doesn't correspond to any provider location'
            return None
        
        # Choose node creation strategy
        try:
            features = self.conn.features.get('create_node')
        except AttributeError:
            features = []
        
        try:
            if "ssh_key" in features:
                # Pass on public key and we are done
                print "Provider: ssh_key. Pass on key"
                node = self.conn.create_node(
                    name=name, image=image, size=flavor, location=realm,
                    auth=NodeAuthSSHKey(settings.PUBLIC_KEY)
                )
            elif 'generates_password' in features:
                # Use deploy_node to deploy public key
                print "Provider: generates_password. Use deploy_node"
                pubkey = SSHKeyDeployment(settings.PUBLIC_KEY) 
                node = self.conn.deploy_node(
                    name=name, image=image, size=flavor, location=realm,
                    deploy=pubkey
                )
            elif 'password' in features:
                # Pass on password and use deploy_node to deploy public key
                pubkey = SSHKeyDeployment(settings.PUBLIC_KEY)
                rpassword = generate_random_password(15)
                print "Provider: password. Pass on password=%s" % rpassword
                node = self.conn.deploy_node(
                    name=name, image=image, size=flavor, location=realm,
                    auth=NodeAuthPassword(rpassword), deploy=pubkey
                )
            else:
                # Create node without any extra steps nor parameters
                print "Provider: no features. Create node without parameters"
                args = {
                    self.provider.extra_param_name: self.provider.extra_param_value
                }
                node = self.conn.create_node(
                    name=name, image=image, size=flavor, location=realm, **args
                )
        except Exception, e:
            print "Exception of type %s" % type(e)
            print e
            return None
        
        return {
            'public_ip': node.public_ip[0],
            'uuid': node.uuid,
            'extra': node.extra
        }
    
    def reboot_node(self, instance):
        #TODO: this is braindead. We should be able to do self.conn.get_node(uuid=uuid)
        node = None
        for n in self.conn.list_nodes():
            if n.uuid == instance.instance_id:
                node = n
                break
        return self.conn.reboot_node(node)
    
    def destroy_node(self, instance):
        #TODO: this is braindead. We should be able to do self.conn.get_node(uuid=uuid)
        if self.provider.provider_type == "Dummy_libcloud":
            return True
        node = None
        for n in self.conn.list_nodes():
            if n.uuid == instance.instance_id:
                node = n
                break
        return self.conn.destroy_node(node)
    
    def get_nodes(self):
        return self.conn.list_nodes()
    
    def get_images(self):
        #TODO: remove EC2 if
        if self.provider.provider_type.startswith("EC2"):
            images = [image for image in self.conn.list_images() if image.id.startswith('ami')]
        else:
            images = self.conn.list_images()
        return images
    
    def get_flavors(self):
        return self.conn.list_sizes()
    
    def get_realms(self):
        return self.conn.list_locations()


class DummyDriver():
    def create_node(self, name, image, size, flavor=None):
        return {"public_ip": "80.70.50.81", 'uuid': 'asdkfjsaopdj5780fcd5'}
    
    def list_sizes(self):
        sizes = [
            DummySize("1", "m1.small"),
            DummySize("2", "c1.medium"),
        ]
        return sizes
    
    def list_images(self):
        images = [
            DummyImage("1", "Fedora 14"),
            DummyImage("2", "Ubuntu 10.04"),
        ]
        return images
    
    def list_realms(self):
        return ['us-east-1a', 'us-east-1zzz']

class DummyImage():
    def __init__(self, id, name):
        self.id = id
        self.name = name

class DummySize():
    def __init__(self, id, name):
        self.id = id
        self.name = name

def generate_random_password(length):
    import random, string
    chars = []
    chars.extend([i for i in string.ascii_letters])
    chars.extend([i for i in string.digits])
    chars.extend([i for i in '\'"!@#$%&*()-_=+[{}]~^,<.>;:/?'])

    return ''.join([random.choice(chars) for i in range(length)])
