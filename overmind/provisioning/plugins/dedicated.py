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
    
    def _validate_ip(self, ip):
        try:
            # Validate with IPy module
            from IPy import IP
            try:
                IP(ip)
            except ValueError:
                raise Exception, "Incorrect IP"
        except ImportError:
            # Validate with regex
            import re
            ValidIpAddressRegex = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
            if re.match(ValidIpAddressRegex, ip) is None:
                raise Exception, "Incorrect IP"
    
    def create_node(self, **kwargs):
        # Validate IP address
        ip = kwargs.get('ip', '')
        self._validate_ip(ip)
        
        # Return Node object (IP serves as uuid feed)
        n = Node(id=ip.replace(".",""),
                 name=kwargs.get('name'),
                 state=NodeState.RUNNING,
                 public_ip=[ip],
                 private_ip=[],
                 driver=self)
        return n
