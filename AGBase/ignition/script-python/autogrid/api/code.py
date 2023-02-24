from autogrid.monitoring import call_pd

AG_TS_FORMAT="yyyy-MM-dd'T'HH:mm:ss'Z'"
AG_BATCH_TS_FORMAT="yyyy-MM-dd' 'HH:mm:ss.S'Z'"
AG_DROMS_TS_FORMAT="yyyy-MM-dd'T'HH:mm:ssZ"
TS_API_SECONDS=300


def get_utc_offset():
	'''
	return our local system's offset from UTC
	'''
	date = system.date.now()
	return int(-1 * system.date.getTimezoneOffset(date))


def increment_tenant_api_fault(tenant, message=""):
	'''
	Increment counter tag indicating flex API call failure at the tenant level
	'''
	path="[default]"+tenant+"/ErrorTracking/FlexAPICallFailed"
	
	value=system.tag.readBlocking([path])[0].value
	system.tag.writeBlocking([path], [value+1])
	call_pd('flex_api', 'tenant_api_failure', "Failure calling tenant level Flex API: "+message, "trigger")


def increment_events_api_fault(tenant, message=""):
	'''
	Increment counter tag indicating flex API call failure at the tenant level
	'''
	path="[default]"+tenant+"/ErrorTracking/EventAPICallFailed"
	
	value=system.tag.readBlocking([path])[0].value
	system.tag.writeBlocking([path], [value+1])
	call_pd('events_api', 'events_api_failure', "Failure calling events API: "+message, "trigger")


def get_params(tenant):
	'''
	Get the Flex endpoint parameters including a new auth token for the given tenant and return them in a dictionary
	'''
	base="[default]AutoGrid/TenantCredentials"
	
	vals=system.tag.readBlocking(
		[base+"/"+tenant+"/Flex_TS_API_Password", 
		base+"/"+tenant+"/Flex_TS_API_Username", 
		base+"/"+tenant+"/Flex_API_URL", 
		base+"/"+tenant+"/Flex_FERM_API_Token",
		base+"/"+tenant+"/DROMS_API_Username",
		base+"/"+tenant+"/DROMS_API_Password",
		base+"/"+tenant+"/DROMS_API_URL",
		base+"/"+tenant+"/DROMS_Meta_API_Username",
		base+"/"+tenant+"/DROMS_Meta_API_Password"
		])

	return {
		"url": vals[2].value, 
		"ts_user": vals[1].value, 
		"ts_pass": vals[0].value, 
		"ferm_token": vals[3].value, 
		"droms_user": vals[4].value, 
		"droms_pass": vals[5].value, 
		"droms_url": vals[6].value,
		"fer_meta_user": vals[7].value,
		"fer_meta_pass": vals[8].value,
		} 


def get_resource_status(tenant, resource):
	'''	
	Return whether or not the given resource is available (true/false)
	
	url="https://dev-internal.ks.autogridsystems.net/fermanager/1.0/predictive_controls_dev/state/Hospital_Battery_02"
	ferm_token="token"
	tenant="predictive_controls_dev"
	
	client = system.net.httpClient()
	
	response=client.get(url, headers={"Authorization": "Token "+ferm_token, "Content-Type": "application/json"}).json
	
	print response
	
	'''
	logger=system.util.getLogger("Flex API Client")
	params=get_params(tenant)
	
	url = params["url"]+"/fermanager/1.0/"+tenant+"/state/"+resource
	client = system.net.httpClient()
	
	response=None
	
	try:
		response=client.get(url, headers={"Authorization": "Token "+params["ferm_token"], "Content-Type": "application/json"})
		if response.good and response.json['name'] == "AVAILABLE":
			return True
		else:
			logger.error("Bad return status from fermanager state API: "+response.data)
			increment_tenant_api_fault(tenant)
	except Exception as ex:
		logger.error("Calling FER Manager Health API: "+str(response))
		increment_tenant_api_fault(tenant)

	increment_tenant_api_fault(tenant)
	return False


def get_latest_value_detail(tenant, resource, stream_type):
	'''
	Get the latest value and timestamp for the given stream on the given resource in the given tenant returned as a dictionary {"value": 1234.5, "ts": timestamp}
	eg: autogrid.api.get_latest_value("predictive_controls_dev", "Hospital_Battery_02", "GEN_POWER_ACTUAL")
	'''
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	url=params["url"]
	
	start=system.date.format( system.date.addSeconds( system.date.addHours(system.date.now(), get_utc_offset()), -TS_API_SECONDS), AG_TS_FORMAT )
	end=system.date.format( system.date.addHours(system.date.now(), get_utc_offset()), AG_TS_FORMAT )
	
	resp=None
	client = system.net.httpClient()
	try:
		response = client.get(url+"/connectors/timeseries/api/v1/telemetry/"+tenant+"/"+resource+"/?start_utc="+start+"&end_utc="+end+"&measurement-names=[%22"+stream_type+"%22]", 
			username=params["ts_user"],
			password=params["ts_pass"],
			headers={"Content-Type": "application/json"})
			
		if response.good:
			resp=response.json
		else:
			logger.error("Unable to fetch timeseries value: "+response.data)
			increment_tenant_api_fault(tenant, "Unable to fetch timeseries value: "+response.data)
			return None
	except Exception as ex:
		raise
		logger.error("Exception getting telemetry")
		logger.error(str(ex))
		increment_tenant_api_fault(tenant)
		return None
	
	value=None
	ts=None
	
	for item in resp["data"]:
		this_ts=system.date.parse(item["timestamp_utc"], AG_TS_FORMAT)
		if ts is None or system.date.isAfter(this_ts, ts):
			ts=this_ts
			value=float(item["measurements"][0]["value"])
	
	return {"value": value, "ts": ts}


def get_latest_value(tenant, resource, stream_type):
	return get_latest_value_detail(tenant, resource, stream_type)['value']


def start_scalar_dr_event( tenant, utility_program_uid, start_time, end_time, shed_kW):
	'''
	Start a DR event given the tenant, program UID, start time, end time, and target shed kW
	returns event UID on success, None on failure
	
	throws exception or returns event-identifier
	
	autogrid.api.start_scalar_dr_event( "afc-storage-2", system.date.addHours(system.date.now(), 1), system.date.addHours(system.date.now(), 2), 10)
	''' 
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	url=params["droms_url"]
	
	payload = {
		"utility_program_uid": utility_program_uid,
		"start_time": system.date.format( start_time, AG_DROMS_TS_FORMAT ),
		"end_time": system.date.format( end_time, AG_DROMS_TS_FORMAT ),
		"flexibility_commitments": [
		  {
		    "start_time": system.date.format( start_time, AG_DROMS_TS_FORMAT ),
		    "end_time": system.date.format( end_time, AG_DROMS_TS_FORMAT ),
		    "target_power": shed_kW
		  }
		 ]
		}
	
	try:
		client = system.net.httpClient()
		result=client.post(url+"/api/v2/dr_events", data=system.util.jsonEncode(payload), headers={"Content-Type": "application/json"}, username=params['droms_user'], password=params['droms_pass'])
		
		if not result.good:
			logger.error("Error creating DROMS event: "+result.text)
			increment_events_api_fault(tenant)
			return None
		else:
			logger.info("Created DROMS event for program "+utility_program_uid+" with ID "+result.json['event-identifier'])
			return result.json['event-identifier']
	except Exception as ex:
		logger.error("Exception creating event for program "+utility_program_uid)
		increment_events_api_fault(tenant)
		return None


def end_dr_event(tenant, event_identifier):
	'''
	End a DR event given the tenant and event identifier
	
	return whether or not the event was cancelled	
	''' 
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	url=params["droms_url"]
	
	payload = {
		"utility_dr_event_uid": event_identifier
		}
		
	client = system.net.httpClient()
	
	try:
		result=client.post(
			url+"/api/v1/dr_events/cancel", 
			data=payload, 
			headers={"Content-Type": "application/json"}, 
			username=params['droms_user'], password=params['droms_pass'])
		
		if not result.good:
			logger.error("Error cancelling DROMS event: "+result.text)
			increment_tenant_api_fault(tenant)
			return False
		else:
			return True
	except Exception as ex:
		logger.error("Exception canceling event iD "+event_identifier)
		increment_events_api_fault(tenant)
		return None


def get_devices_in_pool(tenant, pool_id):
	'''
	Given a tenant and pool, return an array of the resources in the pool (but not the pool itself)
	'''
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	
	url = params["droms_url"]+"/api/v1/fer_metadata/"+tenant+"/resources/"+pool_id
	request_params={
		"resource_type": "program",
		"depth": 3,
		"active_on": system.date.format( system.date.now(), AG_TS_FORMAT )
		}
	
	client = system.net.httpClient()
	
	response=None
	retval=[]
	
	try:
		response=client.get(url, params=request_params, username=params['fer_meta_user'], password=params['fer_meta_pass'])
		if response.good:
			for resource in response.json['resources']:
				if resource['identifier'] != pool_id and resource['resource_type'] == 'device':
					retval.append(resource)
		else:
			logger.error("Error getting resources in pool "+response.text)
			increment_tenant_api_fault(tenant, "Error getting resources in pool "+response.text)
	except Exception as ex:
		logger.error("Exception getting resources in pool")
		increment_tenant_api_fault(tenant)
		
	return retval


def get_pool_info(tenant, pool_id):
		'''
		Given a tenant and pool, return an array of pool metadata
		'''
		logger = system.util.getLogger("AutoGrid API Client")
		params=get_params(tenant)
		
		url = params["droms_url"]+"/api/v1/fer_metadata/"+tenant+"/resources/"+pool_id
		request_params={
			"resource_type": "program",
			"depth": 3,
			"active_on": system.date.format( system.date.now(), AG_TS_FORMAT )
			}
		
		client = system.net.httpClient()
		
		response=None
		retval=[]
		
		try:
			response=client.get(url, params=request_params, username=params['fer_meta_user'], password=params['fer_meta_pass'])
			if response.good:
				for resource in response.json['resources']:
					if resource['identifier'] == pool_id:
						return resource
			else:
				logger.error("Error getting pool info "+response.text)
				increment_tenant_api_fault(tenant, "Error getting pool info "+response.text)
		except Exception as ex:
			logger.error("Exception getting resources in pool")
		
		increment_tenant_api_fault(tenant)
		return None

def get_pool_aggregate(tenant, pool_id, device_type, stream, source="api"):
	'''
	Given a tenant and pool, get the current sum of the telemetry values for the given stream type for each device of type device_type in the pool
	
	ex: get_pool_aggregate("predictive_controls_dev", "afc-storage-2", "der_battery_storage", "GEN_POWER_ACTUAL")
	'''
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
		
	device_ids=[]
	for device in get_devices_in_pool(tenant, pool_id):	
		if device['params']['device_model'] == device_type:
			device_ids.append(device['identifier'])
	
	if source == 'api':
		start=system.date.format( system.date.addSeconds( system.date.addHours(system.date.now(), get_utc_offset()), -TS_API_SECONDS), AG_TS_FORMAT )
		end=system.date.format( system.date.addHours(system.date.now(), get_utc_offset()), AG_TS_FORMAT )
		
		total=0.0
		for tuple in get_batch_measurements(tenant, start, end, device_ids, stream).values():
			total+=tuple['value']
		
		return total
	elif source == 'kafka':
		paths=[]
		for device in device_ids:
			path="[AutoGrid Kafka]"+tenant+"/"+device+"/"+stream
			paths.append(path)
		
		total=0.0
		for value in system.tag.readBlocking(paths):
			if value.quality.isGood():
				total+=value.value
		return total


def get_batch_measurements(tenant, start, end, device_ids, stream):
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	
	values={}
	
	ts_params={
		"tenant_uid": tenant,
		"start_date": start,
		"end_date": end,
		"device_identifiers": device_ids,
		"stream_type": stream	
		}
	
	url=params['url']
	client=system.net.httpClient()
	
	response=None
	try: 
		response = client.post(url+"/connectors/timeseries/api/v1/device_data/batch_retrieve/", 
			data=system.util.jsonEncode(ts_params),
			username=params["ts_user"],
			password=params["ts_pass"],
			headers={"Content-Type": "application/json"})
	except Exception as ex:
		logger.error("Exception getting batch telemetry")
		increment_tenant_api_fault(tenant)
		
		return values
	
	if response.good:
		for item in response.json["data"]:
			if item['stream_type'] == stream:
				value=None
				ts=None
				
				for record in item['time_series_values']:
					this_ts=system.date.parse(record["datetime"], AG_BATCH_TS_FORMAT)
					if ts is None or system.date.isAfter(this_ts, ts):
						ts=this_ts
						value=float(record["value"])
						
				if value is not None:
					values.update({item['device_identifier']: {'ts': ts, 'value': value}})
			
		return values
	else:
		logger.error("Bulk TS API call failed: "+response.text)
		increment_tenant_api_fault(tenant)
		return values


def get_event_info(tenant, event_uid):
	'''
	Get the metadata associated with the given event, return the json object returned by Flex
	'''
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	url=params["droms_url"]
		
	client = system.net.httpClient()
	
	try:
		result=client.get(
			url+"/api/v1/dr_events/"+event_uid, 
			headers={"Content-Type": "application/json"}, 
			username=params['droms_user'], password=params['droms_pass'])
		
		if not result.good:
			logger.error("Error getting event info: "+result.text)
			increment_tenant_api_fault(tenant, "Error getting event info: "+result.text)
			return None
		else:
			return result.json
	except Exception as ex:
		logger.error("Exception getting event info")
		increment_events_api_fault(tenant)
		return None


def add_service_point( tenant, account, sp_uid, tz, custom_attributes=None):
	'''
	Add a service point to the specified account returning either an error message or update count as described in
	https://autogridsystems.atlassian.net/wiki/spaces/API/pages/52461861/Customer+Data+API#CustomerDataAPI-Servicepoints 
	
	eg:
	
	tenant="predictive_controls_dev"
	account="entergy"
	sp_uid="IGNITION_TEST_SP"
	tz="Pacific Time (US & Canada)"
	
	print autogrid.api.add_service_point( tenant, account, sp_uid, tz)
	''' 
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	url=params["droms_url"]
	
	# DROMS doesn't like spaces and some other chars
	sp_uid=sp_uid.replace(" ", "_")
	
	payload = {
		"accounts": [
			{
			"account_identifier": account,
			"service_points": [
				{
					"service_identifier": sp_uid,
					"service_time_zone": tz
				}
				]
			}
			]
		}
	
	if custom_attributes is not None:
		for key in custom_attributes:
			payload['accounts'][0]['service_points'][0][key] = custom_attributes[key]
	
	try:
		client = system.net.httpClient()
		result=client.post(url+"/api/v1/accounts", data=system.util.jsonEncode(payload), headers={"Content-Type": "application/json"}, username=params['droms_user'], password=params['droms_pass'])
		
		if not result.good:
			logger.error("Error creating service point: "+result.text+" with request "+system.util.jsonEncode(payload))
			#increment_events_api_fault(tenant)
			return None
		else:
			return result.text
	except Exception as ex:
		logger.error("Exception creating service point "+sp_uid)
		#increment_events_api_fault(tenant)
		return None


def add_update_device( tenant, account, sp_uid, device, model, proxy, custom_attributes=None):
		'''
		Add a device to the specified service point returning either an error message or update count as described in
		https://autogridsystems.atlassian.net/wiki/spaces/API/pages/52461861/Customer+Data+API#CustomerDataAPI-Devices(WIP)
		
		Device model short names: https://autogridsystems.atlassian.net/wiki/spaces/CSKBD/pages/812385080/Supported+Equipment+-+Models+Short+Names+and+Associated+Proxies 
		
		eg:
		
		tenant="predictive_controls_dev"
		account="entergy"
		sp_uid="IGNITION_TEST_SP"
		device="IGN_TESTDEV_001"
		model="Battery Storage"
		proxy="Autogrid Message Bus"
		
		print autogrid.api.add_device( tenant, account, sp_uid, device, model, proxy)
		''' 
		logger = system.util.getLogger("AutoGrid API Client")
		params=get_params(tenant)
		url=params["droms_url"]
		
		# DROMS doesn't like spaces and some other chars
		sp_uid=sp_uid.replace(" ", "_")
		
		payload = {
			"accounts": [
				{
				"account_identifier": account,
				"service_points": [
					{
						"service_identifier": sp_uid,
						"devices": [
							{
								"device_identifier": device,
								"device_model": model,
								"device_proxy": proxy
							}
						]
					}
					]
				}
				]
			}
			
		if custom_attributes is not None:
			for key in custom_attributes:
				payload['accounts'][0]['service_points'][0]['devices'][0][key] = custom_attributes[key]
		 
		try:
			client = system.net.httpClient()
			result=client.post(url+"/api/v1/accounts", data=system.util.jsonEncode(payload), headers={"Content-Type": "application/json"}, username=params['droms_user'], password=params['droms_pass'])
			
			if not result.good:
				logger.error("Error creating device: "+result.text+" with request "+system.util.jsonEncode(payload))
				#increment_events_api_fault(tenant)
				return None
			else:
				return result.text
		except Exception as ex:
			logger.error("Exception creating device: "+sp_uid)
			#increment_events_api_fault(tenant)
			return None


def create_program_subscription( tenant, program, resource, level="devices"):
	'''
	Add or Update a program subscription in DROMS
	https://autogridsystems.atlassian.net/wiki/spaces/API/pages/948699516/External+v3+APIs
	Note:
	Ah - I'll need different credentials for external?
	kdurski  6:16 AM
	not really
	6:16	just change the path to /api/v3/internal/XXX
	6:16	and pass X-Tenant header
	6:16	and in 95%+ cases it will work
		
	eg:
	
	tenant="predictive_controls_dev"
	resource="ign_test_tstat"
	program="ign_test_dlc"
	
	print autogrid.api.create_program_subscription( tenant, program, resource)
	
	subscription level (level parameter) is devices by default, can also be accounts or (?? for service points)
	''' 	
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	url=params["droms_url"]
	
	start=system.date.format(system.date.now(), "YYYY-MM-dd")
	end="2030-05-01"
	
	# DROMS doesn't like spaces and some other chars
	resource=resource.replace(" ", "_")
	
	payload={
		"data": {
	    	"type": "subscriptions",
	    	"attributes": {
	      		"start_date": start,
	      		"end_date": end,
	      		"resource_id": resource,
	      		"resource_type": level,
	      		"program_id": program,
	      		"subscription_type": "Primary",
	      		#"parent_subscription_id": "null"
	    	}
	  	}
	}
		
	try:
		client = system.net.httpClient()
		result=client.post(url+"/api/v3/subscriptions", data=system.util.jsonEncode(payload), headers={"Accept": "application/vnd.api+json", "Content-Type": "application/vnd.api+json", "X-Tenant": tenant}, username=params['droms_user'], password=params['droms_pass'])
		
		if not result.good:
			logger.error("Error creating program subscription: "+result.text+" with request "+system.util.jsonEncode(payload))
			#increment_events_api_fault(tenant)
			return None
		else:
			return result.text
	except Exception as ex:
		logger.error("Exception managing program subscription "+sp_uid)
		#increment_events_api_fault(tenant)
		return None


def get_servicepoint_details( tenant, service_point_name):
	'''
	This function given a tenant and name of a service point 
	queries an api to return the values of a given custom attribute
	''' 	
	logger = system.util.getLogger("AutoGrid API Client")
	params=get_params(tenant)
	url=params["droms_url"]
	
	headers = {
		'Accept': 'application/vnd.api+json',
		'Content-Type': 'application/vnd.api+json'
	}
	try:
		client = system.net.httpClient()

		result=client.get(
			url+"/api/v3/service_points/"+service_point_name,
			headers=headers,
			username=params['droms_user'],
			password=params['droms_pass']
		)

		if not result.good:
			logger.error("Error querying service point details for "+ service_point_name + " : " +result.text)
			return None
		else:
			return result.text
	except Exception as ex:
		logger.error("Exception querying service point details "+service_point_name)
		return None


def get_servicepoint_custom_attribute( tenant, service_point_name, attribute):
	'''
	This function given a tenant, service point name, and custom attribute, 
	queries an api to return the value of a given custom
	attribute within a particular service point
	'''
	return system.util.jsonDecode(get_servicepoint_details( tenant, service_point_name))['data']['attributes']['custom_attributes'][attribute]
#	return system.util.jsonDecode(get_servicepoint_details( tenant, service_point_name))['data']['attributes']['custom_attributes']
#	info=system.util.jsonDecode(get_servicepoint_details( tenant, service_point_name))
#	ds=[]
#	for name,value in info['data']['attributes']['custom_attributes'].items():
#		ds += [value]
#	return ds
