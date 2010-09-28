# Dedicated Hardware plugin
from libcloud.base import ConnectionKey, NodeDriver, Node
from libcloud.types import NodeState


display_name = "Dedicated Hardware"
access_key   = None
secret_key   = None
form_fields  = ['ip']
supported_actions = ['create']


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
        #TODO: Check ip correctness
        if not kwargs.get('ip'): return None
        # IP serves as uuid
        n = Node(id=kwargs.get('ip').replace(".",""),
                 name=kwargs.get('name'),
                 state=NodeState.RUNNING,
                 public_ip=[kwargs.get('ip')],
                 private_ip=[],
                 driver=self)
        return n
    
    # TODO: remove dummy methods
    # and catch NotImplemented Exceptions upstream (or check supported)
    def list_images(self): return []
    def list_sizes(self): return []
    def list_locations(self): return []

