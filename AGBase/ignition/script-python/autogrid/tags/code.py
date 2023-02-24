

def tag_tree(path, filter):
	'''
	Adapted from https://forum.inductiveautomation.com/t/how-to-make-a-tag-browse-tree-in-perspective/24997
	Used to populate a datatstructure to recursively make a perspecitve tag tree given the path to start at
	'''
	tagTreeList = []
	if filter is None:
		filter = []
	
	# Browse the curent path.		
	results = system.tag.browse(path)
	
	# Add each tag that was found to a new item.
	for result in results.getResults():
		if len(filter) > 0 and not result['name'] in filter:
			continue
			
		newItem = {}
		newItem['label'] = result['name']
		newItem['data'] = result['fullPath']
		
		# If the tag has children, browse and add each of the children to the item.
		if result['hasChildren']:
			newItem['items'] = tag_tree(result['fullPath'], []) # remove filter here or we won't get the children
		
		# Once all children have been added to the item, add the new item to the list.
		tagTreeList.append(newItem.copy())
	
	# After all items under the path have been added to the list, return the list.	
	return tagTreeList


def add_hb_destination(new_hb, secs):
	'''
	Append the given new_hb to the list of heartbeat destinations with the given number of seconds between heartbeats
	'''
	if secs not in {4,10,30}:
		raise(Exception("Heartbeat must be 4, 10, or 30 seconds"))
		
	hb_dests="[default]AutoGrid/HB_OUT_DESTINATIONS"
	
	dests=system.tag.readBlocking([hb_dests])[0].value
	dests=system.dataset.addRow(dests, ["[default]AutoGrid/HB"+str(secs)+"s", new_hb])
	system.tag.writeBlocking([hb_dests], [dests])


def send_hb_destinations(hb_tag, value):
	'''
	Get an array of all of the destinations for the given heartbeat tag
	'''
	retval=[]
	values=[]
	dests=system.tag.readBlocking(["[default]AutoGrid/HB_OUT_DESTINATIONS"])[0].value
	py_dests=system.dataset.toPyDataSet(dests)
	for hb, dest in py_dests:
		if hb == hb_tag:
			retval.append(dest)
			values.append(value)
	system.tag.writeAsync(retval, values, None)


def init_tags():
	'''
	To be called on gateway startup, check for common tags and if missing, create them from the JSON here 
	Use the merge strategy for updating the tag list
	'''
	collisionPolicy = "o" 
	
	tags = [
		{
			"name": "AutoGrid",
			"tagType": "Folder"
		},
		{
		  "name": "BreakerDevice",
		  "parameters": {
			"kV": ""
		  },
		  "tagType": "UdtType",
		  "tags": [
			{
			  "value": {
				"bindType": "parameter",
				"binding": "{kV}"
			  },
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "Nominal_kV",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "alarms": [
				{
				  "name": "BreakerOpen",
				  "priority": "High"
				}
			  ],
			  "name": "BRKR_CLOSED",
			  "value": False,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "name": "BRKR_CLS",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "name": "BRKR_OPE",
			  "tagType": "AtomicTag"
			}
		  ]
		},
		{
		  "name": "HBDevice",
		  "typeId": "",
		  "tagType": "UdtType",
		  "tags": [
			{
			  "valueSource": "memory",
			  "name": "HB_IN",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "expr",
			  "expression": "if(isGood({[.]HB_IN.Quality}) && secondsBetween({[.]HB_IN.Timestamp}, now()) < {[.]HB_STALE_DELAY}, True, False)",
			  "dataType": "Boolean",
			  "alarms": [
				{
				  "name": "HeartbeatAlarm",
				  "priority": "High"
				}
			  ],
			  "name": "HB_GOOD",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "name": "HB_OUT",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "name": "HB_STALE_DELAY",
			  "value": 30,
			  "tagType": "AtomicTag"
			}
		  ]
		},
		{
		  "name": "BinaryDevice",
		  "typeId": "AutoGrid/HBDevice",
		  "tagType": "UdtType",
		  "tags": [
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "sourceTagPath": "",
			  "name": "RTCC_DR_DEPLOY",
			  "value": False,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_STALE_DELAY",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "LOAD_POWER_ACTUAL",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_OUT",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_GOOD",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "GEN_POWER_ACTUAL",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_IN",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "name": "RTCC_DR_PREACTION",
			  "value": False,
			  "tagType": "AtomicTag"
			}
		  ]
		},
		{
		  "name": "SimpleBattery",
		  "typeId": "AutoGrid/HBDevice",
		  "tagType": "UdtType",
		  "tags": [
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "name": "REMOTE_STATUS",
			  "value": True,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_STALE_DELAY",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "AssetSettings",
			  "tagType": "Folder",
			  "tags": [
				{
				  "valueSource": "memory",
				  "name": "META_USABLE_ENERGY",
				  "value": 0,
				  "tagType": "AtomicTag"
				},
				{
				  "valueSource": "memory",
				  "name": "META_MAX_DISCHARGE",
				  "value": 0,
				  "tagType": "AtomicTag"
				},
				{
				  "valueSource": "memory",
				  "name": "META_MAX_CHARGE",
				  "value": 0,
				  "tagType": "AtomicTag"
				},
				{
				  "valueSource": "memory",
				  "name": "META_TOTAL_ENERGY",
				  "value": 0,
				  "tagType": "AtomicTag"
				}
			  ]
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "GEN_POWER_ACTUAL",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "REACTIVE_POWER_ACTUAL",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_OUT",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_IN",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "SOE_ABS_ACTUAL",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "SET_POINT_ABS",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "name": "SET_POINT_CONF_ABS",
			  "value": 0,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_GOOD",
			  "tagType": "AtomicTag"
			}
		  ]
		},
		{
		  "name": "PV",
		  "tagType": "UdtType",
		  "tags": [
		    {
		      "valueSource": "memory",
		      "dataType": "Float8",
		      "name": "REACTIVE_POWER_ACTUAL",
		      "tagType": "AtomicTag"
		    },
		    {
		      "valueSource": "memory",
		      "dataType": "Float8",
		      "name": "GEN_POWER_ACTUAL",
		      "tagType": "AtomicTag"
		    },
		    {
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "SET_POINT_ABS",
			  "tagType": "AtomicTag"
			}
		  ]
		},
				{
		  "name": "ExtendedBattery",
		  "typeId": "AutoGrid/SimpleBattery",
		  "tagType": "UdtType",
		  "tags": [
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "alarms": [
				{
				  "setpointA": 1.0,
				  "name": "HeavyAlarm",
				  "priority": "High"
				}
			  ],
			  "value": False,
			  "name": "BESS_HEAVY_ALARM",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "alarms": [
				{
				  "setpointA": 1.0,
				  "name": "LightAlarm"
				}
			  ],
			  "value": False,
			  "name": "BESS_LIGHT_ALARM",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_GOOD",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "SET_POINT_ABS",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "REMOTE_STATUS",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "AuxBreaker",
			  "typeId": "AutoGrid/BreakerDevice",
			  "tagType": "UdtInstance",
			  "tags": [
				{
				  "name": "BRKR_OPE",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_CLS",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "Nominal_kV",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_CLOSED",
				  "tagType": "AtomicTag"
				}
			  ]
			},
			{
			  "name": "GEN_POWER_ACTUAL",
			  "tagType": "AtomicTag",
			  "value": 0.0
			},
			{
			  "name": "AuxMeter",
			  "tagType": "Folder",
			  "tags": [
				{
				  "valueSource": "memory",
				  "dataType": "Float8",
				  "name": "LOAD_POWER_ACTUAL",
				  "tagType": "AtomicTag",
				  "value": 0.0
				}
			  ]
			},
			{
			  "name": "HB_STALE_DELAY",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_IN",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "SOE_ABS_ACTUAL",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "SET_POINT_CONF_ABS",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "expr",
			  "dataType": "Boolean",
			  "expression": "if( {[.]HB_GOOD} && isGood({[.]GEN_POWER_ACTUAL.Quality}) && isGood({[.SET_POINT_ABS.Quality}), True, False)",
			  "alarms": [
				{
				  "setpointA": 0.0,
				  "timeOnDelaySeconds": 5.0,
				  "name": "ControllerHealthAlarm",
				  "priority": "High"
				}
			  ],
			  "name": "CONTROLLER_HEALTH",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Boolean",
			  "alarms": [
				{
				  "setpointA": 1.0,
				  "name": "MediumAlarm",
				  "priority": "Medium"
				}
			  ],
			  "value": False,
			  "name": "BESS_MED_ALARM",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "AssetSettings",
			  "tagType": "Folder",
			  "tags": [
				{
				  "name": "META_MAX_CHARGE",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "META_TOTAL_ENERGY",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "META_USABLE_ENERGY",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "META_MAX_DISCHARGE",
				  "tagType": "AtomicTag"
				}
			  ]
			},
			{
			  "name": "HB_OUT",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "MainBreaker",
			  "typeId": "AutoGrid/BreakerDevice",
			  "parameters": {
				"kV": ""
			  },
			  "tagType": "UdtInstance",
			  "tags": [
				{
				  "name": "BRKR_CLOSED",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "Nominal_kV",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_OPE",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_CLS",
				  "tagType": "AtomicTag"
				}
			  ]
			}
		  ]
		},
				{
		  "name": "DroopBattery",
		  "typeId": "AutoGrid/ExtendedBattery",
		  "parameters": {
			"NOMINAL_FREQUENCY": ""
		  },
		  "tagType": "UdtType",
		  "tags": [
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "DROOP_HIGH_START_HZ",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "PCCMeter",
			  "tagType": "Folder",
			  "tags": [
			    {
			      "valueSource": "memory",
			      "dataType": "Float8",
			      "name": "GEN_POWER_ACTUAL",
			      "tagType": "AtomicTag"
			    }
			  ]
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "DROOP_LOW_MAX_POWER",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "BESS_MED_ALARM",
			  "tagType": "AtomicTag",
			  "value": False
			},
			{
			  "name": "BESS_HEAVY_ALARM",
			  "tagType": "AtomicTag",
			  "value": False
			},
			{
			  "name": "AuxMeter",
			  "tagType": "Folder",
			  "tags": [
				{
				  "name": "LOAD_POWER_ACTUAL",
				  "tagType": "AtomicTag",
				  "value": 0.0
				}
			  ]
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "DROOP_LOW_STOP_HZ",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "FREQUENCY",
			  "formatString": "#,##0.####",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "SET_POINT_CONF_ABS",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "AuxBreaker",
			  "tagType": "UdtInstance",
			  "tags": [
				{
				  "name": "Nominal_kV",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_CLS",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_OPE",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_CLOSED",
				  "tagType": "AtomicTag"
				}
			  ]
			},
			{
			  "name": "SOE_ABS_ACTUAL",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "SET_POINT_ABS",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_OUT",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "CONTROLLER_HEALTH",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "DROOP_LOW_START_HZ",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "DROOP_HIGH_MAX_POWER",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "GEN_POWER_ACTUAL",
			  "tagType": "AtomicTag",
			  "value": 0.0
			},
			{
			  "name": "REMOTE_STATUS",
			  "tagType": "AtomicTag",
			  "value": True
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "DROOP_NOMINAL_FREQ",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_STALE_DELAY",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Float8",
			  "name": "DROOP_HIGH_STOP_HZ",
			  "value": 0.0,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "name": "DROOP_SPT_MODE",
			  "value": 0,
			  "tagType": "AtomicTag"
			},
			{
			  "name": "AssetSettings",
			  "tagType": "Folder",
			  "tags": [
				{
				  "name": "META_MAX_DISCHARGE",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "META_MAX_CHARGE",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "META_USABLE_ENERGY",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "META_TOTAL_ENERGY",
				  "tagType": "AtomicTag"
				}
			  ]
			},
			{
			  "name": "BESS_LIGHT_ALARM",
			  "tagType": "AtomicTag",
			  "value": False
			},
			{
			  "name": "MainBreaker",
			  "tagType": "UdtInstance",
			  "tags": [
				{
				  "name": "BRKR_CLS",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_OPE",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "BRKR_CLOSED",
				  "tagType": "AtomicTag"
				},
				{
				  "name": "Nominal_kV",
				  "tagType": "AtomicTag"
				}
			  ]
			},
			{
			  "name": "HB_GOOD",
			  "tagType": "AtomicTag"
			},
			{
			  "name": "HB_IN",
			  "tagType": "AtomicTag"
			}
		  ]
		},
		{
		  "name": "PVBattery",
		  "typeId": "AutoGrid/DroopBattery",
		  "tagType": "UdtType",
		  "tags": [
		    {
		      "name": "PV",
		      "typeId": "AutoGrid/PV",
		      "tagType": "UdtInstance",
		      "tags": [
		        {
		          "name": "REACTIVE_POWER_ACTUAL",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "GEN_POWER_ACTUAL",
		          "tagType": "AtomicTag",
		          "value": 0.0
		        }
		      ]
		    },
		    {
		      "name": "PCCMeter",
		      "tagType": "Folder",
		      "tags": [
		        {
		          "valueSource": "memory",
		          "dataType": "Float8",
		          "name": "LOAD_POWER_ACTUAL",
		          "tagType": "AtomicTag",
		          "value": 0.0
		        }
		      ]
		    },
		    {
		      "valueSource": "memory",
		      "dataType": "DataSet",
		      "name": "VOLT_VAR_CURVE",
		      "value": "{\"columns\":[{\"name\":\"pct_voltage\",\"type\":\"java.lang.Integer\"},{\"name\":\"pct_VAR\",\"type\":\"java.lang.Integer\"}],\"rows\":[]}",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "DROOP_HIGH_STOP_HZ",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "AuxBreaker",
		      "tagType": "UdtInstance",
		      "tags": [
		        {
		          "name": "Nominal_kV",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "BRKR_CLS",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "BRKR_OPE",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "BRKR_CLOSED",
		          "tagType": "AtomicTag"
		        }
		      ]
		    },
		    {
		      "name": "FREQUENCY",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "HB_OUT",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "SiteLoad",
		      "typeId": "AutoGrid/BinaryDevice",
		      "tagType": "UdtInstance",
		      "tags": [
		        {
		          "name": "RTCC_DR_PREACTION",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "HB_GOOD",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "RTCC_DR_DEPLOY",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "GEN_POWER_ACTUAL",
		          "tagType": "AtomicTag",
		          "value": 0.0
		        },
		        {
		          "name": "HB_OUT",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "LOAD_POWER_ACTUAL",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "HB_IN",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "HB_STALE_DELAY",
		          "tagType": "AtomicTag"
		        }
		      ]
		    },
		    {
		      "name": "REMOTE_STATUS",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "DROOP_LOW_MAX_POWER",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "HB_GOOD",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "SET_POINT_ABS",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "HB_STALE_DELAY",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "BESS_MED_ALARM",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "MainBreaker",
		      "tagType": "UdtInstance",
		      "tags": [
		        {
		          "name": "BRKR_CLOSED",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "BRKR_OPE",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "Nominal_kV",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "BRKR_CLS",
		          "tagType": "AtomicTag"
		        }
		      ]
		    },
		    {
		      "name": "SOE_ABS_ACTUAL",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "SET_POINT_CONF_ABS",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "AuxMeter",
		      "tagType": "Folder",
		      "tags": [
		        {
		          "name": "LOAD_POWER_ACTUAL",
		          "tagType": "AtomicTag",
		          "value": 0.0
		        }
		      ]
		    },
		    {
		      "name": "GEN_POWER_ACTUAL",
		      "tagType": "AtomicTag",
		      "value": 0.0
		    },
		    {
		      "name": "BESS_LIGHT_ALARM",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "DROOP_LOW_STOP_HZ",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "CONTROLLER_HEALTH",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "AssetSettings",
		      "tagType": "Folder",
		      "tags": [
		        {
		          "name": "META_USABLE_ENERGY",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "META_MAX_DISCHARGE",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "META_MAX_CHARGE",
		          "tagType": "AtomicTag"
		        },
		        {
		          "name": "META_TOTAL_ENERGY",
		          "tagType": "AtomicTag"
		        }
		      ]
		    },
		    {
		      "name": "DROOP_HIGH_MAX_POWER",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "DROOP_SPT_MODE",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "DROOP_LOW_START_HZ",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "DROOP_HIGH_START_HZ",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "BESS_HEAVY_ALARM",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "HB_IN",
		      "tagType": "AtomicTag"
		    },
		    {
		      "name": "DROOP_NOMINAL_FREQ",
		      "tagType": "AtomicTag"
		    }
		  ]
		}, # end UDTs 
		{
		  "name": "Sims",
		  "tagType": "Folder",
		},
		{
		  "valueSource": "memory",
		  "dataType": "DataSet",
		  "name": "BattSims",
		  "value": "{\"columns\":[{\"name\":\"path\",\"type\":\"java.lang.String\"},{\"name\":\"energy\",\"type\":\"java.lang.Integer\"},{\"name\":\"power\",\"type\":\"java.lang.Integer\"},{\"name\":\"name\",\"type\":\"java.lang.String\"}],\"rows\":[]}",
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "memory",
		  "dataType": "DataSet",
		  "basePath": "[default]AutoGrid",
		  "name": "DRSims",
		  "value": "{\"columns\":[{\"name\":\"path\",\"type\":\"java.lang.String\"},{\"name\":\"name\",\"type\":\"java.lang.String\"},{\"name\":\"normal\",\"type\":\"java.lang.Integer\"},{\"name\":\"shed\",\"type\":\"java.lang.Integer\"}],\"rows\":[]}",
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "memory",
		  "dataType": "DataSet",
		  "name": "HMISites",
		  "value": "{\"columns\":[{\"name\":\"name\",\"type\":\"java.lang.String\"},{\"name\":\"path\",\"type\":\"java.lang.String\"},{\"name\":\"hmi\",\"type\":\"java.lang.String\"},{\"name\":\"control\",\"type\":\"java.lang.String\"}],\"rows\":[]}",
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "expr",
		  "eventScripts": [
			{
			  "eventid": "valueChanged",
			  "script": "\tautogrid.sims.do_batt_sim()"
			}
		  ],
		  "expression": "if( getSecond(now()) % 2 = 0, 1, 0)",
		  "basePath": "[default]AutoGrid",
		  "name": "HB1s",
		  "value": 0,
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "expr",
		  "eventScripts": [
			{
			  "eventid": "valueChanged",
			  "script": "\tautogrid.sims.do_dr_sim()\n\tautogrid.tags.send_hb_destinations(tagPath, currentValue)"
			}
		  ],
		  "expression": "if( getSecond(now()) % 4 = 0, 1, 0)",
		  "basePath": "[default]AutoGrid",
		  "name": "HB4s",
		  "value": 0, 
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "expr",
		  "expression": "(getSecond(now()) > 9 && getSecond(now()) < 20) || (getSecond(now()) > 29 && getSecond(now()) < 40) || (getSecond(now()) > 49)",
		  "basePath": "[default]AutoGrid",
		  "name": "HB10s",
		  "value": 0,
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "expr",
		  "expression": "getSecond(now()) > 30",
		  "basePath": "[default]AutoGrid",
		  "name": "HB30s",
		  "value": 0,
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "expr",
		  "eventScripts": [
			{
			  "eventid": "valueChanged",
			  "script": "\tautogrid.sims.do_pv_sim()"
			}
		  ],
		  "expression": "if(getMinute(now()) % 2 = 0, 1 , 0)",
		  "basePath": "[default]AutoGrid",
		  "name": "HB60s",
		  "value": 0,
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "memory",
		  "basePath": "[default]AutoGrid",
		  "name": "ENABLE_MQTT_AUTOCREATE",
		  "dataType": "Boolean",
		  "value": False,
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "memory",
		  "dataType": "DataSet",
		  "name": "HB_OUT_DESTINATIONS",
		  "value": "{\"columns\":[{\"name\":\"HB\",\"type\":\"java.lang.String\"},{\"name\":\"dest\",\"type\":\"java.lang.String\"}],\"rows\":[]}",
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "memory",
		  "dataType": "DataSet",
		  "name": "PVSims",
		  "value": "{\"columns\":[{\"name\":\"path\",\"type\":\"java.lang.String\"},{\"name\":\"name\",\"type\":\"java.lang.String\"},{\"name\":\"sunup_hr\",\"type\":\"java.lang.Integer\"},{\"name\":\"sundown_hr\",\"type\":\"java.lang.Integer\"},{\"name\":\"size\",\"type\":\"java.lang.Integer\"}],\"rows\":[]}",
		  "tagType": "AtomicTag"
		},
		{
		  "valueSource": "memory",
		  "dataType": "String",
		  "name": "Environment",
		  "value": "dev",
		  "tagType": "AtomicTag"
		},
		{
		  "name": "Monitoring",
		  "tagType": "Folder",
		  "tags": [
		    {
		      "valueSource": "memory",
		      "dataType": "StringArray",
		      "name": "AlertEnabledOPCConnections",
		      "value": [],
		      "tagType": "AtomicTag"
		    },
		    {
		      "valueSource": "memory",
		      "dataType": "StringArray",
		      "name": "AlertingOPCConnections",
		      "value": [],
		      "tagType": "AtomicTag"
		    },
		    {
		      "valueSource": "memory",
		      "dataType": "StringArray",
		      "name": "AlertEnabledDevices",
		      "value": [],
		      "tagType": "AtomicTag"
		    },
		    {
		      "valueSource": "memory",
		      "dataType": "StringArray",
		      "name": "AlertingDevices",
		      "value": [],
		      "tagType": "AtomicTag"
		    }
		  ]
		},
		{
		  "valueSource": "memory",
		  "dataType": "String",
		  "name": "PagerDutyServiceKey",
		  "value": "",
		  "tagType": "AtomicTag"
		},
		{
		  "name": "TenantCredentials",
		  "tagType": "Folder",
		  "tags": []
		}
	]
	for tag in tags:
		basePath = "[default]AutoGrid"
		if tag["name"] == "AutoGrid":
			basePath = "[default]"
		if not system.tag.exists(basePath+"/"+tag['name']):
			system.tag.configure(basePath, [tag], collisionPolicy)
	
	# set up simulators 
	#autogrid.sims.add_simulator('dr', "STONECRUSHER", "[default]AutoGrid/Sims",normal=4500, shed=1000)
	#autogrid.sims.add_simulator('batt', "DEMOBATT", "[default]AutoGrid/Sims",power=1000, energy=2000)


def add_tenant_tree(tenant):
	'''
	Add the tags representing a tenant's tag tree
	'''
	tags={
	  "name": tenant,
	  "tagType": "Folder",
	  "tags": [
		{
		  "name": "ErrorTracking",
		  "tagType": "Folder",
		  "tags": [
			{
			  "valueSource": "memory",
			  "dataType": "Int4",
			  "name": "FlexAPICallFailed",
			  "value": 0,
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "Int4",
			  "name": "EventAPICallFailed",
			  "value": 0,
			  "tagType": "AtomicTag"
			}
		  ]
		}
	  ]
	}
	system.tag.configure("[default]"+tenant, [tags], "i")	    


def add_tenant_credentials(tenant):
	'''
	Add the tag structure to store a tenant's credentials
	'''
	if not autogrid.ui.is_valid_new_tenant(tenant):
		return
		
	tags={
		  "name": tenant,
		  "tagType": "Folder",
		  "tags": [
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "Flex_FERM_API_Token",
			  "value": "",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "DROMS_Meta_API_Username",
			  "value": "dev_api_user",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "DROMS_API_URL",
			  "value": "https://dev-droms-internal.ks.autogridsystems.net",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "Flex_API_URL",
			  "value": "https://dev-internal.ks.autogridsystems.net",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "DROMS_API_Username",
			  "value": "api_test",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "Flex_TS_API_Password",
			  "value": "",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "DROMS_Meta_API_Password",
			  "value": "",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "DROMS_API_Password",
			  "value": "",
			  "tagType": "AtomicTag"
			},
			{
			  "valueSource": "memory",
			  "dataType": "String",
			  "name": "Flex_TS_API_Username",
			  "value": "connectorsuser",
			  "tagType": "AtomicTag"
			}
		  ]
		}
	system.tag.configure("[default]AutoGrid/TenantCredentials", [tags], "i")


def update_agbase_version(version):
	tag={
	  "valueSource": "memory",
	  "dataType": "String",
	  "name": "AGBaseVersion",
	  "value": version,
	  "tagType": "AtomicTag"
	}
	
	system.tag.configure("[default]AutoGrid", [tag], "i")