# Dedicated Hardware plugin
#from providerplugin import BaseDriver
from libcloud.base import ConnectionKey, NodeDriver, Node
from libcloud.types import NodeState

display_name = "Dedicated Hardware"
access_key   = None
secret_key   = None
form_fields  = ['ip']

class Connection(ConnectionKey):
    '''Dummy connection'''
    def connect(self, host=None, port=None):
        pass

class Driver(NodeDriver):
    name = display_name
    type = 0

    def __init__(self, creds):
        self.creds = creds
        self.connection = Connection(self.creds)
    
    def create_node(self, **kwargs):
        if not kwargs.get('ip'): return None
        n = Node(id=self.generate_random_num(),
                 name=kwargs.get('name'),
                 state=NodeState.RUNNING,
                 public_ip=[kwargs.get('ip')],
                 private_ip=[],
                 driver=self)
        return n
    
    def list_nodes(self): return []
    def list_images(self): return []
    def list_sizes(self): return []
    def list_locations(self): return []

    def generate_random_num(self):
        import random
        return random.randint(0,10000)
