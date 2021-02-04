// Globals
var mouseOverOperator;
var mouseHold;
var cKeyState
var loadedFlows = {};
var pauseFlowchartUpdate = false;
var lastUpdatePollTime = 0;

// visjs
var nodes = [];
var edges = [];
var network = null;
var nextId = 0;

// jimi
var flowObjects = {};
var nodeObjects = {};
var flowLinks = {};
var selectedObject = null;
var processlist = {};
var init = false;

$(document).ready(function () {
	setupFlowchart();
	
	// Key events
	$(document).keydown(function(event) {
		switch (String.fromCharCode(event.which).toLowerCase()) {
			case 'c':
				cKeyState = true;
				break;
		}
	});
	$(document).keyup(function( event ) {
		// Really it needs to detect the object its on e.g. operator or link not just anything but the few listed
		if (event.keyCode == 46 && document.activeElement.type != "text" && document.activeElement.type != "checkbox" && document.activeElement.type != "textarea") {
			deleteSelected();
		}
		cKeyState = false;
	});
});

function autoupdate() {
	setTimeout(updateFlowchart, 2500);
}

function deleteSelected() {
	selectedNodes = network.getSelectedNodes()
	if (selectedNodes.length == 1) {
		node = nodeObjects[selectedNodes[0]]["flowID"]
		if (confirm("Are you sure you want to remove object '"+ node +"' from this conduct?")) {
			var dashboardID = GetURLParameter("dashboardID");
			$.ajax({url:"/plugin/monitor/dashboard/"+dashboardID+"/"+node+"/", data: JSON.stringify({ CSRF: CSRF }), type:"DELETE", contentType:"application/json", success: function ( responseData ) {
					deleteNode(node)
				}
			});
		}
	}

	links = network.getSelectedEdges()
	if (links.length == 1) {
		link = flowLinks[links[0]]
		var dashboardID = GetURLParameter("dashboardID");
		var to = link["to"]
		var from = link["from"]
		$.ajax({url:"/plugin/monitor/dashboard/"+dashboardID+"/link/"+from+"/"+to+"/", data: JSON.stringify({ CSRF: CSRF }), type:"DELETE", contentType:"application/json", success: function ( responseData ) {
				deleteLink(from,to)
			}
		});
	}
}

function updateNode(flow) {
	if (flow["flowID"] in flowObjects == false) {
		flowObjects[flow["flowID"]] = { "flowID": flow["flowID"], "flowType": flow["flowType"], "nodeID": nextId, "_id": flow["_id"], "name" : flow["name"], "node" : flow["node"] }
		nodeObjects[nextId] = { "flowID": flow["flowID"], "nodeID": nextId }
		flowObjects[flow["flowID"]]["node"]["id"] = nextId
		nodes.add(flowObjects[flow["flowID"]]["node"])
		nextId++;
	} else {
		flow["node"]["id"] = flowObjects[flow["flowID"]]["nodeID"]
		if ( "name" in flow ) {
			flowObjects[flow["flowID"]]["name"] = flow["name"]
		}
		if (("x" in flow["node"] || "y" in flow["node"]) && ("color" in flow["node"] == false) && ("label" in flow["node"] == false)) {
			flowObjects[flow["flowID"]]["node"]["x"] = flow["node"]["x"]
			flowObjects[flow["flowID"]]["node"]["y"] = flow["node"]["y"]
			network.moveNode(flowObjects[flow["flowID"]]["nodeID"],flow["node"]["x"],flow["node"]["y"])
		} else {
			if ("x" in flow["node"] || "y" in flow["node"]) {
				flowObjects[flow["flowID"]]["node"]["x"] = flow["node"]["x"]
				flowObjects[flow["flowID"]]["node"]["y"] = flow["node"]["y"]
			}
			if ("color" in flow["node"]) {
				flowObjects[flow["flowID"]]["node"]["color"] = flow["node"]["color"]
			}
			if ("label" in flow["node"]) {
				flowObjects[flow["flowID"]]["node"]["label"] = flow["node"]["label"]
			}
			nodes.update(flow["node"])
		}
	}
}

function deleteNode(flowID) {
	nodes.remove({ id: flowObjects[flowID]["nodeID"] })
	delete nodeObjects[flowObjects[flowID]["nodeID"]]
	delete flowObjects[flowID]
}

function createLinkRAW(from,to,color) {
	var linkName = from + "->" + to;
	flowLinks[linkName] = { "from": from, "to": to, "color": color }
	edges.add({ 
		id: linkName,
		from: flowObjects[from]["nodeID"], 
		to: flowObjects[to]["nodeID"],
		color: {
			color: color
		},
		arrows: {
			middle: {
			  enabled: true,
			  type: "arrow"
			}
		},
		smooth: {
			enabled: true,
			type: "cubicBezier",
			roundness: 0.7
		},
		width: 1.5
	 });
	nextId++;
}

function updateLink(from,to,color) {
	var linkName = from + "->" + to;
	flowLinks[linkName]["from"] = from
	flowLinks[linkName]["to"] = to
	flowLinks[linkName]["color"] = color
	edges.update({ 
		id: linkName,
		from: flowObjects[from]["nodeID"], 
		to: flowObjects[to]["nodeID"],
		color: color
	});
	return true;
}

function deleteLink(from,to) {
	var linkName = from + "->" + to;
	edges.remove({ 
		id: linkName
	});
	delete flowLinks[linkName]
}

function createLink(from,to,colour,save) {
	if (from == to) {
		var dashboardID = GetURLParameter("dashboardID")
		$.ajax({url:"/plugin/monitor/dashboard/"+dashboardID+"/link/"+from+"/"+to+"/", type:"DELETE", contentType:"application/json"});
		return false
	}

	if (save) {
		if (saveNewLink(from,to)) {
			if (createLinkRAW(from,to,colour)) {
				return true;
			} else {
				//$.ajax({url:"/conductEditor/"+conductID+"/flowLink/"+from+"/"+to+"/", type:"DELETE", contentType:"application/json"});
				return false
			}
		};
	} else {
		var conductID = GetURLParameter("conductID")
		if (createLinkRAW(from,to,colour)) {
			return true;
		} else {
			//$.ajax({url:"/conductEditor/"+conductID+"/flowLink/"+from+"/"+to+"/", type:"DELETE", contentType:"application/json"});
			return false
		}
	}
	return false;
}

function saveNewLink(from,to) {
	var dashboardID = GetURLParameter("dashboardID")
	$.ajax({url:"/plugin/monitor/dashboard/"+dashboardID+"/link/"+from+"/"+to+"/", data: JSON.stringify({ CSRF: CSRF }), type:"PUT", contentType:"application/json", success: function ( responseData ) {
			return true;
		}
	});
}

function updateFlowchartNonBlocking(blocking) {
	nonlock = 0
	// Operator Updates
	for (operator in processlist["operators"]["update"]) {
		updateNode(processlist["operators"]["update"][operator]);
		delete processlist["operators"]["update"][operator]
		nonlock++
		if ((!blocking) && (nonlock > 0)) {
			setTimeout(function() { updateFlowchartNonBlocking() }, 10);
			return
		}
	}
	// Operator Creates
	for (operator in processlist["operators"]["create"]) {
		updateNode(processlist["operators"]["create"][operator]);
		delete processlist["operators"]["create"][operator]
		nonlock++
		if ((!blocking) && (nonlock > 0)) {
			setTimeout(function() { updateFlowchartNonBlocking() }, 10);
			return
		}
	}
	// Operator Deletions
	for (operator in processlist["operators"]["delete"]) {
		obj = processlist["operators"]["delete"][operator]
		deleteNode(obj["flowID"]);
		delete processlist["operators"]["delete"][operator]
		nonlock++
		if ((!blocking) && (nonlock > 0)) {
			setTimeout(function() { updateFlowchartNonBlocking() }, 10);
			return
		}
	}
	// Link Creates
	for (link in processlist["links"]["create"]) {
		obj = processlist["links"]["create"][link]
		createLinkRAW(obj["from"],obj["to"],obj["color"])
		delete processlist["links"]["create"][link]
		nonlock++
		if ((!blocking) && (nonlock > 0)) {
			setTimeout(function() { updateFlowchartNonBlocking() }, 10);
			return
		}
	}
	// Link Updates
	for (link in processlist["links"]["update"]) {
		obj = processlist["links"]["update"][link]
		updateLink(obj["from"],obj["to"],obj["color"])
		delete processlist["links"]["update"][link]
		nonlock++
		if ((!blocking) && (nonlock > 0)) {
			setTimeout(function() { updateFlowchartNonBlocking() }, 10);
			return
		}
	}
	// Link Deletions
	for (link in processlist["links"]["delete"]) {
		obj = processlist["links"]["delete"][link]
		linkName = obj["linkName"]
		edges.remove({ 
			id: linkName
		});
		delete flowLinks[linkName]
		delete processlist["links"]["delete"][link]
		nonlock++
		if ((!blocking) && (nonlock > 0)) {
			setTimeout(function() { updateFlowchartNonBlocking() }, 10);
			return
		}
	}
}

function updateFlowchart() {
	if ((processlist) || (processlist.length == 0)) {
		var dashboardID = GetURLParameter("dashboardID")
		$.ajax({url:"/plugin/monitor/dashboard/"+dashboardID+"/", type:"POST", timeout: 2000, data: JSON.stringify({ lastPollTime : lastUpdatePollTime, operators: flowObjects, links: flowLinks, CSRF: CSRF }), contentType:"application/json", success: function ( responseData ) {
				processlist = responseData
				setTimeout(updateFlowchart, 2500);
				if (init == false) {
					if (nodes.length > 0) {
						init = true;
						network.fit()
					}
					updateFlowchartNonBlocking(true);
					setTimeout(function() { updateFlowchartNonBlocking(true) }, 10);
				} else {
					setTimeout(function() { updateFlowchartNonBlocking(false) }, 10);
				}
				if (nodes.length > 0) {
					if (init == false) {
						init = true;
						network.fit()
					}
				}
			},
			error: function ( error ) {
				console.log("Unable to update flowChart");
				setTimeout(updateFlowchart, 2500);
			}
		});
	} else {
		setTimeout(updateFlowchart, 2500);
	}
}

function setupFlowchart() {
	var container = document.getElementById("flowchart");
	nodes = new vis.DataSet([]);
	edges = new vis.DataSet([]);
	var data = {
		nodes: nodes,
		edges: edges
	};
	var options = {
		physics: {
			enabled: false
		},
		layout : {
			improvedLayout: false
		},
		interaction: {
			multiselect: true,
			hover: false
		},
	};
	network = new vis.Network(container, data, options);

	network.on("dragEnd", function(params) {
		if (params["nodes"].length > 0) {
			pos = network.getPositions(params["nodes"]);
			var dashboardID = GetURLParameter("dashboardID")
			for (node in params["nodes"]) {
				// Slow need to allow batch updates in future in the backend
				$.ajax({url:"/plugin/monitor/dashboard/"+dashboardID+"/move/"+nodeObjects[params["nodes"][node]]["flowID"]+"/"+pos[params["nodes"][node]]["x"]+"/"+pos[params["nodes"][node]]["y"]+"/", type:"POST", data: JSON.stringify({ CSRF: CSRF }), contentType:"application/json", success: function( responseData ) {
					}
				});
			}
		}
		return false;
	});

	network.on("click", function(params) {
		if (selectedObject != null)
		{
			if (selectedObject[1].hasOwnProperty("deselect")) {
				selectedObject[1]["deselect"]()
			}
		}
		if (params["nodes"].length == 1) {
			if (cKeyState) {
				if (selectedObject[0] == "flowObject")
				{
					createLink(selectedObject[1],nodeObjects[params["nodes"][0]]["flowID"],"#3dbeff",true);
				}
			}
			selectedObject = ["flowObject",nodeObjects[params["nodes"][0]]["flowID"]]
		} else {
			selectedObject = null;
		}
		return true;
	});

	network.on("doubleClick", function(params) {
		if (params["nodes"].length == 1) {
			//createPropertiesPanel(nodeObjects[params["nodes"][0]]["flowID"]);
		}
		if ((params["nodes"].length == 0) && (params["edges"].length == 1)) {
			link = flowLinks[params["edges"][0]]
			to = link["to"]
			from = link["from"]
			//createLinkPropertiesPanel(from,to);
		}
		return true;
	});

	updateFlowchart();
}

