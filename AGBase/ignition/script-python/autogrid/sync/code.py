KAFKA_CREATE_PATH="[AutoGrid Kafka]_Meta/Control/CREATE"


def get_kafka_path(path, tag):
	'''
	Given an arbitrarily deep directory tree in a path path and tag name, return the path this would map to under the kafka tag provider (which is always one level deep)
	'''
	path_arr=path.replace("[default]", "").split("/")
	return "[AutoGrid Kafka]"+path_arr[0]+"/"+path_arr[-1]


def add_onchange_handler(source_path, tag_name, dest_path):
	'''
	Given a source_path to a tag and the name of the tag, set up an onChange handler 
	to transfer the tag to the dest_path (full tag name) on change. 
	'''
	system.tag.configure(source_path, {"name": tag_name, "eventScripts": [{"eventid":"valueChanged", "script": "\tif currentValue.quality.isGood():\n\t\tsystem.tag.writeBlocking([\""+dest_path+"\"], [currentValue])"}] }, "m")


def add_tag_to_kafka(tenant, device_name, tag_name):
	'''
	Given a tenant, device, and tag names add them to the kafka tag provider
	'''	
	global KAFKA_CREATE_PATH
	
	return system.tag.writeBlocking([KAFKA_CREATE_PATH], [tenant+"/"+device_name+"/"+tag_name])


def add_ref_tag_with_attrs(path, name, source, type):
	'''
	Add a reference tag at the given path with the given name to the main tag provider tree with the default parameters
	and reference it to the tag at source with the given type
	'''
	
	tag_props = {
		"valueSource": "reference",
		"dataType": type,
		"sourceTagPath": source,
		"name": name,           
		"tagType": "AtomicTag"
	}
	#   o == overwrite, a == abort
	collisionPolicy = "o"
	
	print tag_props
								 
	print system.tag.configure(path, [tag_props], collisionPolicy)[0]


def add_kafka_mapping(path, tag):
	'''
	Given a path and tag, create the matching tag in kafka and set up the mapping out of or into ignition (as applicable)
	'''
	if not path.startswith("[default]"):
		return
	
	# swap [default] for the AG kafka provider and cut down to only tenant/device
	kafka_path=get_kafka_path(path, tag)
	
	# abort if this already exists in kafka
	if system.tag.exists(kafka_path+"/"+tag):
		return
	
	# add the tag to kafka
	system.tag.writeBlocking([KAFKA_CREATE_PATH], [kafka_path+"/"+tag])
	
	if tag in ("SET_POINT_ABS", "RTCC_DR_PREACTION", "RTCC_DR_DEPLOY"):
		add_onchange_handler(kafka_path, tag, path+"/"+tag)
	else:
		add_onchange_handler(path, tag, kafka_path+"/"+tag)	


def add_kafka_mappings(path):
	'''
	Given a tag path, loop through all of the tags at this level of the path and add kafka mappings 
	'''
	results = system.tag.browse(path = path, filter = {'tagType':'AtomicTag'})
	for result in results.getResults():
	    add_kafka_mapping(path, result['name'])


def sync_mqtt_device(new_base_path):
	'''
	When a new deivce is connected, given the base path check to see if the structure exists:
	Tags
	  \tenantid
	    \new_device_name (the last segment of the new_base_path var is expected to be the new device's name)
	    
	The MQTT device name is expected to be of the form tenantid__deviceid (two underscores)
	    
	If not exists then create the above structure with tags transferring data to the associated tags under the kafka connector:
	AutoGrid Kafka
	  \tenantid
	    \new_device_name
	    
	   eg:  [default]testtenant/devid05216
	'''
	if new_base_path is None:
		return
	
	# check if this is enabled
	if not system.tag.readBlocking(["[default]AutoGrid/ENABLE_MQTT_AUTOCREATE"]):
		return
	
	devices_to_add={}
	tenant=""
	
	# eg: new_base_path="Sparkplug B Devices/MQTT SiteSim"
	mqtt_device_path="[MQTT Engine]Edge Nodes/"+new_base_path
	results = system.tag.browse(path = mqtt_device_path, filter = {})
	for result in results.getResults():
		if result['name'] != "Node Control" and result['name'] != "Node Info":
			if "__" in result["name"]:
				device=result["name"].split("__")[1]
				tenant=result["name"].split("__")[0]
				if system.tag.browse(path = "[default]"+tenant+"/"+device, filter = {}).getReturnedSize() == 0:
					for tag in system.tag.browse(path = mqtt_device_path+"/"+result["name"], filter = {}).getResults():
						if tag['name'] != "Device Info":
							ref_tag_path="[default]"+tenant+"/"+device
							add_ref_tag_with_attrs(ref_tag_path, tag['name'], str(tag['fullPath']), str(tag['dataType']))
							add_kafka_mapping(ref_tag_path, tag['name'])
							# TODO: register in Flex via API call
							#  how do we determine/create serice point, etc?
							'''
							system.net.httpPost("https://HOST/api/v1/devices", 
								"application/json",  
								system.util.jsonEncode({"device_identifier": device, "device_model": "heavy_industrial_load", "device_proxy": "SCADA", "params": []}),
								10000,
								60000,
								username,
								password,
								{},
								False,
								True)
							'''
	