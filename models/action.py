import time

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

