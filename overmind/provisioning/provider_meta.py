# List of supported providers and related info
from django.conf import settings
from provisioning import plugins

LIBCLOUD_PROVIDERS = {
    'DUMMY': {
        'display_name': 'Dummy Provider',
        'access_key': 'Dummy Access Key',
        'secret_key': None,
    },
    'EC2_US_WEST': {
        'display_name': 'EC2 US West',
        'access_key': 'AWS Access Key ID',
        'secret_key': 'AWS Secret Key',
        # ex_keyname is needed for EC2 to have our ssh key deployed to nodes
        'extra_param': ['ex_keyname', settings.PUBLIC_KEY_FILE.split(".")[0]],
    },
    'EC2_US_EAST': {
        'display_name': 'EC2 US East',
        'access_key': 'AWS Access Key ID',
        'secret_key': 'AWS Secret Key',
        'extra_param': ['ex_keyname', settings.PUBLIC_KEY_FILE.split(".")[0]],
    },
    'EC2_EU_WEST': {
        'display_name': 'EC2 EU West',
        'access_key': 'AWS Access Key ID',
        'secret_key': 'AWS Secret Key',
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
    for provider in LIBCLOUD_PROVIDERS.keys():
        PROVIDERS[provider] = LIBCLOUD_PROVIDERS[provider]
        PROVIDERS[provider]['supported_actions'] = [
            'create', 'destroy', 'reboot',
            'list', 'images', 'sizes', 'locations',
        ]
        PROVIDERS[provider]['form_fields'] = ['image', 'size', 'location']

def add_plugins():
    plugin_dict = plugins.load_plugins()
    for provider in plugin_dict.keys():
        PROVIDERS[provider] = plugin_dict[provider]

add_libcloud_providers()
add_plugins()
