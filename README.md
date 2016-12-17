# IRC-Logger
A simple IRC logger that creates HTML5 web logs

This logger requires the ircbot.py libary (included)

Works only with Python 2.7

Configuration is done in jt-logger.py
```
SERVER = "irc.freenode.net"
PORT = 6667
SERVER_PASS = None
CHANNELS=["#jt2", '#linuxcnc'] # example ['#channel', '#nutherchannel']
NICK = "jtlog"
NICK_PASS = ""
LOG_FOLDER = 'logs'
LOG_LOCATION = 'http://somewebpage.com/logs/'
```
At this point the logger only logs messages and when someone says /me some text

To Do:
```
log kick
log mode
log nick
log pubnotic
log topic
```
