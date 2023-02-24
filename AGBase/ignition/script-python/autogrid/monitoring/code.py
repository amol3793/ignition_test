PD_KEY_PATH="[default]AutoGrid/PagerDutyServiceKey"

OPC_ALERTING_PATH="[default]AutoGrid/Monitoring/AlertingOPCConnections"
DEVICE_ALERTING_PATH="[default]AutoGrid/Monitoring/AlertingDevices"

OPC_ALERTS_ENABLED="[default]AutoGrid/Monitoring/AlertEnabledOPCConnections"
DEVICE_ALERTS_ENABLED="[default]AutoGrid/Monitoring/AlertEnabledDevices"


def call_pd(type, key, message, action):
	'''
	action can be trigger, acknowledge, or resolve
	'''
	if not system.tag.exists("[default]AutoGrid/PagerDutyServiceKey"):
		return
	pd_key=system.tag.readBlocking([PD_KEY_PATH])[0].value
	
	if pd_key is None or pd_key == "":
		return
	
	url="https://events.pagerduty.com/v2/enqueue"
	gwname=system.tag.readBlocking(["[System]Gateway/SystemName"])[0].value
	logger=system.util.getLogger("PagerDuty Client")
	
	payload = {
		"payload": {
			"summary": gwname+": "+message,
			"timestamp": system.date.format(system.date.now(), "YYYY-MM-dd'T'HH:mm:ss.SZ"),
			"severity": "critical",
			"source": gwname,
			"component": "SCADA",
			"group": "prod-datapipe",
			#"class": "disk",
			"custom_details": { }
		},
		"routing_key": pd_key,
		"dedup_key": gwname+"/"+type+"/"+key,
		"event_action": action,
		"client": "Ignition Events",
		"client_url": "",
		"links": [],
		"images": []
	}
		
	client = system.net.httpClient()
	try:
		response = client.post(url, data=system.util.jsonEncode(payload), headers={"Content-Type": "application/json"})
		if response.good:
			resp=response.json
		else:
			logger.error("Unable to manage PD event: "+response.data)
	except Exception as ex:
		logger.error("Exception managing PD event")
		logger.warn(str(sys.exc_info()))


def create_pd_event(type, key, message):
	'''
	Create a pagerduty incident with the given type (eg: device), key (eg: device ID), and message
	'''
	call_pd(type, key, message, "trigger")


def resolve_pd_event(type, key, message):
	'''
	Create a pagerduty incident with the given type (eg: device), key (eg: device ID), and message
	'''
	call_pd(type, key, message, "resolve")


def check_device(device_name):
	'''
	For the device path given, eg AAT_FQ_Meter, if the Enabled bit is on then 
	check that the Status is "Connected" and emit an event if it is not 
	'''
	active_alerts=system.tag.readBlocking([DEVICE_ALERTING_PATH])[0].value
	
	values=system.tag.readBlocking(["[System]Gateway/Devices/"+device_name+"/Enabled", "[System]Gateway/Devices/"+device_name+"/Status"])
	if values[0].value:
		if values[1].value != "Connected":
			if device_name not in active_alerts:
				create_pd_event("device", device_name, "SCADA Device " + device_name + " is not connected. Status is "+values[1].value)
				active_alerts.append(device_name)
		else:
			if device_name in active_alerts:
				 resolve_pd_event("device", device_name, "SCADA Device " + device_name + " has re-connected")
				 active_alerts.remove(device_name)
		system.tag.writeBlocking([DEVICE_ALERTING_PATH], [active_alerts])


def check_opc(server):
	'''
	For the OPC connection name given, eg Some OPC UA Server, if the Enabled bit is on then 
	check that the Status is "CONNECTED" and emit an event if it is not connected
	'''
	active_alerts=system.tag.readBlocking([OPC_ALERTING_PATH])[0].value
	
	values=system.tag.readBlocking(["[System]Gateway/OPC/Connections/"+server+"/Enabled", "[System]Gateway/OPC/Connections/"+server+"/State"])
	if values[0].value:
		if values[1].value != "CONNECTED":
			if server not in active_alerts:
				create_pd_event("opcserver", server, "OPC Server " + server + " is not connected. Status is "+values[1].value)
				active_alerts.append(server)
		else:
			if server in active_alerts:
				 resolve_pd_event("opcserver", server, "OPC Server " + server + " has re-connected")
				 active_alerts.remove(device_name)
		system.tag.writeBlocking([OPC_ALERTING_PATH], [active_alerts])


def run_checks():
	'''
	Run checks on configured devices and OPC connections
	'''
	if system.tag.exists(OPC_ALERTS_ENABLED):
		for opc in system.tag.readBlocking([OPC_ALERTS_ENABLED])[0].value:
			check_opc(opc)
	
	if system.tag.exists(DEVICE_ALERTS_ENABLED):
		for device in system.tag.readBlocking([DEVICE_ALERTS_ENABLED])[0].value:
			check_device(device)