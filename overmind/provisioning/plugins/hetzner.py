# Hetzner plugin
from libcloud.base import ConnectionUserAndKey, NodeDriver, Node
from libcloud.types import NodeState, InvalidCredsException
import httplib2
import simplejson as json
from urllib import urlencode

display_name = "Hetzner"
access_key   = 'User'
secret_key   = 'Password'
form_fields  = None
# It seems that reboot (reset in the Hetzner API) doesn't work, so don't add
supported_actions = ['list']


class Connection():
    host = "https://robot-ws.your-server.de/"
    
    def __init__(self, user, password):
        self.conn = httplib2.Http(".cache")
        self.conn.add_credentials(user, password)
        
    def _raise_error(self, response, content):
        if response.get('status') == '400':
            raise Exception, "Invalid parameters"
        elif response.get('status') == '401':
            raise InvalidCredsException
        elif response.get('status') == '404' and content == 'Server not found':
            raise Exception, "Server not found"
        elif response.get('status') == '404':
            raise Exception, "Reset not available"
        elif response.get('status') == '500' and content == 'Reset failed':
            raise Exception, "Reset failed"
        else:
            raise Exception, "Unknown error: " + response.get('status')
    
    def request(self, path, method='GET', params=None):
        if method != 'GET' and method != 'POST': return None
        data = None
        if params: data = urlencode(params)
        response, content = self.conn.request(
            self.host + path,
            method,
            data,
        )
        if response.get('status') == '200':
            return json.loads(content)
        else:
            self._raise_error(response, content)


class Driver(NodeDriver):
    name = display_name
    type = 0
    
    NODE_STATE_MAP = {
        'ready': NodeState.RUNNING,
        'process': NodeState.PENDING,
    }
    
    def __init__(self, user, password):
        self.connection = Connection(user, password)
    
    def _parse_nodes(self, data):
        nodes = []
        for n in data:
            nodedata = n['server']
            response = self.connection.request('server/%s' % nodedata['server_ip'])
            nodedata['extra_ips'] = ", ".join(response['server']['ip'])
            # dict.get() will return None even if we write get('subnet', [])
            subnets = response['server'].get('subnet') or []
            nodedata['subnet'] = ", ".join(s['ip'] for s in subnets)
            nodes.append(nodedata)
        return nodes
    
    def _to_node(self, el):
        public_ip = [el.get('server_ip')]
        n = Node(id=el.get('server_ip').replace(".",""),
                 name=el.get('server_ip'),
                 state=self.NODE_STATE_MAP.get(el.get('status'), NodeState.UNKNOWN),
                 public_ip=public_ip,
                 private_ip=[],
                 driver=self,
                 extra={
                    'location':   el.get('dc'),
                    'product':    el.get('product'),
                    'traffic':    el.get('traffic'),
                    'paid_until': el.get('paid_until'),
                    'extra_ips':  el.get('extra_ips'),
                    'subnet':     el.get('subnet'),
                 })
        return n
    
    def list_nodes(self):
        #TODO: 404 error "No server found" needs to be handled
        response = self.connection.request('server')
        nodes = []
        for node in self._parse_nodes(response):
            nodes.append(self._to_node(node))
        return nodes
    
    def reboot(self, node):
        params = { 'type': 'sw' }#Support hd reset?
        response = self.connection.request(
            'reset/' + node.public_ip[0] + "/", method='POST', params=params
        )
