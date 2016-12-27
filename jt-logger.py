#!/usr/bin/env python
# coding: utf-8

"""
JT Logger

A minimal IRC log bot

Written by John Thornton

Includes python-irclib from http://python-irclib.sourceforge.net/

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA   02111-1307, USA.

All configuration is done in this file
"""

__author__ = "John Thornton <bjt128@gmail.com>"
__version__ = "1.4"
__date__ = "12/19/2016"
__copyright__ = "Copyright (c) John Thornton"
__license__ = "GPL3"


from ircbot import SingleServerIRCBot
import time
import socket
import os
import calendar
import urllib
import re

# Configuration

DEBUG = False

# IRC Server
SERVER = "irc.freenode.net"
PORT = 6667
SERVER_PASS = None
CHANNELS=['#jt2']#, '#linuxcnc'] # example ['#channel', '#nutherchannel']
NICK = 'jtlog'
NICK_PASS = ""

# The full path of the local directory logger index
# The subdirectories will be created for each channel if not there
LOG_FOLDER = '/home/john/logs'

# The URL where the main log index is
LOG_URL = 'http://gnipsel.com/logs'

# stop robots from indexing
BOTS = '<meta name=”ROBOTS” content=”NOINDEX, NOFOLLOW, NOARCHIVE, NOODP, NOYDIR”>'

# turn on and off loggable events
LOG_KICK = False
LOG_JOIN = False
LOG_MODE = True
LOG_NICK = True
LOG_PART = False
LOG_PUBNOTICE = False
LOG_TOPIC = True
LOG_QUIT = False

# End Configuration

HTML = {
	"log" : "{}: Today's Log {}",
	"no_log" : '{}: Nothing has been logged today, {} index {}',
	"index" : '{}: The {} index {}',
	"action" : '{} * <span class="person">{}</span> {}',
	"kick" : '{} -!- <span class="kick">{}</span> was kicked from {} by {} [{}]',
	"mode" : '{} -!- {} mode set to <span class="mode">{}</span> by <span class="person">{}</span>',
	"nick" : '{} <span class="person">{}</span> is now known as <span class="person">{}</span>',
	"pubmsg" : '{} <span class="person">{}:</span> {}',
	"pubnotice" : '{} <span class="notice">-{}:{}-</span>{}',
	"topic" : '{} <span class="person">{}</span> changed topic of <span class="channel">{}</span> to: {}',
}

CHANNEL_HEADER = """<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="utf-8">
		{}
		<title>Chat Logs</title>
		<link rel="stylesheet" href="channel.css">
	</head>
	<body>
	<h1>Chat Logs</h1>
"""

CHANNEL_FOOTER = """	<footer>
		<p>Logs by: JT</p>
	</footer>
	</body>
</html>
"""

INDEX_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	{}
	<title>JT Logs</title>
	<link rel="stylesheet" href="../calendar.css">
</head>
<body>
	<p><a href="../index.html">Return to Channel Index</a></p>
	<h1>{} Logs</h1>
	<div class="calendar">
"""

INDEX_FOOTER = """</div><!-- End of calendar Class -->
	<footer>
		<p>Logs by: JT</p>
</footer> 
	</body>
</html>
"""

TABLE_HEADER = """	<table>
		<tr>
			<th colspan="3"><span class="year">{} Logs</span></th>
		</tr>
"""

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

def setkeepalive(sock):
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 300)
	sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 30)
	sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3)

http_re = re.compile('( http[s]?://[^\s]+)', re.IGNORECASE)
www_re = re.compile('( www.[^\s]+)', re.IGNORECASE) # findall search string
www_add = re.compile('(www.[^\s]+)', re.IGNORECASE) # sub search string

class Logbot(SingleServerIRCBot):
	def __init__(self, server, port, server_pass=None, channels=[],
				 nick="timber", nick_pass=None, format_html=HTML):
		SingleServerIRCBot.__init__(self, [(server, port, server_pass)], nick, nick)
		self.chans = [x.lower() for x in channels]
		self.format_html = format_html
		self.count = 0
		self.nick_pass = nick_pass
		# create the log directory if not found
		if not os.path.exists(LOG_FOLDER):
			os.makedirs(LOG_FOLDER)
			for filename in os.listdir('.'):
				if '.css' in filename:
					fp = os.path.join(os.getcwd(), filename)
					os.system('cp {} {}'.format(fp, LOG_FOLDER))

		# create the channel index when started
		with open(os.path.join(LOG_FOLDER, 'index.html'), 'w') as index:
			index.write(CHANNEL_HEADER.format(BOTS))
			for channel in CHANNELS:
				link = channel.replace('#', '%23')
				index.write('<p><a href="{}/index.html">{}</a></p>\n'.format(link, channel))
			index.write(CHANNEL_FOOTER)
		# create channel directories if not found
		for channel in CHANNELS:
			channel_directory = os.path.join(LOG_FOLDER, channel)
			if not os.path.isdir(channel_directory):
				os.makedirs(channel_directory)
			else: # check for index in channel directory
				if not os.path.isfile(os.path.join(channel_directory, 'index.html')):
					self.create_index(channel)

		print 'JT Logbot {}'.format(__version__)
		print "Connecting to {}:{}...".format(server, port)
		print "Press Ctrl-C to quit"

	def quit(self):
		self.connection.disconnect("Quitting...")

	def on_all_raw_messages(self, c, e):
		"""Display all IRC connections in terminal"""
		if DEBUG: print e.arguments()[0]

	def on_welcome(self, c, e):
		"""Join channels after successful connection"""
		print 'Connected', e.source()
		if self.nick_pass:
			c.privmsg("nickserv", "identify %s" % self.nick_pass)
		setkeepalive(c.socket)
		for chan in self.chans:
			c.join(chan)

	### Loggable events

	def on_action(self, c, event): # Someone says /me xxx
		self.format_event('action', event)

	def on_join(self, c, event): # someone joins the channel
		if LOG_JOIN:self.format_event("join", event)

	def on_kick(self, c, event):
		if LOG_KICK:self.format_event('kick', event)

	def on_mode(self, c, event):
		if LOG_MODE:self.format_event('mode', event)

	def on_nick(self, c, event):
		if LOG_NICK:
			nick = self.user(event)
			# Only write the event on channels that actually had the user in the channel
			for chan in self.channels:
				if nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
					self.format_event('nick', event, {'channel':chan,
					'old_nick':self.user(event), 'new_nick':event.target()})

	def on_part(self, c, event):
		if LOG_PART:self.format_event("part", event)

	def on_pubmsg(self, c, event): # public messages
		if event.arguments()[0].startswith(NICK):
			self.log(c, event)
		elif event.arguments()[0] == 'log':
			self.log(c, event)
		elif event.arguments()[0] == 'index':
			self.index(c, event)
		else: # only log messages
			self.format_event('pubmsg', event)

	def on_pubnotice(self, c, event):
		if LOG_PUBNOTICE:self.format_event('pubnotice', event)

	def on_privmsg(self, c, event):
		print self.user(event), event.arguments()
		c.privmsg(self.user(event), self.format_html["log"])

	def on_quit(self, c, event):
		if LOG_QUIT:
			nick = self.user(event)
			# Only write the event on channels that actually had the user in the channel
			for chan in self.channels:
				if nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
					self.format_event("quit", event, {"%chan%" : chan})

	def on_topic(self, c, event): # someone changes the topic with /topic
		if LOG_TOPIC:self.format_event("topic", event)

	def log(self, c, event):
		date = time.strftime("%Y-%m-%d")
		channel = urllib.quote(event.target(), safe='')
		log_url = os.path.join(LOG_URL, channel, date) + '.html'
		log_path = os.path.join(LOG_FOLDER, event.target(), date,) + '.html'
		if not os.path.isfile(log_path):
			log_index = os.path.join(LOG_URL, channel, 'index.html')
			log = self.format_html['no_log'].format(self.user(event), event.target(), log_index)
			c.privmsg(event.target(), log)
		else:
			log = self.format_html['log'].format(self.user(event), log_url)
			c.privmsg(event.target(), log)

	def index(self, c, event):
		channel = urllib.quote(event.target(), safe='')
		index_url = os.path.join(LOG_URL, channel, 'index.html')
		msg = self.format_html['index'].format(self.user(event), event.target(), index_url)
		c.privmsg(event.target(), msg)

	def user(self, event):
		# event.source() is the user and IP address
		return event.source().split("!")[0]

	def format_event(self, action, event, params={}):
		# event.target() is the channel sometimes... XXXXXXXXXXXXXXXXXXXXXXXXX
		# event.arguments()[0] is the message
		# event.eventtype() is the event type like pubmsg, nick etc.
		date = time.strftime("%Y-%m-%d")
		hm = time.strftime('%I:%M')
		msg = self.format_html[action]
		channel = event.target()
		if action == 'action': # someone says /me
			msg = msg.format(hm, self.user(event), event.arguments()[0])
		elif action == 'pubmsg': # public message
			msg = msg.format(hm, self.user(event), event.arguments()[0])
			if re.findall(http_re, msg): # check for http:// and https://
				msg = re.sub(http_re, r'<a href="\1/" target="_blank">\1</a>', msg)
			if re.findall(www_re, msg): # check for www.
				msg = re.sub(www_add, r'<a href="http://\1/" target="_blank">\1</a>', msg)
		elif action == 'kick': # someone got kicked off the channel
			msg = msg.format(hm, self.user(event), event.target(), event.source(), event.arguments()[1])
		elif action == 'mode': # the mode was changed with /mode?
			#person = event.arguments()[1] if len(event.arguments()) > 1 else event.target()
			msg = msg.format(hm, event.target(), event.arguments()[0], self.user(event))
		elif action == 'nick': # user nick changed
			msg = msg.format(hm, self.user(event), event.target())
			channel = params['channel']
		elif action == 'pubnotice': # /notice posted
			msg = msg.format(hm, self.user(event), event.target(), event.arguments()[0])
		elif action == 'topic': # /topic changed
			msg = msg.format(hm, self.user(event), event.target(), event.arguments()[0])
		self.append_log_msg(date, channel, msg)

	def append_log_msg(self, date, channel, msg):
		print date, channel, msg
		log_path = os.path.join(LOG_FOLDER, channel, date) + '.html'
		if not os.path.isfile(log_path):
			self.create_log(log_path, channel)
		with open(log_path, 'r') as log:
			data = log.readlines()[:-len(LOG_FOOTER)]
			data.extend([msg, '\n<br/>\n'])
			data.extend(LOG_FOOTER)
		with open(log_path, 'w') as log:
			log.writelines(data)

	def create_log(self, path, channel): # create and empty log file
		date = time.strftime("%b %d %Y")
		with open(path, 'w') as log:
			log.write(LOG_HEADER.format(BOTS, channel, channel, date, channel))
			log.writelines(LOG_FOOTER)
		self.create_index(channel)

	def create_index(self, channel):
		# delete the index if found
		index_path = os.path.join(LOG_FOLDER, channel, 'index.html')
		if os.path.isfile(index_path):
			print 'deleting index'
			os.remove(index_path)
		# get a list of years/months in the channel
		loglist = []
		ym = set()
		y = set()
		for log in sorted(os.listdir(os.path.join(LOG_FOLDER, channel)),reverse=True):
			loglist.append(log)
			ym.add(log[:7])
			y.add(log[:4])
		if len(y) > 0: # create the index
			index = INDEX_HEADER.format(BOTS, channel)
			# list of year-month for channel
			monthlist = sorted(list(ym),reverse=True)
			yearlist = sorted(list(y),reverse=True)
			for year in yearlist:
				index += TABLE_HEADER.format(year)
				months = []
				for item in monthlist:
					if year == item[:4]:
						months.append(item)
				# create year header
				#figure out which rows to make
				row1 = ['03', '02', '01']
				row4 = ['12', '11', '10']
				row3 = ['09', '08', '07']
				row2 = ['06', '05', '04']

				if any(a[-2:] == b for a in months for b in row1):
					index += '		<tr>\n'
					for i in range(1,4):
						index += self.create_month(int(year), i, loglist)
					index +=  '		</tr>\n'

				if any(a[-2:] == b for a in months for b in row2):
					index += '		<tr>\n'
					for i in range(4,7):
						index += self.create_month(int(year), i, loglist)
					index +=  '		</tr>\n'

				if any(a[-2:] == b for a in months for b in row3):
					index += '		<tr>\n'
					for i in range(7,10):
						index += self.create_month(int(year), i, loglist)
					index +=  '		</tr>\n'

				if any(a[-2:] == b for a in months for b in row4):
					# create a row of 3 months
					index += '		<tr>\n'
					for i in range(10,13):
						index += self.create_month(int(year), i, loglist)
					index +=  '		</tr>\n'

				index += '	</table><br>'
			index += INDEX_FOOTER
			with open(index_path,'w') as f:
				f.write(index)

	def create_month(self, year, month, loglist):
		c = calendar.TextCalendar()
		datelist = []
		for date in c.itermonthdates(year, month):
			datelist.append(date)
		table = '			<td>\n				<table>\n'
		table += '					<tr>\n'
		table += '					<th colspan="7"><span class="month">{}</span></th>\n'.format(calendar.month_name[month])
		table += '					</tr>\n'
		table += '					<tr class="dayheader"><!-- Day Header -->\n'
		for day in calendar.day_abbr[0:7]:
			table += '						<th>{}</th>\n'.format(day)
		table += '					</tr>\n'
		for index, day in enumerate(c.itermonthdays2(year,month)):
			if index == 0:
				table += '					<tbody class="days">\n'
			if day[1] == 0:
				table += '					<tr><!-- Week Row -->\n'
			if day[0] == 0:
				table += '						<td>&nbsp;</td>\n'
			else:
				if any('{:%Y-%m-%d}'.format(datelist[index]) in i for i in loglist):
					table += '						<td><a href="{:%Y-%m-%d}.html">{}</a></td>\n'.format(datelist[index],str(day[0]))
				else:
					table += '						<td>{}</td>\n'.format(str(day[0]))
			if day[1] == 6:
				table += '					</tr>\n'
		table += '					</tbody>\n				</table>\n'
		table += '			</td>\n'
		return table


def main():
	# Start the bot
	bot = Logbot(SERVER, PORT, SERVER_PASS, CHANNELS, NICK, NICK_PASS)
	try:
		# Connect to FTP
		#if FTP_SERVER:
		#	bot.set_ftp(connect_ftp())

		bot.start()
	except KeyboardInterrupt:
		#if FTP_SERVER: bot.ftp.quit()
		bot.quit()


if __name__ == "__main__":
	main()
