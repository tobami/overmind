from libcloud import types
from libcloud.providers import get_driver


class ProviderController():
    def __init__(self, provider):
        self.provider = provider
        
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
            if self.provider.secret_key == "":
                self.conn = Driver(self.provider.access_key)
            else:
                self.conn = Driver(self.provider.access_key, self.provider.secret_key)
    
    def spawn_new_instance(self, form):
        name   = form.cleaned_data['name']
        #TODO: get image id from the form image name
        images = self.get_images()
        image = None
        #Choose correct image
        for img in images:
            image = img
            if image == form.cleaned_data['image']:
                break
        if image is None: #Abort: form image doesn't correspond to any provider image'
            return None
        flavor = form.cleaned_data['flavor']
        node   = self.conn.create_node(name=name, image=image, size=flavor)
        return {"ip, hostname, etc": "data", "some provider specific data": "data"}
    
    def get_flavors(self):
        return self.conn.list_sizes()
    
    def get_images(self):
        return self.conn.list_images()
    
    def get_realms(self):
        #TODO: not implemented
        #return self.conn.??? #No idea how to list availability zones from libcloud
        return None


class DummyDriver():
    def create_node(self, name, image, size, flavor=None):
        return {"ip": "80.70.50.81"}
    
    def list_sizes(self):
        return ['m1-small', 'c1-medium']
    
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
