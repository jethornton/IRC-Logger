# IRC-Logger
A simple IRC logger that creates HTML5 web logs

This logger requires the ircbot.py libary (included)
Works only with Python 2.7

Setup is done in jtlog.py, change SERVER, CHANNELS to what you wish to log
#IRC Server Configuration
SERVER = "irc.freenode.net"
PORT = 6667
SERVER_PASS = None
CHANNELS=["#jt2", '#linuxcnc'] # example ['#channel', '#nutherchannel']
NICK = "jtlog"
NICK_PASS = ""

# The local folder to save logs to
LOG_FOLDER = 'logs'

# The URL where the logs are stored
LOG_LOCATION = 'http://somewebpage.com/logs/'
