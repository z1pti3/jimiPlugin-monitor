from core import plugin, model

class _monitor(plugin._plugin):
    version = 0.2

    def install(self):
        # Register models
        model.registerModel("monitorMSSQL","_monitorMSSQL","_action","plugins.monitor.models.action")
        model.registerModel("monitorPing","_monitorPing","_action","plugins.monitor.models.action")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("monitorMSSQL","_monitorMSSQL","_action","plugins.monitor.models.action")
        model.deregisterModel("monitorPing","_monitorPing","_action","plugins.monitor.models.action")
        return True

    def upgrade(self,LatestPluginVersion):
        if self.version < 0.2:
            model.registerModel("monitorPing","_monitorPing","_action","plugins.monitor.models.action")
