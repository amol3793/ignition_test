import re


def populate_reading_table(value):
	'''
	Populate the reading table in a ReadingTable or similar view
	'''
	ret=[]
	results = system.tag.browse(path = value, filter = {'tagType':'AtomicTag'})
	for result in results.getResults():
		config=system.tag.getConfiguration(result['fullPath'])[0]
		element={
			'instanceStyle': {'classes':{}},
			'instancePosition': {},
			'path': result['fullPath'],
			'label': result['name'],
			'units': "",
			'format': "0.00",
			"type": "Float",
			"tooltip": ""
		}
		if "engUnit" in config.keys():
			element["units"]=config["engUnit"]
		if "formatString" in config.keys():
			element["format"]=config['formatString']
		if "dataType" in config.keys():
			element["type"]=str(config['dataType'])
		if "tooltip" in config.keys():
			element["tooltip"]=str(config['tooltip'])
			
		ret.append(element)
	return ret


def is_valid_new_tenant(name):
	'''
	Return whether or not thie given name is a valid new tenant name
	'''
	if system.tag.exists("[default]AutoGrid/TenantCredentials/"+name):
		return False
		
	if name is None or name == "":
		return False
	
	rx=re.compile(r'^\w+$')
	if rx.match(name):
		return True
	else:
		return False

