# Provisioning plugins module

def get_driver(provider):
    """Gets a driver
    @param provider: name of provider to get driver
    """
    _mod = __import__(provider, globals(), locals())
    return getattr(_mod, "Driver")

def get_plugins():
    import os
    plugin_list = {}
    for f in os.listdir(os.path.dirname(__file__)):
        if f.endswith('.py') and f != '__init__.py' and f != 'providerplugin.py':
            driver_name = f.rstrip('.py')
            _mod = __import__(driver_name, globals(), locals())
            
            meta = {
                'display_name': _mod.display_name,
                'access_key': _mod.access_key,
                'secret_key': _mod.secret_key,
                'plugin'    : True,
                'form_fields': _mod.form_fields,
            }
            plugin_list[driver_name] = meta
    return plugin_list
