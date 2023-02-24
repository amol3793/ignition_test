def watchdogUpdate(watchdogTagPath):
	newWatchdogValue = 1
	curWatchdogValue = system.tag.read(watchdogTagPath)
	print str(curWatchdogValue.quality)
	print("testing git")
	if str(curWatchdogValue.quality) == 'Bad_Disabled':
		OPCServer = system.tag.getAttribute(watchdogTagPath, 'OpcServer')
		if not(OPCServer == 'Ignition OPC UA Server'):
			if  system.opc.getServerState(OPCServer)== 'CONNECTED':
				watchdogTagPath = watchdogTagPath.replace('WatchdogRegister','WatchdogRegisterSim')
				curWatchdogValue = system.tag.read(watchdogTagPath)
				if (curWatchdogValue.value < 101):
					newWatchdogValue = curWatchdogValue.value + 1
				system.tag.writeBlocking([watchdogTagPath],[newWatchdogValue])
		else:
			OPCItemPath = system.tag.getAttribute(watchdogTagPath, 'OpcItemPath')
			modbusDevices = system.device.listDevices()
			modbusDevices = system.dataset.toPyDataSet(modbusDevices)
			for device in modbusDevices:
				if OPCItemPath.find(device['Name']) > -1:
					if device['State'] == 'Connected':
						watchdogTagPath = watchdogTagPath.replace('WatchdogRegister','WatchdogRegisterSim')
						curWatchdogValue = system.tag.read(watchdogTagPath)
						if curWatchdogValue.value is None:
							system.tag.writeBlocking([watchdogTagPath],[0])
							curWatchdogValue = system.tag.read(watchdogTagPath)
						if (curWatchdogValue.value < 101):
							newWatchdogValue = curWatchdogValue.value + 1
						system.tag.writeBlocking([watchdogTagPath],[newWatchdogValue])
				
	elif curWatchdogValue.quality.isGood():		
		if (curWatchdogValue.value < 101):
			newWatchdogValue = curWatchdogValue.value + 1
		system.tag.writeBlocking([watchdogTagPath],[newWatchdogValue])


def watchdogUpdateDEPRICATED(watchdogTagPath):
	print watchdogTagPath
	curWatchdogValue = system.tag.read(watchdogTagPath)
	newWatchdogValue = 0
	if curWatchdogValue.quality.isGood():
		if (curWatchdogValue.value < 100):
			newWatchdogValue = curWatchdogValue.value + 1
		else:
			newWatchdogValue = 1
		system.tag.write(watchdogTagPath,newWatchdogValue)

def createKafkaTags(UDTInstanceTagPath, UDTInstanceTag):
	# This script is used to create Kafka tags when UDTs instances are used	
	logger = system.util.getLogger("Kafka Tag Creator")
	
	UDTInstancePath = UDTInstanceTagPath.replace('/' + UDTInstanceTag,'')
	try:
		UDTConfig = system.tag.getConfiguration(UDTInstancePath)
		if len(UDTConfig) > 0:
			logger.info("Adding KAFKA tags for:  " + UDTInstancePath)
			assetName = UDTConfig[0]['name']
			assetParameters = UDTConfig[0]['parameters']
			assetParametersKeys = assetParameters.keys()
			for paramIndex in range(0,len(assetParameters)):
				if 'kafkaDevicePathPrefix' in assetParametersKeys[paramIndex]:
					kafkaPathPrefix =  str(assetParameters[assetParametersKeys[paramIndex]]).split(',')[1].replace(' value=','').replace('}', '')
					if len(kafkaPathPrefix) == 0:
						logger.warn('The kafka_pathPrefix parameter, usually [AutoGrid Kafka], is not defined in ' + UDTInstancePath + '\n No Kafka tags created') 		
						return
					break
			for paramIndex in range(0,len(assetParameters)):
				if 'kafkaTenant' in assetParametersKeys[paramIndex]:
					print "here"
					tenantName = ""
					tenantName =  str(assetParameters[assetParametersKeys[paramIndex]]).split(',')[1].replace(' value=','').replace('}', '')
					print tenantName
					if len(tenantName) == 0:
						print len(tenantName)
						print "gui"
						logger.warn('The kafka_Tenant parameter is not defined in ' + UDTInstancePath + '\n No Kafka tags created') 		
						return
					break
			for paramIndex in range(0,len(assetParameters)):
				if 'flex' in assetParametersKeys[paramIndex]:
					kafkaTag = str(assetParameters[assetParametersKeys[paramIndex]]).split(',')[1].replace(' value=','').replace('}', '')
					if len(kafkaTag) > 0:
						system.tag.writeBlocking(['[AutoGrid Kafka]_Meta/Control/CREATE'], [tenantName + '/' + assetName + '/' + kafkaTag])
						logger.info("Added KAFKA tag:  " + tenantName + '/' + assetName + '/' + kafkaTag)
		else:
			logger.warn("Create KAFKA Tags - Could not create Kafka tags for:  " + UDTInstancePath) 		
	except:
		logger.warn("Failed to create KAFKA tags for:  " + UDTInstancePath) 		
	
	system.tag.writeAsync([UDTInstanceTagPath],[0])
	return	
	
		 

def updateKafkaValue(UDTInstanceTagPath, UDTInstanceTag, flexParameter,  newValue):
				# This script is used to update Kafka tags when UDTs instances are used	
	logger = system.util.getLogger("Kafka Tag Update")
	UDTInstancePath = UDTInstanceTagPath.replace('/' + UDTInstanceTag,'')
	try:
		UDTConfig = system.tag.getConfiguration(UDTInstancePath)
		if len(UDTConfig) > 0:
			assetName = UDTConfig[0]['name']
			print UDTConfig[0]
			assetParameters = UDTConfig[0]['parameters']
			assetParametersKeys = assetParameters.keys()
			for paramIndex in range(0,len(assetParameters)):
				if 'kafkaDevicePathPrefix' in assetParametersKeys[paramIndex]:
					kafkaPathPrefix =  str(assetParameters[assetParametersKeys[paramIndex]]).split(',')[1].replace(' value=','').replace('}', '')
					break
			for paramIndex in range(0,len(assetParameters)):
				if 'kafkaTenant' in assetParametersKeys[paramIndex]:
					tenantName =  str(assetParameters[assetParametersKeys[paramIndex]]).split(',')[1].replace(' value=','').replace('}', '')
					break
			for paramIndex in range(0,len(assetParameters)):
				if flexParameter == assetParametersKeys[paramIndex]:
					flexTag =  str(assetParameters[assetParametersKeys[paramIndex]]).split(',')[1].replace(' value=','').replace('}', '')
					print(flexTag)
					break		
#			logger.info("Updating KAFKA tag value for:  " + kafkaPathPrefix + tenantName + '/' + assetName + '/' + flexTag + "  value: " + str(newValue))
# kafkaPathPrefix = [Autogrid Kafka]
# tenant Name = totalspain

			print newValue
			print kafkaPathPrefix + tenantName + '/' + assetName + '/' + flexTag
			print system.tag.writeAsync([kafkaPathPrefix + tenantName + '/' + assetName + '/' + flexTag], [newValue])

		else:
			logger.warn("Update KAFKA Value - Could not update Kafka tag value for:  " + UDTInstancePath) 		
	except:
		raise #logger.warn("Failed to update KAFKA tag value for:  " + UDTInstancePath +  "   Parameter: " + flexParameter) 		


	return

def updateKafkaAutogridLabels():
	
	sitelist = autogrid.utils.getChildrenTags('[default]Total Spain/Sites')
	#sitelist = [{"label":"FSOMA","value":"FSOMA"}]
	for site in sitelist:
		site_json = system.util.jsonDecode(site)
		service_point_name = site_json['label']
		up = autogrid.api.get_servicepoint_custom_attribute('totalspain', service_point_name, 'up')
		uof = autogrid.api.get_servicepoint_custom_attribute('totalspain', service_point_name, 'uof')
		kafkapath = '[AutoGrid Kafka]totalspain/' + service_point_name
		for tag in system.tag.browse(kafkapath):
			aglabel = str(tag['fullPath'])  + '.Autogrid-labels'
			dataset = system.tag.readBlocking(aglabel)[0].value
			up_exists = False
			uof_exists = False
			for row in range(dataset.getRowCount()):
				key = dataset.getValueAt(row, "key")
				if key == "up":
					dataset = system.dataset.updateRow(dataset, row, {'up':up})
					up_exists = True
				elif key == "uof":
					dataset = system.dataset.updateRow(dataset, row, {'uof':uof})
					uof_exists = True
			if not up_exists:
			  dataset = system.dataset.addRow(dataset, ['up',up])
			  print "up does not exist"
			if not uof_exists:
			  dataset = system.dataset.addRow(dataset, ['uof',uof])
			  print "uof does not exist"
			system.tag.writeBlocking(aglabel, dataset)

def getChildrenTags(folder_path):
	tagTree = system.tag.browse(folder_path)
  
	return map(lambda x: system.util.jsonEncode({"value": x["name"], "label": x["name"]}), tagTree)
  
def getChildrenTagsNiceNames(folder_path):
	tagTree = system.tag.browse(folder_path)
   
	return map(lambda x: system.util.jsonEncode({x["name"]}), tagTree)

def getChildrenTagsWithACS(folder_path):
		list_all_sites = autogrid.utils.getChildrenTags(folder_path)
		controllable_sites = list(filter(lambda x: system.tag.readBlocking(folder_path + '/' + system.util.jsonDecode(x)['value'] + '/Parameters/ACS_Enable')[0].value == 1, list_all_sites))
		return controllable_sites
		
def getChildrenTagsWithoutACS(folder_path):
  list_all_sites = autogrid.utils.getChildrenTags(folder_path)
  non_controllable_sites = list(filter(lambda x: system.tag.readBlocking(folder_path + '/' + system.util.jsonDecode(x)['value'] + '/Parameters/ACS_Enable')[0].value == 0, list_all_sites))
  return non_controllable_sites
				
#def sendDataToREE():
#  siteFolders = "[default]Total Spain/Sites"
#  controllable_sites = autogrid.utils.getChildrenTagsWithACS(siteFolders)
#  non_controllable_sites = autogrid.utils.getChildrenTagsWithoutACS(siteFolders)
#  
#  for controllable_site in controllable_sites:
#    print(controllable_site)
#  for non_controllable_site in non_controllable_sites:
#    sitePath = siteFolders + "/" + system.util.jsonDecode(non_controllable_site)['value']
#    active_power = system.tag.readBlocking([sitePath + "/Active_Power"])[0]
#    result = system.tag.writeBlocking(["[default]Total Spain/Operators/CECOEL/Site_Specific/Solar Simulator/From TOTSA/Active_Power"], [active_power.value])

def sendToREE(tagPath, currentValue):
  tagParent,siteName,metric = tagPath.rsplit("/",2)
  tag_path_cecore = "[default]Total Spain/Operators/CECORE/Site_Specific/"+siteName+"/From TOTSA/"+metric
  tag_path_cecoel = "[default]Total Spain/Operators/CECOEL/Site_Specific/"+siteName+"/From TOTSA/"+metric
  system.tag.writeBlocking([tag_path_cecore, tag_path_cecoel], [currentValue, currentValue]) 

#  if str(tag_path_cecore + ".quality") == "Good":
#  	system.tag.writeBlocking([tag_path_cecore], [currentValue])
#  if str(tag_path_cecoel + ".quality") == "Good":
# 	system.tag.writeBlocking([tag_path_cecoel], [currentValue])


#def eventScheduler():
#	now = system.date.now()
#	#Scheduled Events
#	scheduledEventstart = system.date.getDate("[default]Test/scheduledEvents.StartDate")
#	scheduledEventend = system.date.getDate("[default]Test/scheduledEvents.EndDate")
#	if system.date.isBetween(now, scheduledEventstart, scheduledEventend) #Checks if current time is within the event time window
#		system.tag.writeAsync([default]Test/scheduledEvents.assetName + '/' + scheduledEvent] , 1) #Starts Event
#	#Downtime Events
#	downtimeEventstart = system.date.getDate("[default]Test/downtimeEvents.StartDate")
#	downtimeEventend = system.date.getDate("[default]Test/downtimeEvents.EndDate")
#	if system.date.isBetween(now, downtimeEventstart, downtimeEventend) #Checks if current time is within the event time window
#		system.tag.writeAsync([default]Test/scheduledEvents.assetName + '/' + downtimeEvent] , 1) #Starts Event	
#	#Break Events
#	breakEventstart = system.date.getDate("[default]Test/breakEvents.StartDate")
#	breakEventend = system.date.getDate("[default]Test/breakEvents.EndDate")
#	if system.date.isBetween(now, breakEventstart, breakEventend) #Checks if current time is within the event time window
#		system.tag.writeAsync([default]Test/scheduledEvents.assetName + '/' + breakEvent] , 1) #Starts Event

def sendDataToFlex(tagName):
  #retrieve all children of Sites
  getChildrenTags("[default]Total Spain/Sites")
  #forEachChildrenTags 
  #read the value of tagName and push to Kafka provider

  

  		

					
