import time

import jimi

class _monitor(jimi.db._document):
    name = str()
    up = bool()
    itemType = str()
    lastSeen = int()

    _dbCollection = jimi.db.db["monitor"]

    def new(self, acl, name, up, itemType):
        self.acl = acl
        self.name = name
        self.up = up
        self.itemType = itemType
        self.lastSeen = int(time.time())
        return super(_monitor, self).new()

class _monitorWebDashboard(jimi.db._document):
    name = str()
    dashboardLayout = dict()
    monitorLinks = dict()

    def new(self, acl, name):
        self.acl = acl
        self.name = name
        return super(_monitorWebDashboard, self).new()

    _dbCollection = jimi.db.db["monitorWebDashboard"]