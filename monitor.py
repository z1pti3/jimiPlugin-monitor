from core import plugin, model

class _monitor(plugin._plugin):
    version = 0.1

    def install(self):
        # Register models
        model.registerModel("monitorMSSQL","_monitorMSSQL","_action","plugins.monitor.models.action")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("monitorMSSQL","_monitorMSSQL","_action","plugins.monitor.models.action")
        return True

    