from libcloud import types
from libcloud.providers import get_driver


class ProviderController():
    def __init__(self, provider):
        self.provider = provider
        self.flavors = None
        self.images = None
        
        # Extremely dumb code to map provider_types to libcloud providers
        #TODO replace with a proper function/statement or extending PROVIDER_META
        provider_type = None
        #overmind's dummy driver'
        if provider.provider_type =="Dummy":
            provider_type = "Dummy"
        #libclouds dummy driver
        elif provider.provider_type =="Dummy_libcloud":
            provider_type = types.Provider.DUMMY
        ## REAL DRIVERS ##
        elif provider.provider_type == "EC2_US_EAST":
            provider_type = types.Provider.EC2_US_EAST
        elif provider.provider_type == "EC2_EU_WEST":
            provider_type = types.Provider.EC2_EU_WEST
        elif provider.provider_type == "Rackspace":
            provider_type = types.Provider.RACKSPACE
        else:
            raise Exception("Unknown Provider type")
        
        #Get driver from libcloud
        if provider_type == "Dummy": self.conn = DummyDriver()
        else:
            Driver = get_driver(provider_type)
            # Providers with only one access key
            if self.provider.secret_key == "":
                self.conn = Driver(self.provider.access_key)
            # Providers with 2 keys
            else:
                self.conn = Driver(self.provider.access_key, self.provider.secret_key)
    
    def spawn_new_instance(self, form):
        name   = form.cleaned_data['name']
        #TODO: get image id from the form image name
        images = self.get_images()
        flavors = self.get_flavors()
        image = None
        flavor = None
        #Choose correct image
        for img in images:
            image = img
            if image.id == form.cleaned_data['image']:
                break
        if image is None: #Abort: form image doesn't correspond to any provider image'
            return None
        #Choose correct flavor/flavor
        for f in flavors:
            flavor = f
            if flavor.id == form.cleaned_data['flavor']:
                break
        if flavor is None: #Abort: form flavor doesn't correspond to any provider flavor'
            return None
        node = self.conn.create_node(name=name, image=image, size=flavor)
        return {"ip, hostname, etc": "data", "some provider specific data": "data"}

    def get_images(self):
        if self.images is None:
            self.images = self.conn.list_images()
        if self.provider.provider_type.startswith("EC2"):
            self.images = [image for image in self.images if image.id.startswith('ami')]
        return self.images

    def get_flavors(self):
        if self.flavors is None:
            self.flavors = self.conn.list_sizes()
        return self.flavors
    
    def get_realms(self):
        #TODO: not implemented
        #return self.conn.??? #No idea how to list availability zones from libcloud
        return None


class DummyDriver():
    def create_node(self, name, image, size, flavor=None):
        return {"ip": "80.70.50.81"}
    
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
