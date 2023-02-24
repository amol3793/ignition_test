import com.inductiveautomation.ignition.common.opc

def watchdogUpdate(watchdogTagPath):
	'''
		Purpose:  	Updates the watchdog heartbeat value in the local controller.
		
		Called By:  {asset}/heartbeat/_heartbeatUpdate
					The _heartbeatUpdate tag is periodically executed based on the hearbeatPeriodicity property of the {asset}

		Notes:		1. 	Heartbeat value is only updated if the connectivity to the {asset} is good and the _heartbeatUpdate is enabled.  
					2. 	The {asset}/heartbeat/watchdogHeartbeat will be incremented by 1 each time this subroutine is called.  Once 
						the value is 100, the value will be reset to 1.  A watchdogHeartbeat value of 0 will NEVER be written.
		'''
		# check connectivity status of the {asset}
	connectivityTagPath = watchdogTagPath.replace('heartbeat/watchdogHeartbeat', 'connectivityStatus/connectivityStatus')
	curConnectivity = int(system.tag.readBlocking([connectivityTagPath])[0].value)

		# get the current value of {asset}/heartbeat/watchdogHeartbeat
	curWatchdogValue = int(system.tag.readBlocking([watchdogTagPath])[0].value)
		# initialize the newWatchdogValue	
	newWatchdogValue = 0

		# if good connectivity, increment the {asset}/heartbeat/watchdogHeartbeat and write the new value to the {asset} controller
	if (curConnectivity == 1):
		if (curWatchdogValue < 100):
			newWatchdogValue = curWatchdogValue + 1
		else:
			newWatchdogValue = 1
		system.tag.write(watchdogTagPath,newWatchdogValue)
		
def getUDTParameters(UDTInstancePath):
	'''
	Purpose:  	Reads the tag configuration of the {asset} represented by the full UDTInstancePath.
				Extracts the list of parameters from the tag configuration and returns the list.
				Returns none if the tag represented by the UDTInstancePath is not found

	Called By:  other utils functions in order to get current parameter values of the asset

	Notes:		
	'''
		# read the tag represented by UDTInstancepath; check the length of the config information to ensure validity; return parameters 
	try:
		UDTConfig = system.tag.getConfiguration(UDTInstancePath)
		if len(UDTConfig) > 0:
			return UDTConfig[0]['parameters']
	except:
		return none

def extractParameterValue(parameterEntryList):
	'''
	Purpose:  	Extracts the value of the parameter from a string that contains the parameter name and the parameter value.
				This parameter string is extracted from the parameter list else where.  This function strips away all of the information
				in the string except the value of the parameter and returns that value.
	
	Called By:  other utils functions in order to get current parameter values of the asset
	
	Notes:		if no parameter value is found, an empty string '' is returned	
	'''
	
	parameterEntryList = str(parameterEntryList)
	try:
		return parameterEntryList[parameterEntryList.rindex('value=')+6: len(parameterEntryList)].replace('}','')
	except:
		return 	''

	
def createKafkaTags(UDTInstanceTagPath, UDTInstancePropertyTag):
	'''
	Purpose:  	Finds the kafka_tenant in the {asset} parameters and
				gets a list of parameters of the {asset} and scans the list for all parameter names for those that begin with 'flex'.
				When a parameter name beginning with 'flex' is found, the value of the parameter is the name of the kafka tag that needs
				to be created using the kafkaPathPrefix and the kafka_tenant as root and branch portions of the path.  If a
				'flex' parameter is found with a value of empty string '', no tag is created.  For flex tags that include the text 'dispatch',
				the configuration of the tag is changed after creation wherein an onchange script is automatically added to call for
				'doDiscreteDispatch' or 'doAnalogDispatch'
	
	Called By:  When the "Create Kafka Tags" button is clicked on the Dashboard 'General' tab, the {asset}/_createKafkaTags variable is set to 1.
				An onchange script call is made to this function by the {asset}/_createKafkaTags
	
	Notes:	
			
	'''

		# CONSTANTS for createKafkaTags	
	KafkaModuleTagCreatorPath = '[AutoGrid Kafka]_Meta/Control/CREATE'
	#KafkaTagProviderRootPath = '[AutoGrid Kafka]'
	loopDelayIndex = 0;
	loopDelayIndexMax = 10000;
	tab = '\t'
	newline = ' \n'
	UDTscriptPath = 'StandardUDT.utils.'

		# get logger handle
	logger = system.util.getLogger("Kafka Tag Creator")
	
		# extract {asset} path from the parameters passed to createKafkaTags.  
		# The first parameter contains the full path of the {asset} including the variable calling this funcion.
		# The second parameter contains the name of the variable in the asset which called this function. 
		# The asset path without the asset variable name is desired.
	UDTInstancePath = UDTInstanceTagPath.replace('/' + UDTInstancePropertyTag,'')

	try:

		# Parse the asset name from the UDTInstancePath variable
		assetName = UDTInstancePath[UDTInstancePath.rindex('/')+1: len(UDTInstancePath)]

		# Log the start of adding Kafka tags for the {asset}
		logger.info("Adding KAFKA tags for:  " + UDTInstancePath)

		# get a list of the {asset} parameters
		UDTInstanceParameters = getUDTParameters(UDTInstancePath)
		
		# get Ignition kafa tag provider root
		kafkaPathPrefix = extractParameterValue(UDTInstanceParameters['kafka_devicePathPrefix'])
		
		# log message and return if the kafka_devicePathPrefix parameter is not set in the {asset}
		if len(kafkaPathPrefix) == 0:
			logger.error('''The "kafka_pathPrefix" parameter, usually "[AutoGrid Kafka]", is not defined in ''' + UDTInstancePath + ' - No Kafka tags created')
			return
		
		# log message and return if the kafka_tenant parameter is not set in the {asset}
		tenantName = extractParameterValue(UDTInstanceParameters['kafka_tenant'])
		if len(tenantName) == 0:
			logger.error('''The "kafka_tenant" parameter is not defined in ''' + UDTInstancePath + " - No Kafka tags created") 
			return
			
		# interate through the {asset} parmeters looking for 'flex' in the parameter name	
		for key,value in UDTInstanceParameters.items():
			kafkaTag = ''

		# if a parameter is found with 'flex' in the name, create the appropriate Kafka tag
			if 'flex' in key:
				kafkaTag = extractParameterValue(value)				
				if len(kafkaTag) > 0:
					system.tag.writeBlocking([KafkaModuleTagCreatorPath], [tenantName + '/' + assetName + '/' + kafkaTag])
		
		# delay to let the Kafka module create the kafka tag.  The kafka module can only handle one tag creation request at a time
		# and does not que the requests and there is no blocking mechanism to hang this script while waiting for the Kafka module to create
		# the tag so an old school mechanism of looping through testing for the tag's existence until it is created is needed
					while not (system.tag.exists(kafkaPathPrefix + tenantName + '/' + assetName + '/' + kafkaTag)) and (loopDelayIndex < loopDelayIndexMax):
						loopDelayIndex = loopDelayIndex + 1
					
		# once the Kafka tag is created create a log info entry to indicate the same			
					if (system.tag.exists(kafkaPathPrefix + tenantName + '/' + assetName + '/' + kafkaTag)):
						logger.info("Added KAFKA tag:  " + tenantName + '/' + assetName + '/' + kafkaTag)
	
		# if the kafka tag created is a discrete dispatch command tag, then edit the tag configuration to include an onchange script
		# to execute the doDiscreteDispatch funcion.
						if ('dispatchCommand' in key):
							script = ''
							script = script + tab + 'dispatchUDTPath = "' + UDTInstancePath + '"'  + newline
							script = script + tab + UDTscriptPath + 'doDiscreteDispatch(tagPath, tag.name, dispatchUDTPath, currentValue.value)' + newline
							config = system.tag.getConfiguration(kafkaPathPrefix + tenantName + '/' + assetName + '/' + kafkaTag)
							eventScripts = 	{
											'eventid':'valueChanged',
											'script': script
											}
							tag = 	{
									'name': kafkaTag,
									'eventScripts':[eventScripts]           
									}
							result = system.tag.configure(kafkaPathPrefix + tenantName + '/' + assetName,[tag],'m')        							

		# if the kafka tag created is an analog dispatch command tag, then edit the tag configuration to include an onchange script
		# to execute the doAnalogDispatch funcion.
						if ('dispatchSetpoint' in key):
							script = ''
							script = script + tab + 'dispatchUDTPath = "' + UDTInstancePath + '"'  + newline
							script = script + tab + UDTscriptPath + 'doAnalogDispatch(tagPath, tag.name, dispatchUDTPath, currentValue.value)' + newline
							config = system.tag.getConfiguration(kafkaPathPrefix + tenantName + '/' + assetName + '/' + kafkaTag)
							eventScripts = 	{
											'eventid':'valueChanged',
											'script': script
											}
							tag = 	{
									'name': kafkaTag,
									'eventScripts':[eventScripts]           
									}
							result = system.tag.configure(kafkaPathPrefix + tenantName + '/' + assetName,[tag],'m')        							

		# if the kafka tag created is a dispatch Preactivation command tag, then edit the tag configuration to include an onchange script
		# to execute the doPreactDispatch funcion.
						if ('dispatchPreactivation' in key):
							script = ''
							isDiscreteDispatch = int(extractParameterValue(UDTInstanceParameters['config_isDiscreteDispatch']))
							isAnalogDispatch = int(extractParameterValue(UDTInstanceParameters['config_isAnalogDispatch']))
							script = script + tab + 'dispatchUDTPath = "' + UDTInstancePath + '"'  + newline
							script = script + tab + UDTscriptPath + 'doPreactDispatch(tagPath, tag.name, dispatchUDTPath, currentValue.value)' + newline
							config = system.tag.getConfiguration(kafkaPathPrefix + tenantName + '/' + assetName + '/' + kafkaTag)
							eventScripts = 	{
											'eventid':'valueChanged',
											'script': script
											}
							tag = 	{
									'name': kafkaTag,
									'eventScripts':[eventScripts]           
									}
							result = system.tag.configure(kafkaPathPrefix + tenantName + '/' + assetName,[tag],'m')        							
					loopDelayIndex = 0	
				else:
					logger.warn("Create KAFKA Tags - kafka tag undefined for " + UDTInstancePath + "   " + key + " parameter") 		
	except:
		logger.warn("Failed to create KAFKA tags for:  " + UDTInstancePath) 		
	
		# set the {asset}/_createKafkaTags variable to zero
	system.tag.writeAsync([UDTInstanceTagPath],[0])
	return	

def updateKafkaValue(UDTInstancePropertyTagPath, UDTInstancePropertyTag, newValue):
						#This script is used to update Kafka tags when UDTs instances are used
		
						# Get a logger to provide information in the event an error 
						# occurs or debug information needs to be sent to the Ignition 
						# logger system
	logger = system.util.getLogger("Kafka Tag Update")
						# Walk up the UDT property tree starting at the property initiating
						# this function to get to the root UDT Instance and assign the 
						# UDTInstancePath variable
	if 'telemetryValues' in  UDTInstancePropertyTagPath:
		UDTInstancePath = UDTInstancePropertyTagPath.replace('/telemetryValues/' + UDTInstancePropertyTag,'')
	elif 'systemStatus' in  UDTInstancePropertyTagPath:
		UDTInstancePath = UDTInstancePropertyTagPath.replace('/systemStatus/' + UDTInstancePropertyTag,'')
	elif 'heartbeat' in  UDTInstancePropertyTagPath:
		UDTInstancePath = UDTInstancePropertyTagPath.replace('/heartbeat/' + UDTInstancePropertyTag,'')
	elif 'dispatch' in  UDTInstancePropertyTagPath:
		UDTInstancePath = UDTInstancePropertyTagPath.replace('/dispatch/' + UDTInstancePropertyTag,'')
	elif 'businessServices' in  UDTInstancePropertyTagPath:
			UDTInstancePath = UDTInstancePropertyTagPath.replace('/businessServices/' + UDTInstancePropertyTag,'')
	elif 'connectivityStatus' in  UDTInstancePropertyTagPath:
				UDTInstancePath = UDTInstancePropertyTagPath.replace('/connectivityStatus/' + UDTInstancePropertyTag,'')
	else: 
		UDTInstancePath = UDTInstancePropertyTagPath.replace('/' + UDTInstancePropertyTag,'')
						# Parse the asset name from the UDTInstancePath variable
	assetName = UDTInstancePath[UDTInstancePath.rindex('/')+1: len(UDTInstancePath)]
						# Attempt to get the kafka information needed from the UDT Instance
						# parameters in order to update the kafka stream with the new value 
						# of the UDT property
	
	try:
		parameters = getUDTParameters(UDTInstancePath)
		if not (parameters == None):
			kafka_devicePathPrefix = extractParameterValue(parameters['kafka_devicePathPrefix'])
			kafka_tenant = extractParameterValue(parameters['kafka_tenant'])
			if ('Temperature' in UDTInstancePropertyTag) or ('Wind' in UDTInstancePropertyTag):
				usesMetricUnits = int(extractParameterValue(parameters['config_usesMetricUnits']))
			if ('Temperature' in UDTInstancePropertyTag) and (usesMetricUnits == 1):
				flex_tag = extractParameterValue(parameters['flex_measuredTemperatureCelciusTag'])
			elif ('Temperature' in UDTInstancePropertyTag) and not(usesMetricUnits == 1):
				flex_tag = extractParameterValue(parameters['flex_measuredTemperatureFarenheitTag'])
			elif ('Wind' in UDTInstancePropertyTag) and (usesMetricUnits == 1):
				flex_tag = extractParameterValue(parameters['flex_measuredWindSpeedKPHTag'])
			elif ('Wind' in UDTInstancePropertyTag) and not(usesMetricUnits == 1):
				flex_tag = extractParameterValue(parameters['flex_measuredWindSpeedMPHTag'])
			else:
				flex_tag = extractParameterValue(parameters['flex_' + UDTInstancePropertyTag + 'Tag'])
						# if the kafka_devicePathPrefix is not configured, issue an error and exit
			if len(str(kafka_devicePathPrefix)) == 0:
				logger.debug("kafka_devicePathPrefix parameter is undefined for " + UDTInstancePropertyTagPath +
							"  Updating kafka stream with timeseries data from this property will be unavailable until this property is accurately set")
				return
					# if the kafka_tenant is not configured, issue an error and exit
			if len(str(kafka_tenant)) == 0:
				logger.debug("kafka_tenant parameter is undefined for " + UDTInstancePropertyTagPath +
							"  Updating kafka stream with timeseries data from this property will be unavailable until this property is accurately set")
				return
					# if the kafka stream tag for the UTD property is not configured, issue an error and exit
			if len(str(flex_tag)) == 0:
				logger.debug('flex_' + UDTInstanceTag + 'Tag' + ' parameter is undefined for ' + UDTInstancePropertyTagPath +
							"  Updating kafka stream with timeseries data from this property will be unavailable until this property is accurately set")
				return
						# if the logger is in Debug mode, print a statement that indicates an attempt to 
						# update the kafka stream with the new value	
#			logger.debug("Updating KAFKA tag value for:  " + kafkaPathPrefix + tenantName + '/' + assetName + '/' + flexTag + "  value: " + str(newValue))
						# write the new value to the kafka stream
			system.tag.writeBlocking([kafka_devicePathPrefix + kafka_tenant + '/' + assetName + '/' + flex_tag], [newValue])
		else:
			logger.error("Update KAFKA Value - Could not get parameters for  " + UDTInstancePath) 		
	except:
		logger.error("Catastrophic Error when attempting update KAFKA tag value for :  " + UDTInstancePropertyTagPath) 		

	return	

def doDiscreteDispatch(tagPath, tagName, dispatchUDTPath, newValue):
			# determine if a Manual dispatch is in progress
	dispatchManualDispatch = 0
	dispatchManualDispatch = system.tag.readBlocking([dispatchUDTPath + '/dispatch/_dispatchManualDispatchEnable'])[0]
	if (dispatchManualDispatch.value == 0):
			# get UDT parameters to determine configuration for the Discrete dispatch
		parameters = getUDTParameters(dispatchUDTPath)
		if not (parameters == None):
				# find the values that need to be written to the local controller for Dispatch and RTN
			discreteDispatchControllerDispatchValue = int(extractParameterValue(parameters['config_discreteDispatchControllerDispatchValue']))
			discreteDispatchControllerDispatchRTNValue = int(extractParameterValue(parameters['config_discreteDispatchControllerDispatchRTNValue']))
			is3WireDiscreteDispatch = int(extractParameterValue(parameters['config_is3WireDiscreteDispatch']))
			hasAggregateDispatch = int(extractParameterValue(parameters['config_hasAggregateDispatch']))
			aggregateDispatchParentPath = extractParameterValue(parameters['config_aggregateDispatchParentPath'])
			kafka_devicePathPrefix = extractParameterValue(parameters['kafka_devicePathPrefix'])
			kafka_tenant = extractParameterValue(parameters['kafka_tenant'])

				# test if Discrete Dispatch is aggregated to another asset 
			print hasAggregateDispatch
			if (hasAggregateDispatch == 1):
					# get UDT parameters of the aggregated asset for dispatch
				parameters = getUDTParameters(aggregateDispatchParentPath)
				aggregate_dispatchCommandTag = extractParameterValue(parameters['flex_dispatchCommandTag'])
				tagRoot = (aggregateDispatchParentPath.split('/'))[-1]
				aggregate_dispatchCommandPath = kafka_devicePathPrefix  + kafka_tenant + '/' + tagRoot + '/' + aggregate_dispatchCommandTag
				system.tag.writeBlocking([aggregate_dispatchCommandPath],[newValue])
			else:
				# test if Discrete Dispatch is controlled by 
				print is3WireDiscreteDispatch
				if (is3WireDiscreteDispatch == 0):  # must be 2-wire control so use only startDispatch register
					if (newValue == 1):
						print dispatchUDTPath + '/dispatch/startDispatch'
						print discreteDispatchControllerDispatchValue
						system.tag.writeBlocking([dispatchUDTPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchValue])
					else:
						system.tag.writeBlocking([dispatchUDTPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchRTNValue])
				else:   # must be 3-wire control so use both startDispatch and StopDispatch registers				
					if (newValue == 1):
						system.tag.writeBlocking([dispatchUDTPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchValue])
						system.tag.writeBlocking([dispatchUDTPath + '/dispatch/stopDispatch'],[discreteDispatchControllerDispatchRTNValue])
					else:
						system.tag.writeBlocking([dispatchUDTPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchRTNValue])
						system.tag.writeBlocking([dispatchUDTPath + '/dispatch/stopDispatch'],[discreteDispatchControllerDispatchValue])
	return
					
def doAnalogDispatch(tagPath, tagName, dispatchUDTPath, newValue):
                    # determine if a Manual dispatch is in progress
	dispatchManualDispatch = 0
	dispatchManualDispatch = system.tag.readBlocking([dispatchUDTPath + '/dispatch/_dispatchManualDispatchEnable'])[0]
	if (dispatchManualDispatch.value == 0):
					# get UDT parameters to determine configuration for the Discrete dispatch
		parameters = getUDTParameters(dispatchUDTPath)
		if not (parameters == None):
					# find the values that need to be written to the local controller for Dispatch and RTN
			hasAggregateDispatch = int(extractParameterValue(parameters['config_hasAggregateDispatch']))
			aggregateDispatchParentPath = extractParameterValue(parameters['config_aggregateDispatchParentPath'])
			kafka_devicePathPrefix = extractParameterValue(parameters['kafka_devicePathPrefix'])
			kafka_tenant = extractParameterValue(parameters['kafka_tenant'])

					# test if Analog Dispatch is aggregated to another asset 
			if (hasAggregateDispatch == 1):
					# get UDT parameters of the aggregated asset for dispatch
				parameters = getUDTParameters(aggregateDispatchParentPath)
				aggregate_dispatchSetpointTag = extractParameterValue(parameters['flex_dispatchSetpointTag'])
				tagRoot = (aggregateDispatchParentPath.split('/'))[-1]
				aggregate_dispatchSetpointPath = kafka_devicePathPrefix  + kafka_tenant + '/' + tagRoot + '/' + aggregate_dispatchSetpointTag
				system.tag.writeBlocking([aggregate_dispatchSetpointPath],[newValue])
			else:
				system.tag.writeBlocking([dispatchUDTPath + '/dispatch/setpointDispatch'],[newValue])
	return

def doPreactDispatch(tagPath, tagName, dispatchUDTPath, newValue):
                    # determine if a Manual dispatch is in progress
	dispatchManualDispatch = 0
	dispatchManualDispatch = system.tag.readBlocking([dispatchUDTPath + '/dispatch/_dispatchManualDispatchEnable'])[0]
	if (dispatchManualDispatch.value == 0):
					# get UDT parameters to determine configuration for the Discrete dispatch
		parameters = getUDTParameters(dispatchUDTPath)
		if not (parameters == None):
					# find the values that need to be written to the local controller for Dispatch and RTN
			hasAggregateDispatch = int(extractParameterValue(parameters['config_hasAggregateDispatch']))
			aggregateDispatchParentPath = extractParameterValue(parameters['config_aggregateDispatchParentPath'])
			kafka_devicePathPrefix = extractParameterValue(parameters['kafka_devicePathPrefix'])
			kafka_tenant = extractParameterValue(parameters['kafka_tenant'])

					# test if Analog Dispatch is aggregated to another asset 
			if (hasAggregateDispatch == 1):
					# get UDT parameters of the aggregated asset for dispatch
				parameters = getUDTParameters(aggregateDispatchParentPath)
				aggregate_dispatchSetpointTag = extractParameterValue(parameters['flex_dispatchPreactivationTag'])
				tagRoot = (aggregateDispatchParentPath.split('/'))[-1]
				aggregate_dispatchSetpointPath = kafka_devicePathPrefix  + kafka_tenant + '/' + tagRoot + '/' + aggregate_dispatchSetpointTag
				system.tag.writeBlocking([aggregate_dispatchSetpointPath],[newValue])
			else:
				system.tag.writeBlocking([dispatchUDTPath + '/dispatch/preactivation'],[newValue])
	return

def doManualDispatch(tagPath, tagName, dispatchValue):
			        	# determine if a Manual dispatch is in progress
		logger = system.util.getLogger('Manual Dispatch')
		logger.info('tagPath: '+tagPath+' .... '+'tagName: '+tagName+' .... '+'dispatchValue: '+str(dispatchValue))
		UTDPath = tagPath.replace('/dispatch/'+tagName,'')
		dispatchManualDispatchEnable = 0
		dispatchManualDispatchEnable = int(system.tag.readBlocking([UTDPath + '/dispatch/_dispatchManualDispatchEnable'])[0].value)
						# get UDT parameters to determine configuration for the Manual dispatch
		parameters = getUDTParameters(UTDPath)
		if not (parameters == None):
						# find the values that need to be written to the local controller for Direct Dispatch or Aggregate Dispatch
			hasAggregateDispatch = int(extractParameterValue(parameters['config_hasAggregateDispatch']))
			aggregateDispatchParentPath = extractParameterValue(parameters['config_aggregateDispatchParentPath'])
			isDiscreteDispatch = int(extractParameterValue(parameters['config_isDiscreteDispatch']))
			isAnalogDispatch = int(extractParameterValue(parameters['config_isAnalogDispatch']))
			discreteDispatchControllerDispatchValue = int(extractParameterValue(parameters['config_discreteDispatchControllerDispatchValue']))
			discreteDispatchControllerDispatchRTNValue = int(extractParameterValue(parameters['config_discreteDispatchControllerDispatchRTNValue']))
			is3WireDiscreteDispatch = int(extractParameterValue(parameters['config_is3WireDiscreteDispatch']))
			analogDispatchManualDispatchValue = int(extractParameterValue(parameters['config_analogDispatchManualDispatchValue']))
			analogDispatchManualRTNValue = int(extractParameterValue(parameters['config_analogDispatchManualRTNValue']))
			if ((dispatchManualDispatchEnable == 1) and (isAnalogDispatch == 1)): 
				if (dispatchManualDispatch == 1):
						# test if Analog Dispatch is aggregated to another asset 
					if (hasAggregateDispatch == 1):
						# get UDT parameters of the aggregated asset for dispatch
						parameters = getUDTParameters(aggregateDispatchParentPath)
						aggregate_dispatchSetpointTag = extractParameterValue(parameters['flex_dispatchSetpointTag'])
						tagRoot = (aggregateDispatchParentPath.split('/'))[-1]
						aggregate_dispatchSetpointPath = kafka_devicePathPrefix  + kafka_tenant + '/' + tagRoot + '/' + aggregate_dispatchSetpointTag
						system.tag.writeBlocking([aggregate_dispatchSetpointPath],[analogDispatchManualDispatchValue])
					else:
						system.tag.writeBlocking([UTDPath + '/dispatch/setpointDispatch'],[analogDispatchManualDispatchValue])
				else:
					if (hasAggregateDispatch == 1):
						# get UDT parameters of the aggregated asset for dispatch
						parameters = getUDTParameters(aggregateDispatchParentPath)
						aggregate_dispatchSetpointTag = extractParameterValue(parameters['flex_dispatchSetpointTag'])
						tagRoot = (aggregateDispatchParentPath.split('/'))[-1]
						aggregate_dispatchSetpointPath = kafka_devicePathPrefix  + kafka_tenant + '/' + tagRoot + '/' + aggregate_dispatchSetpointTag
						system.tag.writeBlocking([aggregate_dispatchSetpointPath],[analogDispatchManualRTNValue])
					else:
						system.tag.writeBlocking([UTDPath + '/dispatch/setpointDispatch'],[analogDispatchManualRTNValue])
			
			
			if ((dispatchManualDispatchEnable == 1) and (isDiscreteDispatch == 1)):
				print ("dispatchManualDispatchEnable: "+ str(dispatchManualDispatchEnable) +' .... '+'isDiscreteDispatch: '+str(isDiscreteDispatch))
					# test if Discrete Dispatch is aggregated to another asset 
				if (hasAggregateDispatch == 1):
					# test if Discrete Dispatch is controlled by one or more registers
						if (dispatchValue == 1):
							parameters = getUDTParameters(aggregateDispatchParentPath)
							aggregate_dispatchCommandTag = extractParameterValue(parameters['flex_dispatchCommandTag'])
							tagRoot = (aggregateDispatchParentPath.split('/'))[-1]
							aggregate_dispatchCommandPath = kafka_devicePathPrefix  + kafka_tenant + '/' + tagRoot + '/' + aggregate_dispatchCommandTag
							system.tag.writeBlocking([aggregate_dispatchCommandPath],[1])
						else:
							parameters = getUDTParameters(aggregateDispatchParentPath)
							aggregate_dispatchCommandTag = extractParameterValue(parameters['flex_dispatchCommandTag'])
							tagRoot = (aggregateDispatchParentPath.split('/'))[-1]
							aggregate_dispatchCommandPath = kafka_devicePathPrefix  + kafka_tenant + '/' + tagRoot + '/' + aggregate_dispatchCommandTag
							system.tag.writeBlocking([aggregate_dispatchCommandPath],[0])
				else:
					# test if Discrete Dispatch is controlled by one or more registers
					if (is3WireDiscreteDispatch == 0):  # must be 2-wire control so use only startDispatch register
						if (dispatchValue == 1):
							system.tag.writeBlocking([UTDPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchValue])
						else:
							print('dispatchValue: '+str(dispatchValue))
							system.tag.writeBlocking([UTDPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchRTNValue])
					else:   # must be 3-wire control so use both startDispatch and StopDispatch registers				
						if (dispatchValue == 1):
							system.tag.writeBlocking([UTDPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchValue])
							system.tag.writeBlocking([UTDPath + '/dispatch/stopDispatch'],[discreteDispatchControllerDispatchRTNValue])
						else:
							system.tag.writeBlocking([UTDPath + '/dispatch/startDispatch'],[discreteDispatchControllerDispatchRTNValue])
							system.tag.writeBlocking([UTDPath + '/dispatch/stopDispatch'],[discreteDispatchControllerDispatchValue])
		return

		
def doConnectivityCheck(tagPath):
		#constants
		ignitionDefaultDeviceOPCServerName = 'Ignition OPC UA Server'
		
		logger = system.util.getLogger("Connectivity Check")
		UDTInstancePath = tagPath.replace('/connectivityStatus','')
		parameters = getUDTParameters(UDTInstancePath)
		OPCServerToCheck =  extractParameterValue(parameters['opc_serverName'])
	#	logger.info("tagPath: " + tagPath + "     UDTInstancePath: " + UDTInstancePath)
		if (OPCServerToCheck == ignitionDefaultDeviceOPCServerName):
			#Using internal Ignition OPC server translation to a device driver for communication to asset
			opcDeviceToCheck =  extractParameterValue(parameters['opc_serverTopic']).split('[')[1].split(']')[0]
			devices = system.device.listDevices()
			devicesPy = system.dataset.toPyDataSet(devices)
			for row in devicesPy:
				if row['Name'] == OPCDeviceToCheck:
					deviceEnabled = row['Enabled']
					deviceConnected = (row['State'] == 'Connected')
					goodConnection = deviceEnabled and deviceConnected
					alarmConnection = deviceEnabled and not deviceConnected
					tagList = [tagPath + '/connectivityStatus',tagPath +'/connectivityInAlarm', tagPath + '/connectionEnabled']
					valueList = [goodConnection, alarmConnection, deviceEnabled]
					system.tag.writeBlocking(tagList, valueList)
					return
			logger.error ('Device:  ' + opcDeviceToCheck + " not found.")
			tagList = [tagPath + '/connectivityStatus',tagPath +'/connectivityInAlarm', tagPath + '/connectionEnabled']
			valueList = [0, 1, deviceEnabled]
			system.tag.writeBlocking(tagList, valueList)
			
		else:
			try:
				#Using external OPC Server for Communication to Asset
				serverEnabled = system.opc.isServerEnabled(OPCServerToCheck)
				serverConnected = system.opc.getServerState(OPCServerToCheck) == 'CONNECTED'
				goodConnection = serverEnabled and serverConnected
				alarmConnection = serverEnabled and not serverConnected
				tagList = [tagPath + '/connectivityStatus',tagPath +'/connectivityInAlarm', tagPath + '/connectionEnabled']
				valueList = [goodConnection, alarmConnection, serverEnabled]
				system.tag.writeBlocking(tagList, valueList)
				return
			except:
				logger.error ('OPC Server:  ' + OPCServerToCheck + " not found.")
				tagList = [tagPath + '/connectivityStatus',tagPath +'/connectivityInAlarm', tagPath + '/connectionEnabled']
				valueList = [0, 1,serverEnabled]
				

def doRepeatDispatchCommand(tagPath, tagName, newValue):
	logger = system.util.getLogger("Repeat Dispatch")
	logger.info('tagPath: '+tagPath+' .... '+'tagName: '+tagName+' .... '+'dispatchValue: '+str(newValue))
	if 'connectivityStatus' in tagPath:
		UDTInstancePath = tagPath.replace('/connectivityStatus/'+tagName,'')
	if 'dispatch' in tagPath:
		UDTInstancePath = tagPath.replace('/dispatch/'+tagName,'')
	UDTInstancePathParts = UDTInstancePath.split('/')
	UDTInstanceName = UDTInstancePathParts[len(UDTInstancePathParts)-1]
	parameters = getUDTParameters(UDTInstancePath)

	dispatchManualDispatchEnable = int(system.tag.readBlocking([UDTInstancePath + '/dispatch/_dispatchManualDispatchEnable'])[0].value)
	isAnalogDispatch = int(extractParameterValue(parameters['config_isAnalogDispatch']))
	isDiscreteDispatch = int(extractParameterValue(parameters['config_isDiscreteDispatch']))
	kafka_devicePathPrefix = extractParameterValue(parameters['kafka_devicePathPrefix'])
	print kafka_devicePathPrefix
	kafka_tenant = extractParameterValue(parameters['kafka_tenant'])
	flex_dispatchCommandTag = extractParameterValue(parameters['flex_dispatchCommandTag'])
	flex_analogDispatchSetpointTag = extractParameterValue(parameters['flex_dispatchSetpointTag'])
	dispatchManualDispatchCommand = system.tag.readBlocking([UDTInstancePath + '/dispatch/_dispatchManualDispatch'])[0].value
	logger.info('good 1')	
	if (dispatchManualDispatchEnable == 0):
		if (isAnalogDispatch == 1):
			analogDispatchSetpoint = int(system.tag.readBlocking([kafka_devicePathPrefix + kafka_tenant +'/' + UDTInstanceName +'/' + flex_analogDispatchSetpointTag])[0].value)
			doAnalogDispatch(tagPath, tagName, tagPath.replace('/connectivityStatus/'+tagName,''), analogDispatchSetpoint)
		elif (isDiscreteDispatch == 1):
			logger.info('good 2')	
			print kafka_devicePathPrefix + kafka_tenant +'/' + UDTInstanceName +'/' + flex_dispatchCommandTag
			discreteDispatchCommand = int(system.tag.readBlocking([kafka_devicePathPrefix + kafka_tenant +'/' + UDTInstanceName +'/' + flex_dispatchCommandTag])[0].value)
			doDiscreteDispatch(tagPath, tagName, UDTInstancePath , discreteDispatchCommand)
	else:
		doManualDispatch(tagPath, tagName,UDTInstancePath, dispatchManualDispatchCommand)




def buildTree(opcServerName,opcNodeID):
	logger = system.util.getLogger('Build Tree')
	nodes = system.opc.browseServer(opcServerName,opcNodeID)
	branch = []
	for node in nodes:
		#		leaf = buildTree(opcServerName,nodeID)
		if opcNodeID == '':
			logger.info(node.getNodeId())
			limb = {'label': node.getDisplayName(),
				'expanded': False,
#				'data': {'nodeID':node.getServerNodeId(), 'namespace': getServerNamespace(node.getServerNodeId())},
				'data': {'nodeID':node.getNodeId(), 'namespace': node.getNodeId().split(';')[0]},
				'items': []
				 }
			branch.append(limb)
		else:
			limb = {'label': node.getDisplayName(),
					'expanded': False,
					'data': {'nodeID':node.getNodeId()},
					'items': []
					 }
			branch.append(limb)
	return branch

