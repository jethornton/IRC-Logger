#!/usr/bin/env python
# coding: utf-8

"""
jt-logger

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
__version__ = "1.0.0"
__date__ = "12/17/2016"
__copyright__ = "Copyright (c) John Thornton"
__license__ = "GPL3"


from ircbot import SingleServerIRCBot
import time
import socket
import os
import calendar

# Configuration

DEBUG = False

# IRC Server
SERVER = "irc.freenode.net"
PORT = 6667
SERVER_PASS = None
CHANNELS=['#jt2', '#linuxcnc'] # example ['#channel', '#nutherchannel']
NICK = 'jtlog'
NICK_PASS = ""

# The local folder to save logs to
LOG_FOLDER = 'logs'

# The URL where the logs are stored
LOG_LOCATION = 'http://gnipsel.com/logs/'

# End Configuration

HTML = {
	"help" : "{}: Today's Log {}{}/{}.html",
	"action" : '{} * <span class="person">{}</span> {}',
	"kick" : '-!- <span class="kick">%user%</span> was kicked from %channel% by %kicker% [%reason%]',
	"mode" : '-!- mode/<span class="mode">%channel%</span> [%modes% %person%] by %giver%',
	"nick" : '<span class="nick">%old%</span> is now known as <span class="nick">%new%</span>',
	"pubmsg" : '{} <span class="person">{}:</span> {}',
	"pubnotice" : '<span class="notice">-%user%:%channel%-</span> %message%',
	"topic" : '<span class="topic">%user%</span> changed topic of <span class="topic">%channel%</span> to: %message%',
}

CHANNEL_HEADER = """<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="utf-8">
		<title>Chat Logs</title>
		<link rel="stylesheet" href="../channel.css">
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
	<title>JT Logs</title>
	<link rel="stylesheet" href="../../calendar.css">
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
			<th colspan="3">{} Logs</th>
		</tr>
"""

LOG_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<title>{} Logs</title>
	<link rel="stylesheet" href="../../log.css">
</head>
<body>
	<p><a href="index.html">{} Calendar</a></p>
"""

LOG_FOOTER = ['	<footer>\n', '		<p>Logs by: JT</p>\n', '</footer>\n',
 '	</body>\n', '</html>']

def setkeepalive(sock):
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 300)
	sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 30)
	sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3)

def channel_index():
	with open(os.path.join(os.getcwd(), LOG_FOLDER, 'index.html'), 'w') as index:
		index.write(CHANNEL_HEADER)
		for channel in CHANNELS:
			link = channel.replace('#', '%23')
			index.write('<p><a href="{}/index.html">{}</a></p>\n'.format(link, channel))
		index.write(CHANNEL_FOOTER)

class Logbot(SingleServerIRCBot):
	def __init__(self, server, port, server_pass=None, channels=[],
				 nick="timber", nick_pass=None, format_html=HTML):
		SingleServerIRCBot.__init__(self, [(server, port, server_pass)], nick, nick)

		self.chans = [x.lower() for x in channels]
		self.format_html = format_html
		#self.set_ftp()
		self.count = 0
		self.nick_pass = nick_pass

		#self.load_channel_locations()
		#print "Logbot %s" % __version__
		print "Connecting to %s:%i..." % (server, port)
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

	def on_action(self, c, e): # Someone says /me xxx
		self.format_event("action", e)

	def on_join(self, c, e): # someone joins the channel
		pass
		#self.format_event("join", e)

	def on_kick(self, c, e):
		self.format_event("kick", e,
						 {"%kicker%" : e.source(),
						  "%channel%" : e.target(),
						  "%user%" : e.arguments()[0],
						  "%reason%" : e.arguments()[1],
						 })

	def on_mode(self, c, e):
		self.format_event("mode", e,
						 {"%modes%" : e.arguments()[0],
						  "%person%" : e.arguments()[1] if len(e.arguments()) > 1 else e.target(),
						  "%giver%" : nm_to_n(e.source()),
						 })

	def on_nick(self, c, e):
		self.format_event('nick',e)
		"""
		old_nick = nm_to_n(e.source())
		# Only write the event on channels that actually had the user in the channel
		for chan in self.channels:
			if old_nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
				self.format_event("nick", e,
							 {"%old%" : old_nick,
							  "%new%" : e.target(),
							  "%chan%": chan,
							 })"""

	def on_part(self, c, e):
		pass
		#self.format_event("part", e)

	def on_pubmsg(self, c, e): # public messages
		if e.arguments()[0].startswith(NICK):
			self.log(c, e)
		elif e.arguments()[0].startswith('log'):
			self.log(c, e)
		else: # only log messages
			self.format_event("pubmsg", e)

	def on_pubnotice(self, c, e):
		self.format_event("pubnotice", e)

	def on_privmsg(self, c, e):
		print nm_to_n(e.source()), e.arguments()
		c.privmsg(nm_to_n(e.source()), self.format_html["help"])

	def on_quit(self, c, e):
		pass
		"""
		nick = nm_to_n(e.source())
		# Only write the event on channels that actually had the user in the channel
		for chan in self.channels:
			if nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
				self.format_event("quit", e, {"%chan%" : chan})
		"""

	def on_topic(self, c, e): # someone changes the topic with /topic
		self.format_event("topic", e)

	def log(self, c, event):
		date = time.strftime("%Y-%m-%d")
		log = self.format_html['help'].format(LOG_LOCATION,self.user(event), event.target(), date)
		c.privmsg(event.target(), log)

	def user(self, event):
		# event.source() is the user and IP address
		return event.source().split("!")[0]

	"""
	format_event replaces place holders with stuff
	help user, channel, date
	action time, user, message
	"""

	def format_event(self, action, event, params={}):
		# event.target() is the channel
		# event.arguments()[0] is the message
		# event.eventtype() is the event type like pubmsg, nick etc.
		date = time.strftime("%Y-%m-%d")
		hm = time.strftime('%I:%M')
		msg = self.format_html[action]
		if action == 'action': # someone says /me
			msg = msg.format(hm, self.user(event), event.arguments()[0])
		elif action == 'pubmsg': # public message
			msg = msg.format(hm, self.user(event), event.arguments()[0])
		self.append_log_msg(date, event.target(), msg)

	def append_log_msg(self, date, channel, msg):
		print channel, date, msg
		log_path = os.path.join(os.getcwd(), LOG_FOLDER, channel, date) + '.html'
		if not os.path.isfile(log_path): # just do this here maybe
			self.create_log(log_path, channel)
		#data = []
		with open(log_path, 'r') as log:
			data = log.readlines()[:-len(LOG_FOOTER)]
			data.extend([msg, '\n<br/>\n'])
			data.extend(LOG_FOOTER)
		with open(log_path, 'w') as log:
			log.writelines(data)
		#write_lines(filename, data)

	def create_log(self, path, channel): # create and empty log file
		with open(path, 'w') as log:
			log.write(LOG_HEADER.format(channel, channel))
			log.writelines(LOG_FOOTER)
		self.create_index(channel)

	def create_index(self, channel):
		# delete the index if found
		log_dir = os.getcwd()+'/logs'
		index_path = os.path.join(log_dir, channel, 'index.html')
		if os.path.isfile(index_path):
			print 'deleting index'
			os.remove(index_path)
		# get a list of years/months in the channel
		loglist = []
		ym = set()
		y = set()
		for log in sorted(os.listdir(os.path.join(log_dir, channel)),reverse=True):
			loglist.append(log)
			ym.add(log[:7])
			y.add(log[:4])
		if len(y) > 0: # create the index
			index = INDEX_HEADER.format(channel)
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
		table = '			<td class="month">\n				<table>\n'
		table += '					<tr>\n'
		table += '					<th colspan="7">{}</th>\n'.format(calendar.month_name[month])
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
	# create the log directory if not found
	if not os.path.exists(LOG_FOLDER):
		os.makedirs(LOG_FOLDER)
	# create the channel index when started
	channel_index()
	# create channel directories if not found
	for channel in CHANNELS:
		channel_directory = os.path.join(os.getcwd(), LOG_FOLDER, channel)
		if not os.path.isdir(channel_directory):
			os.makedirs(channel_directory)

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
