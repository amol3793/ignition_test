"""
PoC for moving an RTCC config into Ignition.  Read the RTCC config API and create the devices and their associated tags in ignition, collapsing the RTCC
site->device->datapoint heirarchy into Ignition's device->tag model.

Invoke manually in a console with:

import rtcc_sync

rtcc_uri="https://10.55.0.90/api/v1/module"
rtcc_user="admin"
rtcc_passwd="admin"
rtcc_instance="predictive_controls_dev"

rtcc_sync.sync_rtcc(rtcc_uri,rtcc_user,rtcc_passwd,rtcc_instance)
"""

def get_rtcc_devices(rtcc_uri,rtcc_user,rtcc_passwd):
	rtcc_resp = system.net.httpGet(rtcc_uri+"/site", username=rtcc_user, password=rtcc_passwd, bypassCertValidation =True)
	response = system.util.jsonDecode(rtcc_resp)
	
	return response


def get_rtcc_site_devices(rtcc_uri,rtcc_user,rtcc_passwd):
	rtcc_resp = system.net.httpGet(rtcc_uri+"/device", username=rtcc_user, password=rtcc_passwd, bypassCertValidation =True)
	response = system.util.jsonDecode(rtcc_resp)
	
	return response


def get_rtcc_datapoints(rtcc_uri,rtcc_user,rtcc_passwd):
	rtcc_resp = system.net.httpGet(rtcc_uri+"/datapoint", username=rtcc_user, password=rtcc_passwd, bypassCertValidation =True)
	response = system.util.jsonDecode(rtcc_resp)
	
	return response


def sync_rtcc(rtcc_uri,rtcc_user,rtcc_passwd,rtcc_instance,tenant="test_tenant"):
	rtcc_devices = get_rtcc_devices(rtcc_uri,rtcc_user,rtcc_passwd)
	rtcc_site_devices = get_rtcc_site_devices(rtcc_uri,rtcc_user,rtcc_passwd)
	rtcc_datapoints = get_rtcc_datapoints(rtcc_uri,rtcc_user,rtcc_passwd)
	
	ign_devices=system.dataset.toPyDataSet(system.device.listDevices())
	kafka_tag_creation_path="[AutoGrid Kafka]_Meta/Control/CREATE"
	
	for rtcc_device in rtcc_devices['results']:
		if rtcc_device['rtcc_instance'] == rtcc_instance:
			converted_name=rtcc_device['site_name']
		
			found=False
			for ign_device in ign_devices:
				if ign_device['Name'] == converted_name:
					found = True
			if not found:
				print "Importing " + rtcc_device['site_name']
				
				# match RTCC protocol to Ignition driver
				driver=None
				if rtcc_device['protocol'] == "Modbus":
					driver="ModbusTcp"
				elif rtcc_device['protocol'] == "DNP3":
					driver="Dnp3Driver"
				else:
					print "No matching driver" # logger.warn()...
					continue
					
				props={
					"Hostname": rtcc_device['ip_address'],
					"Port": rtcc_device['port']
					}
				
				# handle protocol specific settings
				if driver == "ModbusTcp":
					props["zeroBasedAddressing"] = False # this is backwards: we want to start counting at 0 so we need to set this to false (a bug?)
					
				elif driver == "Dnp3Driver":
					props["sourceAddress"]=rtcc_device['protocol_master_id']  # master ID
					props["destinationAddress"]=rtcc_device['protocol_station_id']  # slave ID
					props["integrityPollInterval"]=rtcc_device['scan_rate']
					
				system.device.addDevice(deviceType=driver,\
										deviceName=converted_name,\
										deviceProps=props)
				# disable by default
				system.device.setDeviceEnabled(converted_name, 0)
				
				# now add datapoints to new device by mapping RTCC devices to folders and datapoints to tags
				for rtcc_site_device in rtcc_site_devices['results']:
					if rtcc_site_device['site_id']  == rtcc_device['site_id']:
						tag_base_path = "[default]/"+tenant+"/"+converted_name+"/"+rtcc_site_device["device_name"]
						
						for rtcc_tag in rtcc_datapoints['results']:
						 	if rtcc_tag['device_id'] == rtcc_site_device['device_id']:
						 		opcItemPath = "ns=1;s=["+converted_name+"]"
						 		dataType=None
						 		
						 		if rtcc_device['protocol'] == "Modbus":
						 			# 16 bit signed and unsigned
						 			if rtcc_tag['protocol_function'] == "HOLDING" and rtcc_tag['data_format'] == 'INT16':
						 				opcItemPath = opcItemPath+"HR"
						 				dataType="Int4"
						 			elif rtcc_tag['protocol_function'] == "HOLDING" and rtcc_tag['data_format'] == 'UINT16':
						 				opcItemPath = opcItemPath+"HRUS"
						 				dataType="Int4"
						 			elif rtcc_tag['protocol_function'] == "INPUT" and rtcc_tag['data_format'] == 'INT16':
						 				opcItemPath = opcItemPath+"IR"
						 				dataType="Int4"
						 			elif rtcc_tag['protocol_function'] == "INPUT" and rtcc_tag['data_format'] == 'UINT16':
						 				opcItemPath = opcItemPath+"IRUS"
						 				dataType="Int4"
						 			#floating point
						 			elif rtcc_tag['protocol_function'] == "HOLDING" and rtcc_tag['data_format'] == 'FLOAT32':
						 				opcItemPath = opcItemPath+"HRF"
						 				dataType="Float8"
						 			elif rtcc_tag['protocol_function'] == "INPUT" and rtcc_tag['data_format'] == 'FLOAT32':
						 				opcItemPath = opcItemPath+"IRF"
						 				dataType="Float8"
						 			# 32 bit ints
						 			elif rtcc_tag['protocol_function'] == "HOLDING" and rtcc_tag['data_format'] == 'INT32':
						 				opcItemPath = opcItemPath+"HRI"
						 				dataType="Int4"
						 			elif rtcc_tag['protocol_function'] == "HOLDING" and rtcc_tag['data_format'] == 'UINT32':
						 				opcItemPath = opcItemPath+"HRUI"
						 				dataType="Int4"
						 			elif rtcc_tag['protocol_function'] == "INPUT" and rtcc_tag['data_format'] == 'INT32':
						 				opcItemPath = opcItemPath+"IRI"
						 				dataType="Int4"
						 			elif rtcc_tag['protocol_function'] == "INPUT" and rtcc_tag['data_format'] == 'UINT32':
						 				opcItemPath = opcItemPath+"IRUI"
						 				dataType="Int4"
						 			# coils
						 			elif rtcc_tag['protocol_function'] == "COIL":
						 				opcItemPath = opcItemPath+"C"
						 				dataType="Boolean"
						 			else:
						 				print "Unsupported format: " + rtcc_tag['data_format'] # logger.warn...
						 				pass
						 				
						 			opcItemPath = opcItemPath+str(rtcc_tag['datapoint_index'])
						 	
						 		# TODO: support importing the scale and offset factors
						 		tag_props = {
						 			"name": rtcc_tag['datapoint_name'],           
						 			"opcItemPath" : opcItemPath,
						 			"opcServer": "Ignition OPC-UA Server",
						 			"valueSource": "opc",
						 			"dataType": dataType,
									"eventScripts": [
									  {
						 			    "eventid": "valueChanged",
						 			    "script": "\tif currentValue.quality.isGood():\n\t\tsystem.tag.writeAsync([tagPath.replace(\"[default]\",\"[AutoGrid Kafka]\")], [currentValue])"
						 			  }
						 			]#,
						 			#"sampleMode" : sampleMode,
						 			#"tagGroup" : tagGroup
						 			}
								#   o == overwrite, a == abort
								collisionPolicy = "o"
								 
								system.tag.configure(tag_base_path, [tag_props], collisionPolicy)
								
								# now create the tags in the kafka module
								autogrid.sync.add_tag_to_kafka(tenant, rtcc_site_device["device_name"], converted_name)
								
								# add change handlers to new tag
								