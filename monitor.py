import jimi

class _monitor(jimi.plugin._plugin):
    version = 0.4

    def install(self):
        # Register models
        jimi.model.registerModel("monitorMSSQL","_monitorMSSQL","_action","plugins.monitor.models.action")
        jimi.model.registerModel("monitorPing","_monitorPing","_action","plugins.monitor.models.action")
        jimi.model.registerModel("monitor","_monitor","_document","plugins.monitor.models.monitor")
        jimi.model.registerModel("monitorGetStatus","_monitorGetStatus","_action","plugins.monitor.models.action")
        jimi.model.registerModel("monitorSetStatus","_monitorSetStatus","_action","plugins.monitor.models.action")
        jimi.model.registerModel("monitorWebDashboard","_monitorWebDashboard","_document","plugins.monitor.models.monitor")
        return True

    def uninstall(self):
        # deregister models
        jimi.model.deregisterModel("monitorMSSQL","_monitorMSSQL","_action","plugins.monitor.models.action")
        jimi.model.deregisterModel("monitorPing","_monitorPing","_action","plugins.monitor.models.action")
        jimi.model.deregisterModel("monitor","_monitor","_document","plugins.monitor.models.monitor")
        jimi.model.deregisterModel("monitorGetStatus","_monitorGetStatus","_action","plugins.monitor.models.action")
        jimi.model.deregisterModel("monitorSetStatus","_monitorSetStatus","_action","plugins.monitor.models.action")
        jimi.model.deregisterModel("monitorWebDashboard","_monitorWebDashboard","_document","plugins.monitor.models.monitor")
        return True

    def upgrade(self,LatestPluginVersion):
        if self.version < 0.2:
            jimi.model.registerModel("monitorPing","_monitorPing","_action","plugins.monitor.models.action")
        if self.version < 0.3:
            jimi.model.registerModel("monitor","_monitor","_document","plugins.monitor.models.monitor")
            jimi.model.registerModel("monitorGetStatus","_monitorGetStatus","_action","plugins.monitor.models.action")
            jimi.model.registerModel("monitorSetStatus","_monitorSetStatus","_action","plugins.monitor.models.action")
            jimi.model.registerModel("monitorWebDashboard","_monitorWebDashboard","_document","plugins.monitor.models.monitor")
