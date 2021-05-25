import time
import subprocess
import re
import platform
from pythonping import ping

from plugins.monitor.models import monitor

import jimi

class _monitorMSSQL(jimi.action._action):
	host = str()
	username = str()
	password = str()
	database = str()
	timeout = int()

	def setAttribute(self,attr,value,sessionData=None):
		if attr == "password" and not value.startswith("ENC "):
			if jimi.db.fieldACLAccess(sessionData,self.acl,attr,accessType="write"):
				self.password = "ENC {0}".format(jimi.auth.getENCFromPassword(value))
				return True
			return False
		return super(_monitorMSSQL, self).setAttribute(attr,value,sessionData=sessionData)

	def run(self,data,persistentData,actionResult):
		import pyodbc
		host = jimi.helpers.evalString(self.host,{"data" : data})
		username = jimi.helpers.evalString(self.username,{"data" : data})
		database = jimi.helpers.evalString(self.database,{"data" : data})
		password = jimi.auth.getPasswordFromENC(self.password)

		timeout = 30
		if self.timeout != 0:
			timeout=self.timeout

		status = "up"
			
		startTime=time.time()
		try:
			connection = pyodbc.connect("Driver={0};Server={1};Database={2};uid={3};pwd={4}".format(pyodbc.drivers()[0],host,database,username,password),timeout=timeout)
			connection.close()
			endTime=time.time()
			duration = endTime - startTime
			actionResult["result"] = True
			actionResult["rc"] = 0
			return actionResult
		except:
			actionResult["result"] = False
			actionResult["rc"] = 504
			status = "down"
		finally:
			endTime=time.time()
			duration = endTime - startTime
			actionResult["data"] = { "server" : host, "database" : database, "startTime" : startTime, "endTime" : endTime, "duration" : duration, "status": status }

		return actionResult

class _monitorPing(jimi.action._action):
	host = str()
	count = 3
	timeout = 2

	def run(self,data,persistentData,actionResult):
		host = jimi.helpers.evalString(self.host,{"data" : data})
		actionResult["result"] = False
		actionResult["up"] = False
		actionResult["rc"] = 999
		try:
			pingResult = ping(host, timeout=self.timeout, count=self.count)
			actionResult["result"] = True
			actionResult["rc"] = 0
			actionResult["up"] = True
			actionResult["sent"] = len(pingResult._responses)
			actionResult["lost"] = float(pingResult.packets_lost*100)
			if actionResult["lost"] < 100:
				actionResult["min_rtt"] = float(pingResult.rtt_min_ms)
				actionResult["max_rtt"] = float(pingResult.rtt_max_ms)
				actionResult["avg_rtt"] = float(pingResult.rtt_avg_ms)
			else:
				actionResult["min_rtt"] = -1
				actionResult["max_rtt"] = -1
				actionResult["avg_rtt"] = -1
		except Exception as e:
			if "Cannot resolve address" in str(e):
				actionResult["result"] = False
				actionResult["rc"] = 2
				actionResult["up"] = False
				actionResult["msg"] = "Host not found"
		return actionResult

class _monitorGetStatus(jimi.action._action):
	itemName = str()

	def __init__(self):
		jimi.cache.globalCache.newCache("monitorCache")

	def run(self,data,persistentData,actionResult):
		itemName = jimi.helpers.evalString(self.itemName,{"data" : data})

		cacheItem = jimi.cache.globalCache.get("monitorCache",itemName,getMonitorItem)
		if cacheItem != None:
			cacheItem = cacheItem[0]
			actionResult["result"] = True
			actionResult["rc"] = 0
			actionResult["monitor"] = { "name" : cacheItem.name, "up" : cacheItem.up, "type" : cacheItem.itemType, "lastSeen" : cacheItem.lastSeen }
			return actionResult
		actionResult["result"] = False
		actionResult["rc"] = 404
		actionResult["msg"] = "No monitor item found with that itemName"
		return actionResult

class _monitorSetStatus(jimi.action._action):
	itemName = str()
	itemStatus = bool()
	itemType = str()

	def __init__(self):
		jimi.cache.globalCache.newCache("monitorCache")

	def run(self,data,persistentData,actionResult):
		itemName = jimi.helpers.evalString(self.itemName,{"data" : data})
		itemType = jimi.helpers.evalString(self.itemType,{"data" : data})

		cacheItem = jimi.cache.globalCache.get("monitorCache",itemName,getMonitorItem)
		if cacheItem == None:
			monitor._monitor().new(self.acl,itemName,self.itemStatus,itemType)
			actionResult["result"] = True
			actionResult["rc"] = 0
			return actionResult
		else:
			cacheItem = cacheItem[0]
			cacheItem.up = self.itemStatus
			cacheItem.lastSeen = int(time.time())
			cacheItem.update(["up","lastSeen"])
			actionResult["result"] = True
			actionResult["rc"] = 0
			return actionResult
		

def getMonitorItem(itemName,sessionData):
	return monitor._monitor().getAsClass(query={ "name" : itemName })