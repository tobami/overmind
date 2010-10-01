# List of supported providers and related info
from django.conf import settings
from overmind.provisioning import plugins

LIBCLOUD_PROVIDERS = {
    'DUMMY': {
        'display_name': 'Dummy Provider',
        'access_key': 'Dummy Access Key',
        'secret_key': None,
    },
    'EC2_US_WEST': {
        'display_name': 'EC2 US West',
        'access_key': 'AWS Access Key ID',
        'secret_key': 'AWS Secret Key ID',
        'extra_param': ['ex_keyname', settings.PUBLIC_KEY_FILE.split(".")[0]],
    },
    'EC2_US_EAST': {
        'display_name': 'EC2 US East',
        'access_key': 'AWS Access Key ID',
        'secret_key': 'AWS Secret Key ID',
        'extra_param': ['ex_keyname', settings.PUBLIC_KEY_FILE.split(".")[0]],
    },
    'EC2_EU_WEST': {
        'display_name': 'EC2 EU West',
        'access_key': 'AWS Access Key ID',
        'secret_key': 'AWS Secret Key ID',
        'extra_param': ['ex_keyname', settings.PUBLIC_KEY_FILE.split(".")[0]],
    },
    'RACKSPACE': {
        'display_name': 'Rackspace',
        'access_key': 'Username',
        'secret_key': 'API Access Key',
    },
}

PROVIDERS = {}

def add_libcloud_providers():
    for p in LIBCLOUD_PROVIDERS.keys():
        PROVIDERS[p] = LIBCLOUD_PROVIDERS[p]
        PROVIDERS[p]['supported_actions'] = ['create', 'destroy', 'reboot', 'list']
        PROVIDERS[p]['form_fields'] = ['image', 'flavor', 'realm']

add_libcloud_providers()

def add_plugins():
    plugin_dict = plugins.load_plugins()
    for p in plugin_dict.keys():
        PROVIDERS[p] = plugin_dict[p]

add_plugins()
