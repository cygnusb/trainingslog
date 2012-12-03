import datetime
import re
import time
from django.utils.timezone import utc

from elementtree.ElementTree import ElementTree

class TCXTrack:
	xmlns = "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}"

	def __init__(self, tcxfile):
		
		tcxfile.trackfile.open()
		self.xmltree = ElementTree(file = tcxfile.trackfile)
		tcxfile.trackfile.close()
		
	def get_alt(self, samples=-1):
		"""Returns list of (distance, altitude) tuples with optional given max length
		@param samples: Max number of samples
		@type samples: int
		@returns (distance, altitude) tuples
		@rtype: list
		"""
		alt_data = []
		# take only first activity from file
		xmlactivity = self.xmltree.find(self.xmlns + "Activities")[0]

		for xmllap in xmlactivity.findall(self.xmlns + "Lap"):
			for xmltrack in xmllap.findall(self.xmlns + "Track"):
				for xmltp in xmltrack.findall(self.xmlns + "Trackpoint"):
					try:
						alt = float(xmltp.find(self.xmlns + "AltitudeMeters").text)
						distance = float(xmltp.find(self.xmlns + "DistanceMeters").text)
					except AttributeError:
						pass
					else:
						alt_data.append((distance, alt))
		if samples > 0:
			if len(alt_data) > samples:
				sample_size = len(alt_data) / samples
				s = list(zip(*[iter(alt_data)]*sample_size))
				return map(avg, s)
		return alt_data
	
	def get_cad(self, samples=-1):
		"""Returns list of (distance, cadence) tuples with optional given max length
		@param samples: Max number of samples
		@type samples: int
		@returns (distance, cadence) tuples
		@rtype: list
		"""
		cad_data = []
		# take only first activity from file
		xmlactivity = self.xmltree.find(self.xmlns + "Activities")[0]

		for xmllap in xmlactivity.findall(self.xmlns + "Lap"):
			for xmltrack in xmllap.findall(self.xmlns + "Track"):
				for xmltp in xmltrack.findall(self.xmlns + "Trackpoint"):
					try:
						cad = float(xmltp.find(self.xmlns + "Cadence").text)
						distance = float(xmltp.find(self.xmlns + "DistanceMeters").text)
					except AttributeError:
						pass
					else:
						cad_data.append((distance, cad))
		if samples > 0:
			if len(cad_data) > samples:
				sample_size = len(cad_data) / samples
				s = list(zip(*[iter(cad_data)]*sample_size))
				return map(avg, s)
		return cad_data
		
	
	def get_hf(self, samples=-1):
		"""Returns list of (distance, heartrate) tuples with optional given max length
		@param samples: Max number of samples
		@type samples: int
		@returns (distance, heartrate) tuples
		@rtype: list
		"""
		hf_data = []
		# take only first activity from file
		xmlactivity = self.xmltree.find(self.xmlns + "Activities")[0]

		for xmllap in xmlactivity.findall(self.xmlns + "Lap"):
			for xmltrack in xmllap.findall(self.xmlns + "Track"):
				for xmltp in xmltrack.findall(self.xmlns + "Trackpoint"):
					try:
						hf = int(xmltp.find(self.xmlns + "HeartRateBpm")[0].text)
						distance = float(xmltp.find(self.xmlns + "DistanceMeters").text)
					except (TypeError, AttributeError):
						pass
					else:
						hf_data.append((distance, hf))
		if samples > 0:
			if len(hf_data) > samples:
				sample_size = len(hf_data) / samples
				s = list(zip(*[iter(hf_data)]*sample_size))
				return map(avg, s)
		return hf_data
	
	def get_speed(self, samples=-1, pace=False):
		"""Returns list of (distance, heartrate) tuples with optional given max length
		@param samples: Max number of samples
		@type samples: int
		@returns (distance, heartrate) tuples
		@rtype: list
		"""
		speed_data = []
		last_time = None
		last_distance = None
		
		print "Speed as pace: %s" % pace
		seconds_sum = 0		

		# take only first activity from file
		xmlactivity = self.xmltree.find(self.xmlns + "Activities")[0]

		for xmllap in xmlactivity.findall(self.xmlns + "Lap"):
			for xmltrack in xmllap.findall(self.xmlns + "Track"):
				for xmltp in xmltrack.findall(self.xmlns + "Trackpoint"):
					try:
						time = parse_xsd_timestamp(xmltp.find(self.xmlns + "Time").text)
						distance = float(xmltp.find(self.xmlns + "DistanceMeters").text)
					except (TypeError, AttributeError):
						pass
					else:
						if time and last_time and distance != None and last_distance != None:
							td = (time - last_time)
							td_seconds = (td.seconds + td.days * 24 * 3600)
							seconds_sum = seconds_sum + td_seconds
							dist = (distance - last_distance)
							if td_seconds > 0 and dist > 0:
								if pace:
									speed = 1000.0/60.0 * td_seconds / dist
								else:
									speed = dist * 3.6 / td_seconds
								# discard spikes
								if pace and speed > 20:
									continue
									
								speed_data.append((distance, speed))
								last_distance = distance
								last_time = time
						if not last_time and not last_distance:
							last_time = time
							last_distance = distance

		if samples > 0:
			if len(speed_data) > samples:
				sample_size = len(speed_data) / samples
				s = list(zip(*[iter(speed_data)]*sample_size))
				return map(avg, s)
		return speed_data

def activities_summary(activities):
	"""returns summary dictionary for list of activities
	@param activities: list of Activities
	@type avtivities: array
	@return: Summary dictionary
	@rtype: dict
	"""
	summary=dict(num_activities = len(activities),
				total_distance = 0.0,
				total_time = 0,
				total_elev_gain = 0,
				total_calories = 0)
	
	for activity in activities:
		if activity.time:
			summary['total_time'] += activity.time
		if activity.distance:
			summary['total_distance'] += float(activity.distance)
		if activity.elevation_gain:
			summary['total_elev_gain'] += activity.elevation_gain
		if activity.calories:
			summary['total_calories'] += activity.calories
	
	summary['total_time_str'] = str(datetime.timedelta(days=0, seconds=summary['total_time']))
	return summary

def avg(sample):
	return (min(x for x, y in sample),sum(y for x,y in sample)/len(sample))

def int_or_none(val):
	try:
		return int(val)
	except ValueError:
		return None

def float_or_none(val):
	try:
		return float(val)
	except ValueError:
		return None

def str_float_or_none(val):
	ret = float_or_none(val)
	if ret:
		return str(ret)
	else:
		return None

def time_to_seconds(t_string):
	"""Converts time string to seconds
	"""
	fields = t_string.split(':')
	if len(fields)==3:
		seconds = int(fields[0])*3600 + int(fields[1])*60 + int(fields[2])
	elif len(fields)==2:
		seconds = int(fields[0])*60 + int(fields[1])
	else:
		seconds = 0
	return seconds

def seconds_to_time(seconds, force_hour=False):
	"""Converts seconds to time string
	@param seconds: Number of seconds
	@type seconds: string
	@param force_hour: Force hour even if seconds < 3600
	@type force_hour: boolean
	@return time_string
	"""
	hours = int(seconds/3600)
	minutes = int((seconds % 3600) / 60)
	seconds = (seconds % 60)
	
	if hours > 0 or force_hour:
		t_string = "%d:%02d:%02d" % (hours, minutes, seconds)
	else:
		t_string = "%d:%02d" % (minutes, seconds)
	return t_string

def pace_to_speed(val):
	"""Converts pace min/km (mm:ss) to speed (km/h)
	"""
	seconds = time_to_seconds(val)
	speed = 3600.0 / seconds
	return speed

def speed_to_pace(speed):
	"""Converts speed (km/h) float to pace [min/km] (mm:ss)
	"""
	seconds = 3600 / speed
	return seconds_to_time(seconds)

def parse_xsd_timestamp(s):
	"""Returns datetime in minutes or None."""
	m = re.match(""" ^(?P<year>-?[0-9]{4}) - (?P<month>[0-9]{2}) - (?P<day>[0-9]{2})T (?P<hour>[0-9]{2}) : (?P<minute>[0-9]{2}) : (?P<second>[0-9]{2})(?P<microsecond>\.[0-9]{1,6})?((?P<tz>Z) | (?P<tz_hr>[-+][0-9]{2}) : (?P<tz_min>[0-9]{2}))?$ """, s, re.X)
	if m is not None:
		values = m.groupdict()
			
		if values["microsecond"] is None:
			values["microsecond"] = 0
		else:
			values["microsecond"] = values["microsecond"][1:]
			values["microsecond"] += "0" * (6 - len(values["microsecond"]))
		values = dict((k, int(v)) for k, v in values.iteritems() if not k.startswith("tz"))
		try:
			timestamp = datetime.datetime(**values)
			timestamp = timestamp - datetime.timedelta(seconds=time.altzone)
##			if values["tz"] == "Z":

			return timestamp
		except ValueError:
			pass
	return None