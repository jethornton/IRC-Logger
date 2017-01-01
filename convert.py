#!/usr/bin/env python
# coding: utf-8

import os
import datetime
import re

# IMPORTANT only run this once!
# put this in with the logbot files and change the channel

# full path to the folder where the logs are
LOG_FOLDER = '/home/john/logs/#linuxcnc'
CHANNEL = '#linuxcnc'

# stop robots from indexing
BOTS = '<meta name="robots" content="noarchive,nofollow,noimageindex,noindex,noodp,nosnippet"/>'

LOG_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	{}
	<title>{} Logs</title>
	<link rel="stylesheet" href="../log.css">
</head>
<body>
	<h1>{} Logs</h1>
	<h2>{}</h2>
	<p><a href="index.html">{} Calendar</a></p>
"""

LOG_FOOTER = ['	<footer>\n', '		<p>Logs by: JT</p>\n', '</footer>\n',
 '	</body>\n', '</html>']

index_path = os.path.join(LOG_FOLDER, 'index.html')
if os.path.isfile(index_path):
	print 'deleting index'
	os.remove(index_path)

anchor_re = re.compile('<a .*>*</a>')
time_anchor_re = re.compile('<a href="#.*]</a>')
time_re = re.compile('\[.*]')
name_re = re.compile(r'style="color:.>*.*</span>')

for log_file in sorted(os.listdir(LOG_FOLDER)):
	d = datetime.datetime.strptime(log_file[:10], '%Y-%m-%d')
	date = datetime.date.strftime(d, "%b %d %Y")
	new_data = []
	with open(os.path.join(LOG_FOLDER,log_file), 'r') as log:
		data = log.readlines()[32:-4]
		for index, line in enumerate(data):
			if line.startswith('<a href='):
				x = re.search(time_re, line) # get the time
				line = re.sub(time_anchor_re, x.group(0)[1:6], line, 1)
				if re.search(name_re, line):
					y = re.search(name_re, line)
					name = y.group(0)[32:-11]
					if name.endswith('\\'):
						name = name + '\\'
				line = re.sub(name_re, '>' + name + '</span>', line)
			new_data.append(line)
	with open(os.path.join(LOG_FOLDER, log_file), 'w') as log:
		log.write(LOG_HEADER.format(BOTS, CHANNEL, CHANNEL, date, CHANNEL))
		log.writelines(new_data)
		log.writelines(LOG_FOOTER)

