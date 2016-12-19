# IRC-Logger
A simple IRC logger that creates HTML5 web logs

This logger requires the ircbot.py libary (included)

Works only with Python 2.7

Configuration is done in jt-logger.py
```
# Configuration

DEBUG = False

# IRC Server
SERVER = "irc.freenode.net"
PORT = 6667
SERVER_PASS = None
CHANNELS=['#channel', '#nutherchannel']
NICK = 'jtlog'
NICK_PASS = ""

# The full path of the local directory logger index
# The subdirectories will be created for each channel if not there
LOG_FOLDER = '/home/server/programs/logger/logs'

# The URL where the main log index is
LOG_LOCATION = 'http://someurl.com/logs'

# stop robots from indexing, this line is added to the <head> section of each page
BOTS = '<meta name=”ROBOTS” content=”NOINDEX, NOFOLLOW, NOARCHIVE, NOODP, NOYDIR”>'

# turn on and off loggable events
LOG_KICK = False
LOG_JOIN = False
LOG_MODE = True
LOG_NICK = True
LOG_PUBNOTICE = False
LOG_TOPIC = True
LOG_QUIT = False

# End Configuration

``
