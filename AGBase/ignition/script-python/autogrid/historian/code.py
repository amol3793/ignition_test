import system.net


def log_influx(tenant, database, meas_name, meas_id, qv):
	'''
	Simplistic method to write the given arguments as lines in influxdb (in influx a "line" is a TS record)
	
	call with a change handler that looks like this:
	if not initialChange:
		root=str(event.getTagPath()).replace('[default]', '').split('/')[0]
		autogrid.historian.log_influx('tenant', 'historian', event.getTagPath().getItemName(), root, newValue)
	'''
	
	values=system.tag.readBlocking([
		"[default]AutoGrid/InfluxDB/user",
		"[default]AutoGrid/InfluxDB/password",
		"[default]AutoGrid/InfluxDB/host_port"
		])
	
	influx_user=values[0].value
	influx_passwd=values[1].value
	influx_host=values[2].value

	url="http://"+influx_host+"/write?db="+database
	
	nanos=qv.timestamp.getTime()*1000000
	
	line=meas_name+",identifier="+meas_id+",quality="+str(qv.quality)+",tenant="+tenant+" value="+str(qv.value)+" "+str(nanos)
	system.net.httpPost(url, "application/x-www-form-urlencoded", line, 100, 1000, influx_user, influx_passwd)