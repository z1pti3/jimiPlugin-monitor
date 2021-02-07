import urllib.parse
import json
import  uuid
from pathlib import Path
from flask import request, send_from_directory
from markupsafe import Markup

from flask import Blueprint, render_template
from flask import current_app as app

from plugins.monitor.models import monitor

import jimi

pluginPages = Blueprint('monitorPages', __name__, template_folder="templates")

@pluginPages.app_template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.parse.quote_plus(s)
    return Markup(s)

@pluginPages.route('/monitor/includes/<file>')
def custom_static(file):
    # Directroy transversal safe?
    return send_from_directory(str(Path("plugins/monitor/web/includes")), file)

@pluginPages.route("/monitor/", methods=["GET"])
def mainPage():
    dashboards = monitor._monitorWebDashboard().query(sessionData=jimi.api.g.sessionData,query={},fields=["name"])["results"]
    return render_template("dashboards.html", dashboards=dashboards, CSRF=jimi.api.g.sessionData["CSRF"])

@pluginPages.route("/monitor/", methods=["PUT"])
def newDashboard():
    data = json.loads(jimi.api.request.data)
    monitor._monitorWebDashboard().new({"ids" : [ { "accessID" : jimi.api.g.sessionData["primaryGroup"], "read" : True, "write" : True, "delete" : True } ]},data["dashboardName"])
    return { }, 200

@pluginPages.route("/monitor/", methods=["DELETE"])
def deleteDashboard():
    data = json.loads(jimi.api.request.data)
    monitor._monitorWebDashboard().api_delete(id=data["id"])
    return { }, 200

@pluginPages.route("/monitor/dashboard/", methods=["GET"])
def dashboardPage():
    dashboardID = request.args.get('dashboardID')
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
        return render_template("dashboard.html", CSRF=jimi.api.g.sessionData["CSRF"], image=dashboard.image)
    return {}, 404

@pluginPages.route("/monitor/dashboard/<dashboardID>/image/", methods=["GET"])
def dashboardSetImage(dashboardID):
    image = request.args.get('image')
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
        dashboard.image = image
        dashboard.update(["image"])
        return {}, 200
    return {}, 404

@pluginPages.route("/monitor/dashboard/<dashboardID>/", methods=["POST"])
def getDashboard(dashboardID):
    def getIcon(itemType,up):
        if itemType == "firewall":
            if up:
                return "/plugin/monitor/includes/firewall-up.svg"
            else:
                return "/plugin/monitor/includes/firewall-down.svg"
        elif itemType == "router":
            if up:
                return "/plugin/monitor/includes/router-up.svg"
            else:
                return "/plugin/monitor/includes/router-down.svg"
        elif itemType == "switch":
            if up:
                return "/plugin/monitor/includes/switch-up.svg"
            else:
                return "/plugin/monitor/includes/switch-down.svg"
        elif itemType == "loadbalancer":
            if up:
                return "/plugin/monitor/includes/loadbalancer-up.svg"
            else:
                return "/plugin/monitor/includes/loadbalancer-down.svg"
        elif itemType == "user":
            if up:
                return "/plugin/monitor/includes/user-up.svg"
            else:
                return "/plugin/monitor/includes/user-down.svg"
        elif itemType == "server":
            if up:
                return "/plugin/monitor/includes/server-up.svg"
            else:
                return "/plugin/monitor/includes/server-down.svg"
        elif itemType == "computer":
            if up:
                return "/plugin/monitor/includes/computer-up.svg"
            else:
                return "/plugin/monitor/includes/computer-down.svg"
        elif itemType == "ap":
            if up:
                return "/plugin/monitor/includes/ap-up.svg"
            else:
                return "/plugin/monitor/includes/ap-down.svg"
        elif itemType == "building":
            if up:
                return "/plugin/monitor/includes/building-up.svg"
            else:
                return "/plugin/monitor/includes/building-down.svg"
        elif itemType == "vpn":
            if up:
                return "/plugin/monitor/includes/vpn-up.svg"
            else:
                return "/plugin/monitor/includes/vpn-down.svg"
        elif itemType == "cloud":
            return "/plugin/monitor/includes/cloud.svg"
        return None
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
    else:
        return {},404
    data = json.loads(jimi.api.request.data)

    flowchartOperators = data["operators"]
    flowchartLinks = data["links"]

    flowchartResponse = { "operators" : { "delete" : {}, "create" : {}, "update" : {} }, "links" : { "delete" : {}, "create" : {}, "update" : {} } }

    monitorItemsList = [ jimi.db.ObjectId(y["monitorId"]) for x, y in dashboard.dashboardLayout.items() ]

    monitorItems = monitor._monitor().query(query={ "_id" : { "$in" : monitorItemsList } })["results"]
    monitorItemsDict = {}
    for monitorItem in monitorItems:
        monitorItemsDict[monitorItem["_id"]] = monitorItem
    
    for dashboardID, dashboardItem in dashboard.dashboardLayout.items():
        flowchartResponseType = "create"
        if dashboardID in flowchartOperators:
            # If it already exits then its an update
            flowchartResponseType = "update"
        # Setting position if it has changed since last pollTime
        name = monitorItemsDict[dashboardItem["monitorId"]]["name"]
        up = monitorItemsDict[dashboardItem["monitorId"]]["up"]
        try:
            size = dashboardItem["size"]
        except KeyError:
            size = 25
        node = {}
        color = "green"
        if not up:
            color = "red"
        if flowchartResponseType == "create":
            node["x"] = dashboardItem["x"]
            node["y"] = dashboardItem["y"]
            node["shape"] = "dot"
            try:
                node["image"] = getIcon(monitorItemsDict[dashboardItem["monitorId"]]["itemType"],up)
                if node["image"] == None:
                    del node["image"]
                else:
                    node["shape"] = "image"
            except KeyError:
                pass
            node["borderWidth"] = 1
            node["borderWidthSelected"] = 2.5
            node["font"] = { "color" : "#ddd", "multi": True }
            node["shadow"] = { "enabled": True, "color": 'rgba(0, 0, 0, 0.12)',	"size": 10, "x": 5, "y": 5	}
            node["label"] = name
            node["color"] = { "border" : "#2e6da4", "background" : color, "highlight" : { "background" : "#2a2a2a" }, "hover" : { "background" : color } }
            node["size"] = size
        else:
            if dashboardItem["x"] != flowchartOperators[dashboardID]["node"]["x"] or dashboardItem["y"] != flowchartOperators[dashboardID]["node"]["y"]:
                node["x"] = dashboardItem["x"]
                node["y"] = dashboardItem["y"]
            if name != flowchartOperators[dashboardID]["name"]:
                node["label"] = name
            if color != flowchartOperators[dashboardID]["node"]["color"]["background"]:
                try:
                    node["image"] = getIcon(monitorItemsDict[dashboardItem["monitorId"]]["itemType"],up)
                    if node["image"] == None:
                        del node["image"]
                except KeyError:
                    pass
                node["color"] = { "border" : "#2e6da4", "background" : color, "highlight" : { "background" : "#2a2a2a" }, "hover" : { "background" : color } }
            if size != flowchartOperators[dashboardID]["node"]["size"]:
                node["size"] = size
        if node:
            flowchartResponse["operators"][flowchartResponseType][dashboardID] = { "_id" : dashboardID, "flowID" : dashboardID, "name" : name, "node" : node }

        # Do any links need to be created
        linkPopList = []
        for linkKey, linkValue in dashboard.monitorLinks.items():
            if linkKey not in flowchartLinks.keys():
                if linkValue["to"] in flowchartOperators and linkValue["from"] in flowchartOperators:
                    flowchartResponse["links"]["create"][linkKey] = { "from" : linkValue["from"], "to" : linkValue["to"], "color" : "#3dbeff" }
                else:
                    linkPopList.append(linkKey)
            elif flowchartLinks[linkKey]["color"] != color:
                flowchartResponse["links"]["update"][linkKey] = { "from" : linkValue["from"], "to" : linkValue["to"], "color" : "#3dbeff" }
        for link in linkPopList:
            del dashboard.monitorLinks[link]

    # Checking for deleted operators
    for flowchartOperator in flowchartOperators:
        if flowchartOperator not in dashboard.dashboardLayout:
            flowchartResponse["operators"]["delete"][flowchartOperator] = { "flowID" : flowchartOperator }
    # Checking for deleted links
    for flowchartLink in flowchartLinks.keys():
        if flowchartLink not in dashboard.monitorLinks:
            flowchartResponse["links"]["delete"][flowchartLink] = { "linkName" : flowchartLink }

    return flowchartResponse, 200

@pluginPages.route("/monitor/dashboard/<dashboardID>/<dashboardObjectId>/", methods=["DELETE"])
def dashboardDeleteMonitorItem(dashboardID,dashboardObjectId):
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
    else:
        return {},404
    del dashboard.dashboardLayout[dashboardObjectId]
    dashboard.update(["dashboardLayout"])
    return { }, 200

@pluginPages.route("/monitor/dashboard/<dashboardID>/move/<dashboardObjectId>/<x>/<y>/", methods=["POST"])
def dashboardMoveMonitorItem(dashboardID,dashboardObjectId,x,y):
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
    else:
        return {},404
    dashboard.dashboardLayout[dashboardObjectId]["x"] = int(x)
    dashboard.dashboardLayout[dashboardObjectId]["y"] = int(y)
    dashboard.update(["dashboardLayout"])
    return { }, 200

@pluginPages.route("/monitor/dashboard/<dashboardID>/add/<itemID>/<x>/<y>/", methods=["PUT"])
def dashboardAddMonitorItem(dashboardID,itemID,x,y):
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
    else:
        return {},404
    dashboardObjectId = str(uuid.uuid4())
    dashboard.dashboardLayout[dashboardObjectId] = { "id" : dashboardObjectId, "monitorId" : itemID, "x" : x, "y" : y }
    dashboard.update(["dashboardLayout"])
    return { }, 200

@pluginPages.route("/monitor/items/", methods=["GET"])
def getMonitorObjects():
    monitorItems = monitor._monitor().query(sessionData=jimi.api.g.sessionData,query={},fields=["name"])
    return monitorItems, 200

@pluginPages.route("/monitor/dashboard/<dashboardID>/link/<dashboardObjectFrom>/<dashboardObjectTo>/", methods=["PUT"])
def dashboardLinkMonitorItems(dashboardID,dashboardObjectFrom,dashboardObjectTo):
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
    else:
        return {},404
    linkID = "{0}->{1}".format(dashboardObjectFrom,dashboardObjectTo)
    dashboard.monitorLinks[linkID] = { "id" : linkID, "from" : dashboardObjectFrom, "to" : dashboardObjectTo }
    dashboard.update(["monitorLinks"])
    return { }, 200

@pluginPages.route("/monitor/dashboard/<dashboardID>/link/<dashboardObjectFrom>/<dashboardObjectTo>/", methods=["DELETE"])
def dashboardDeleteLink(dashboardID,dashboardObjectFrom,dashboardObjectTo):
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
    else:
        return {},404
    linkID = "{0}->{1}".format(dashboardObjectFrom,dashboardObjectTo)
    del dashboard.monitorLinks[linkID]
    dashboard.update(["monitorLinks"])
    return { }, 200

@pluginPages.route("/monitor/add/<itemName>/<itemType>/<itemStatus>/", methods=["GET"])
def monitorItemCreate(itemName,itemType,itemStatus):
    monitorItem = monitor._monitor().getAsClass(jimi.api.g.sessionData,query={"name" : itemName})
    if len(monitorItem) > 0:
        monitorItem = monitorItem[0]
        monitorItem.itemType=itemType
        monitorItem.up = True
        if itemStatus == "0":
            monitorItem.up = False
        monitorItem.update(["up","itemType"])
        return { }, 200
    else:
        monitor._monitor().new({"ids" : [ { "accessID" : jimi.api.g.sessionData["primaryGroup"], "read" : True, "write" : True, "delete" : True }]},itemName,itemStatus,itemType)
        return { }, 201
    return { }, 404

@pluginPages.route("/monitor/dashboard/<dashboardID>/size/<dashboardObjectId>/<size>/", methods=["POST"])
def dashboardSizeMonitorItem(dashboardID,dashboardObjectId,size):
    dashboard = monitor._monitorWebDashboard().getAsClass(jimi.api.g.sessionData,id=dashboardID)
    if len(dashboard) == 1:
        dashboard = dashboard[0]
    else:
        return {},404
    try:
        if size == "+":
            dashboard.dashboardLayout[dashboardObjectId]["size"] += 10
        elif size == "-":
            dashboard.dashboardLayout[dashboardObjectId]["size"] -= 10
    except KeyError:
        dashboard.dashboardLayout[dashboardObjectId]["size"] = 25
    dashboard.update(["dashboardLayout"])
    return { }, 200