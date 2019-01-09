import hpotter.plugins
import importlib
import signal

def shutdown_servers(signum, frame):
    plugins_dict = hpotter.plugins.__dict__
    for plugin_name in plugins_dict['__all__']:
        importlib.import_module('hpotter.plugins.' + plugin_name)
        plugin = plugins_dict[plugin_name]
        plugin.stop_server()

if "__main__" == __name__:
    signal.signal(signal.SIGINT, shutdown_servers)

    plugins_dict = hpotter.plugins.__dict__
    for plugin_name in plugins_dict['__all__']:
        importlib.import_module('hpotter.plugins.' + plugin_name)
        plugin = plugins_dict[plugin_name]
        plugin.start_server()
