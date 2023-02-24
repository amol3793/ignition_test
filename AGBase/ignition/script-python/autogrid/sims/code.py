import random
import math


def add_noise(meter, factor=0.05):
	return meter-random.randint(0,int(abs(meter*factor)))


def add_simulator(type, name, path, normal=0, shed=0, power=0, energy=0, pv=0):
	'''
	Add the given simulator of the given type ("batt", "batt+pv", or "dr") under the given tag path with the given name
	additional params for dr resources are: normal and shed (normal for PV is the max power output, shed is unused)
	for batteries: power and energy 
	for batteries with solar, power, energy, and pv (size)
	
	return if the path already exists
	'''
	# check for sim already present, tag path is the authoritative source
	search = system.tag.browse(path = path, filter = {'name':name})
	if search is not None and search.getReturnedSize() > 0:
		return
	
	# instantiate create UDT
	typeId = ""
	params= {}
	
	if type == "dr":
		typeId = "AutoGrid/BinaryDevice"
	else:
		if type == 'batt+pv':
			typeId = "AutoGrid/PVBattery"
		else:
			typeId = "AutoGrid/DroopBattery"
				
		params = {
			'NOMINAL_FREQUENCY': 60,
			'META_TOTAL_ENERGY': energy,
			'META_USABLE_ENERGY': energy,
			'META_MAX_CHARGE': -power,
			'META_MAX_DISCHARGE': power
		}
	
	tag = {
		"name": name,         
		"typeId" : typeId,
		"tagType" : "UdtInstance",
		"parameters" : params
		}
	
	# Create the UDT
	system.tag.configure(path, [tag], "a")
	
	# add to sims DataSet tag
	sims_tag="[default]AutoGrid/"
	if type == "dr":
		sims_tag+="DRSims"
		sims=system.tag.readBlocking([sims_tag])[0].value
		sims=system.dataset.addRow(sims, [path+"/"+name, name, normal, shed])
		system.tag.writeBlocking([sims_tag], [sims])
	else:
		sims_tag+="BattSims"
		sims=system.tag.readBlocking([sims_tag])[0].value
		sims=system.dataset.addRow(sims, [path+"/"+name, energy, power, name])
		system.tag.writeBlocking([sims_tag], [sims])
		
		if type == "batt+pv":
			sims_tag="[default]AutoGrid/PVSims"
			sims=system.tag.readBlocking([sims_tag])[0].value
			sims=system.dataset.addRow(sims, [path+"/"+name+"/PV", name, 9, 17, pv])
			system.tag.writeBlocking([sims_tag], [sims])
	
	# add to HMI list
	hmi_tag="[default]AutoGrid/HMISites"
	hmi=system.tag.readBlocking([hmi_tag])[0].value
	if type == "dr":
		hmi=system.dataset.addRow(hmi, [name, path+"/"+name, "Page/OneLines/NoneSelected", "Page/OneLines/NoneSelected", ""])
	else:
		if type == "batt":
			hmi=system.dataset.addRow(hmi, [name, path+"/"+name, "Page/OneLines/SINGLEBATT", "Page/Embedded/ControlViews/DroopBattery", ""])
		else:
			hmi=system.dataset.addRow(hmi, [name, path+"/"+name, "Page/OneLines/SINGLEBATTWithPV", "Page/Embedded/ControlViews/DroopBattery", ""])
	
	system.tag.writeBlocking([hmi_tag], [hmi])
	
	# add HB
	autogrid.tags.add_hb_destination(path+"/"+name+"/HB_OUT", 4)


def do_dr_sim():
	sims=system.tag.readBlocking(["[default]AutoGrid/DRSims"])[0]
	for sim in system.dataset.toPyDataSet(sims.value):
		path_base=sim[0]
		load_normal=sim[2]
		shed_amt=sim[3]

		meter=load_normal
		read_tags=system.tag.readBlocking([path_base+"/RTCC_DR_DEPLOY",path_base+"/HB_OUT"])
		deployed=read_tags[0].value
		hb=read_tags[1].value

		if deployed:
			meter=meter-shed_amt

		meter=add_noise(meter)
		system.tag.writeBlocking([path_base+"/LOAD_POWER_ACTUAL", path_base+"/HB_IN"], [meter, hb])


def do_batt_sim():
	SECOND_RATIO=1.0/(60.0*60.0) # one second expressed as a fraction of an hour, used for energy rate calc, only works if this fires every second
	sims=system.tag.readBlocking(["[default]AutoGrid/BattSims"])[0]
	for sim in system.dataset.toPyDataSet(sims.value):
		path_base=sim[0]
		energy=sim[1]
		power=sim[2]
	
		meter = 0
		
		base_values=system.tag.readBlocking(
			[
				path_base+"/REMOTE_STATUS",
				path_base+"/HB_OUT",
				path_base+"/DROOP_SPT_MODE",
				path_base+"/SET_POINT_ABS",
				path_base+"/SOE_ABS_ACTUAL"
			])
		
		locRem=base_values[0].value
		hb=base_values[1].value
		mode=1
		type=system.tag.getConfiguration(path_base, False)[0]['typeId']
		
		mode=base_values[2].value
		spt=base_values[3].value
		kWh=base_values[4].value
		
		if locRem:			
			if mode == 2:
				# spt mode, pass through
				spt=spt
			elif mode == 0:
				# no mode, stop
				spt = 0
			elif mode == 1:
				droop_values=system.tag.readBlocking(
					[
						path_base+"/FREQUENCY",
						path_base+"/DROOP_NOMINAL_FREQ", 
						
						path_base+"/DROOP_LOW_STOP_HZ", 
						path_base+"/DROOP_LOW_START_HZ", 
						path_base+"/DROOP_LOW_MAX_POWER",
						
						path_base+"/DROOP_HIGH_STOP_HZ", 
						path_base+"/DROOP_HIGH_START_HZ", 
						path_base+"/DROOP_HIGH_MAX_POWER",
					])
				
				FREQUENCY=droop_values[0].value
				DROOP_NOMINAL_FREQ=droop_values[1].value
				
				DROOP_LOW_STOP_HZ=droop_values[2].value
				DROOP_LOW_START_HZ=droop_values[3].value
				DROOP_LOW_MAX_POWER=droop_values[4].value
				
				DROOP_HIGH_STOP_HZ=droop_values[5].value
				DROOP_HIGH_START_HZ=droop_values[6].value
				DROOP_HIGH_MAX_POWER=droop_values[7].value
				
				if FREQUENCY > DROOP_NOMINAL_FREQ:
					if (FREQUENCY - DROOP_NOMINAL_FREQ) >= DROOP_HIGH_START_HZ and (FREQUENCY - DROOP_NOMINAL_FREQ) <= DROOP_HIGH_STOP_HZ:
						slope = (FREQUENCY - DROOP_NOMINAL_FREQ - DROOP_HIGH_START_HZ) / (DROOP_HIGH_STOP_HZ - DROOP_HIGH_START_HZ)
						spt = spt + max(DROOP_HIGH_MAX_POWER, slope * DROOP_HIGH_MAX_POWER)
					elif (FREQUENCY - DROOP_NOMINAL_FREQ) > DROOP_HIGH_STOP_HZ:
						spt = spt + DROOP_HIGH_MAX_POWER
				
				elif FREQUENCY < DROOP_NOMINAL_FREQ:
					if (FREQUENCY - DROOP_NOMINAL_FREQ) <= DROOP_LOW_START_HZ and (FREQUENCY - DROOP_NOMINAL_FREQ) >= DROOP_LOW_STOP_HZ:
						slope = (FREQUENCY - DROOP_NOMINAL_FREQ - DROOP_LOW_START_HZ) / (DROOP_LOW_STOP_HZ - DROOP_LOW_START_HZ)
						spt = spt + min(DROOP_LOW_MAX_POWER, slope * DROOP_LOW_MAX_POWER)
					elif (FREQUENCY - DROOP_NOMINAL_FREQ) < DROOP_LOW_STOP_HZ:
						spt = spt + DROOP_LOW_MAX_POWER
					
				elif FREQUENCY == DROOP_NOMINAL_FREQ:
					spt = spt
			elif mode == 3:
				# PV smooth
				# we hid what the PV should be in the REACTIVE_POWER_ACTUAL field on the PV
				pv_target=system.tag.readBlocking([path_base+"/PV/REACTIVE_POWER_ACTUAL"])[0].value
				pv_actual=system.tag.readBlocking([path_base+"/PV/GEN_POWER_ACTUAL"])[0].value
				spt=spt+(pv_target-pv_actual)
			
			if spt > power:
				spt = power
			elif spt < -power:
				spt = -power

			if (spt < 0 and kWh < energy) or (spt > 0 and kWh > 0):			
				increment_kWh = spt * SECOND_RATIO
				kWh -= increment_kWh
				
				meter=spt
			elif kWh <= 0 or kWh >= energy:
				# auto-reset SoC if it hits UOL or LOL
				kWh = energy/2.0
					
			system.tag.writeBlocking([path_base+"/SET_POINT_CONF_ABS", path_base+"/SOE_ABS_ACTUAL"], [spt, kWh])
		else:
			system.tag.writeBlocking([path_base+"/SET_POINT_CONF_ABS"], [0.0])
			spt=0
		
		system.tag.writeBlocking([
			path_base+"/GEN_POWER_ACTUAL", 
			path_base+"/AssetSettings/META_MAX_DISCHARGE", 
			path_base+"/AssetSettings/META_MAX_CHARGE",
			path_base+"/AssetSettings/META_USABLE_ENERGY", 
			path_base+"/AssetSettings/META_TOTAL_ENERGY", 
			path_base+"/HB_IN",
			path_base+"/MainBreaker/BRKR_CLOSED",
			path_base+"/AuxBreaker/BRKR_CLOSED",
			], 
			[meter, power, -power, energy, energy, hb, True, True])
		
		if type == 'AutoGrid/PVBattery':
			# compute site PCC value from negative of bettery (to go from GEN to LOAD), PV, and site load
			other_tags=system.tag.readBlocking([path_base+"/AuxMeter/LOAD_POWER_ACTUAL", path_base+"/PV/GEN_POWER_ACTUAL", path_base + "/SiteLoad/LOAD_POWER_ACTUAL"])
			pcc=-meter+other_tags[0].value-other_tags[1].value+other_tags[2].value
			
			system.tag.writeBlocking([path_base+"/PCCMeter/LOAD_POWER_ACTUAL"], [pcc])
		else:
			aux=system.tag.readBlocking([path_base+"/AuxMeter/LOAD_POWER_ACTUAL"])[0].value
			pcc=meter-aux
			system.tag.writeBlocking([path_base+"/PCCMeter/GEN_POWER_ACTUAL"], [pcc])


def do_pv_sim():
	sims=system.tag.readBlocking(["[default]AutoGrid/PVSims"])[0]
	for sim in system.dataset.toPyDataSet(sims.value):
		path_base=sim[0]
		sunup=sim[2]
		sundown=sim[3]
		size=sim[4]
		
		duration=float(sundown)-float(sunup)
		now=system.date.getHour24(system.date.now())-sunup
		now=now+(float(system.date.getMinute(system.date.now()))/60.0)
		
		meter = 0
		ratio=now/duration
		
		if now > 0 and now < sundown-sunup:
			meter = math.sin(ratio*3.141592)*size
			meter = add_noise(meter)
			real_meter = meter
			# add random cuts like clouds
			if random.randint(0,7) == 2:
				meter=meter-(meter*.8)
		else:
			meter = 0
		
		system.tag.writeBlocking([path_base+"/GEN_POWER_ACTUAL", path_base+"/REACTIVE_POWER_ACTUAL"], [meter, real_meter])


def reset_batt_soc():
	'''
	Reset all of the battery simulator states of charge
	'''
	sims=system.tag.readBlocking(["[default]AutoGrid/BattSims"])[0]
	for sim in system.dataset.toPyDataSet(sims.value):
		path_base=sim[0]
		energy=sim[1]
		power=sim[2]
		
		system.tag.writeBlocking([path_base+"/SOE_ABS_ACTUAL"], [energy/2.0])