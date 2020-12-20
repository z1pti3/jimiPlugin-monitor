import time
import subprocess
import re
import platform

from core.models import action
from core import helpers, auth, db

class _monitorMSSQL(action._action):
	host = str()
	username = str()
	password = str()
	database = str()
	timeout = int()

	def setAttribute(self,attr,value,sessionData=None):
		if attr == "password" and not value.startswith("ENC "):
			if db.fieldACLAccess(sessionData,self.acl,attr,accessType="write"):
				self.password = "ENC {0}".format(auth.getENCFromPassword(value))
				return True
			return False
		return super(_monitorMSSQL, self).setAttribute(attr,value,sessionData=sessionData)

	def run(self,data,persistentData,actionResult):
		import pyodbc
		host = helpers.evalString(self.host,{"data" : data})
		username = helpers.evalString(self.username,{"data" : data})
		database = helpers.evalString(self.database,{"data" : data})
		password = auth.getPasswordFromENC(self.password)

		timeout = 30
		if self.timeout != 0:
			timeout=self.timeout
			
		startTime=time.time()
		try:
			connection = pyodbc.connect("Driver={SQL Server Native Client 11.0};""Server={0};""Database={1};""uid={2};pwd={3}".format(host,database,username,password),timeout=timeout)
			connection.close()
			endTime=time.time()
			duration = endTime - startTime
			actionResult["result"] = True
			actionResult["rc"] = 0
			return actionResult
		except:
			actionResult["result"] = False
			actionResult["rc"] = 504
		finally:
			endTime=time.time()
			duration = endTime - startTime
			actionResult["data"] = { "startTime" : startTime, "endTime" : endTime, "duration" : duration, "status": "up" }

		return actionResult

class _monitorPing(action._action):
	host = str()

	def run(self,data,persistentData,actionResult):
		host = helpers.evalString(self.host,{"data" : data})
		actionResult["result"] = False
		actionResult["up"] = False
		actionResult["rc"] = 999
		if platform.system() == "Windows":
			ping = subprocess.Popen(["ping", "-n", "3", host], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
			out, error = ping.communicate()
			out=out.decode()
			if "could not find host" in out:
				actionResult["result"] = False
				actionResult["rc"] = 2
				actionResult["up"] = False
				actionResult["msg"] = "Host not found"
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
			ping = subprocess.Popen(["ping", "-c", "3", host], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
			out, error = ping.communicate()
			out=out.decode()
			if "Name or service not known" in out:
				actionResult["result"] = False
				actionResult["rc"] = 2
				actionResult["up"] = False
				actionResult["msg"] = "Host not found"
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
					actionResult["max_rtt"] = float(outResponseMatches[0][1])
					actionResult["avg_rtt"] = float(outResponseMatches[0][2])
				else:
					actionResult["result"] = False
					actionResult["rc"] = 9
					actionResult["msg"] = "No response"
					actionResult["up"] = False
					actionResult["sent"] = int(outPacketMatches[0][0])
					actionResult["received"] = int(outPacketMatches[0][1])
					actionResult["lost"] = int(outPacketMatches[0][0]) - int(outPacketMatches[0][1])
		return actionResult