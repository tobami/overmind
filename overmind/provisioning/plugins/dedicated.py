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
        # Validate IP address
        if not kwargs.get('ip'): return None
        try:
            from IPy import IP
            IP(kwargs.get('ip'))#raise ValueError if incorrect IP
        except ImportError:
            pass#no validation
        
        # Return Node object (IP serves as uuid feed)
        n = Node(id=kwargs.get('ip').replace(".",""),
                 name=kwargs.get('name'),
                 state=NodeState.RUNNING,
                 public_ip=[kwargs.get('ip')],
                 private_ip=[],
                 driver=self)
        return n
