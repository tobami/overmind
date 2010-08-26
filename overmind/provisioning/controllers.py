from libcloud import types
from libcloud.providers import get_driver


class ProviderController():
    def __init__(self, provider):
        self.provider = provider
        
        # Extremely dumb code to map provider_types to libcloud providers
        #TODO replace with a proper function/statement or extending PROVIDER_META
        provider_type = None
        if provider.provider_type == "EC2_US_EAST":
            provider_type = types.Provider.EC2_US_EAST
        elif provider.provider_type == "EC2_EU_WEST":
            provider_type = types.Provider.EC2_EU_WEST
        elif provider.provider_type == "Rackspace":
            provider_type = types.Provider.RACKSPACE
        else:
            raise Exception("Unknown Provider type")
        
        #Get driver from libcloud
        Driver = get_driver(provider_type) 
        self.conn = Driver(self.provider.access_key, self.provider.secret_key)
        return None
    
    def spawn_new_instance(self, form):
        name   = form.cleaned_data['name']
        #TODO: get image id from the form image name
        images = self.get_images()
        image = None
        for img in images:
            image = img
            if image == form.cleaned_data['image']:
                break
        flavor = form.cleaned_data['flavor']
        node   = self.conn.create_node(name=name, image=image, size=flavor)
        return {"ip, hostname, etc": "data", "some provider specific data": "data"}
    
    def get_flavors(self):
        return self.conn.list_sizes()
        #NOTE: dummy code to develop without a cloud accountself
        if self.provider == "Rackspace":
            return ['default']
        else:
            return ['m1-small', 'c1-medium']
        #NOTE: END dummy code
    
    def get_images(self):
        return self.conn.list_images()
        #NOTE: dummy code to develop without a cloud accountself
        if self.provider == "Rackspace":
            return ['Debian Lenny']
        else:
            return ['Ubuntu 10.04', 'Debian 5.0']
        #NOTE: END dummy code
    
    def get_realms(self):
        #return self.conn.??? #No idea how to list availability zones from libcloud
        #NOTE: dummy code to develop without a cloud accountself
        if self.provider == "Rackspace":
            return ['default']
        else:
            return ['us-east-1a', 'us-east-1zzz']
        #NOTE: END dummy code
