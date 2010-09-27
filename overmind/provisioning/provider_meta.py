# List of supported providers and related info
from django.conf import settings
from overmind.provisioning import plugins

PROVIDERS = {
    'DUMMY': {
        'display_name': 'Dummy Provider',
        'access_key': 'Dummy Access Key',
        'secret_key': None,
        'extra_param': ['ex_keyname', settings.PUBLIC_KEY_FILE.split(".")[0]],
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

def add_plugins():
    plugin_list = plugins.get_plugins()
    for p in plugin_list.keys():
        PROVIDERS[p] = plugin_list[p]

add_plugins()
