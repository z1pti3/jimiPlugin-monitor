import time
import subprocess
import re
import platform
from pythonping import ping
import socket

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
	timeout = 2
	count = 5

	def run(self,data,persistentData,actionResult):
		host = jimi.helpers.evalString(self.host,{"data" : data})
		actionResult["result"] = False
		actionResult["up"] = False
		actionResult["rc"] = 999
		if platform.system() == "Windows":
			ping = subprocess.Popen(["ping", "-n", str(self.count), "-w", str(self.timeout), host], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
			out, error = ping.communicate()
			out=out.decode()
			if "could not find host" in out:
				actionResult["result"] = False
				actionResult["rc"] = 2
				actionResult["up"] = False
				actionResult["msg"] = "Host not found"
			elif "Destination Net Unreachable" in out:
				actionResult["result"] = False
				actionResult["rc"] = 2
				actionResult["up"] = False
				actionResult["msg"] = "Destination Net Unreachable"
			else:
				outPacketMatches = re.findall('Packets: Sent = ([0-9]+), Received = ([0-9]+), Lost = ([0-9]+)',out)
				outResponseMatches = re.findall('Minimum = ([0-9]+)ms, Maximum = ([0-9]+)ms, Average = ([0-9]+)ms',out)
				if outResponseMatches:
					actionResult["result"] = True
					actionResult["rc"] = 0
					actionResult["up"] = True
					actionResult["sent"] = int(outPacketMatches[0][0])
					actionResult["received"] = int(outPacketMatches[0][1])
					actionResult["lost"] = int(outPacketMatches[0][2])
					actionResult["min_rtt"] = int(outResponseMatches[0][0])
					actionResult["max_rtt"] = int(outResponseMatches[0][1])
					actionResult["avg_rtt"] = int(outResponseMatches[0][2])
				else:
					actionResult["result"] = False
					actionResult["rc"] = 9
					actionResult["msg"] = "No response"
					actionResult["up"] = False
					actionResult["sent"] = int(outPacketMatches[0][0])
					actionResult["received"] = int(outPacketMatches[0][1])
					actionResult["lost"] = int(outPacketMatches[0][2])
		elif platform.system() == "Linux":
			ping = subprocess.Popen(["ping", "-c", str(self.count), "-W", str(self.timeout), host], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
			out, error = ping.communicate()
			out=out.decode()
			if "Name or service not known" in out:
				actionResult["result"] = False
				actionResult["rc"] = 2
				actionResult["up"] = False
				actionResult["msg"] = "Host not found"
			elif "Destination Net Unreachable" in out:
				actionResult["result"] = False
				actionResult["rc"] = 2
				actionResult["up"] = False
				actionResult["msg"] = "Destination Net Unreachable"
			else:
				outPacketMatches = re.findall('([0-9]+) packets transmitted, ([0-9]+) received, ([0-9]+)% packet loss',out)
				outResponseMatches = re.findall('rtt min/avg/max/mdev = ([0-9\.]+)/([0-9\.]+)/([0-9\.]+)/',out)
				if outResponseMatches:
					actionResult["result"] = True
					actionResult["rc"] = 0
					actionResult["up"] = True
					actionResult["sent"] = int(outPacketMatches[0][0])
					actionResult["received"] = int(outPacketMatches[0][1])
					actionResult["lost"] = int(outPacketMatches[0][0]) - int(outPacketMatches[0][1])
					actionResult["min_rtt"] = float(outResponseMatches[0][0])
					actionResult["max_rtt"] = float(outResponseMatches[0][2])
					actionResult["avg_rtt"] = float(outResponseMatches[0][1])
				else:
					actionResult["result"] = False
					actionResult["rc"] = 9
					actionResult["msg"] = "No response"
					actionResult["up"] = False
					actionResult["sent"] = int(outPacketMatches[0][0])
					actionResult["received"] = int(outPacketMatches[0][1])
					actionResult["lost"] = int(outPacketMatches[0][0]) - int(outPacketMatches[0][1])
		return actionResult

class _monitorTCPCheck(jimi.action._action):
	host = str()
	port = int()
	timeout = 10

	def run(self,data,persistentData,actionResult):
		host = jimi.helpers.evalString(self.host,{"data" : data})
		actionResult["result"] = False
		actionResult["up"] = False
		actionResult["rc"] = 999
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(self.timeout)
		try:
			sock.connect((host,self.port))
			sock.close()
			actionResult["result"] = True
			actionResult["rc"] = 0
			actionResult["up"] = True
		except Exception as e:
			actionResult["result"] = False
			actionResult["rc"] = 2
			actionResult["up"] = False
			actionResult["msg"] = "Failed to connect"
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
