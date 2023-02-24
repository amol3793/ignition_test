def do_gw_value(newValue, event, source, dest):
	'''
	Simple transfer of tag if quality is good from source base path to dest 
	meant for use with gateway tag change handlers
	'''
	fullDestination=event.tagPath.toString().replace(source, dest)
	if newValue.quality.isGood():
		system.tag.writeBlocking([fullDestination], [newValue.getValue()])


def to_kafka(source_tag_path, current_value):
	'''
	Given a tag change with the path [default]tenant_uid/foo/bar/baz/tagname, 
	write the currentValue to [AutoGrid Kafka]tenant_uid/foo/bar/baz/tagname
	'''	
	if current_value.quality.isGood():
		path_arr=source_tag_path.split("/")
		tag=path_arr.pop()
		path="/".join(path_arr)
		path_arr[-1]
		system.tag.writeBlocking([autogrid.sync.get_kafka_path(path, tag)], [current_value])


def from_kafka(source_tag_path, current_value):
			'''
			Given a tag change with the path [AutoGrid Kafka]tenant_uid/foo/bar/baz/tagname, 
			write the currentValue to [default]tenant_uid/foo/bar/baz/tagname
			'''	
			if current_value.quality.isGood():
				system.tag.writeBlocking([source_tag_path.replace("[AutoGrid Kafka]", "[default]")], [current_value])


def do_command_with_fb(newValue, event, source, dest):
	'''
	Meant for use from a onChange handler, copy the new value to the given destination where we need to change the name
	of the outgoing kafka tag, specifically appending with _FB if the tag is not "SET_POINT_ABS"; if it's
	SET_POINT_ABS then we swap SET_POINT_ABS to SET_POINT_CONF_ABS
	
	This only completes if the quality isGood()
	
	eg: autogrid.kafka_xfer.do_command_with_fb(newValue, event, "[default]shell/STCH", "[AutoGrid Kafka]shell") 
	'''
	if newValue.quality.isGood():
		fullDestination=event.tagPath.toString().replace(source, dest)
		# conditionally add the _FB suffix for anything that is not SET_POINT_ABS
		if "SET_POINT_ABS" not in fullDestination:
			fullDestination=fullDestination+"_FB"
		else:
			fullDestination=fullDestination.replace('SET_POINT_ABS', 'SET_POINT_CONF_ABS')
		system.tag.writeBlocking([fullDestination], [newValue.getValue()])