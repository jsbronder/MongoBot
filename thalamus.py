import socket
import ssl
import sys
import re
import traceback

from autonomic import Synapse
from config import load_config
from time import sleep
from id import Id

from pprint import pprint

'''
Welcome to the thalamus - the switchboard of the brain.  It connects the cortex and brainmeats
to the rest of the body, or in this case IRC. It is responsible for relaying input and out to
the IRC server in a sane (well... yeah... whatever) manner; and triggering the necessary
brainmeats in the cortex when commands are recognized.
'''
class Thalamus(object):

    cx = False

    buffer = ''
    connection = False
    settings = False
    secrets = False

    name = False
    server = False

    channels = {}
    regain_nick = False


    '''
    Initialize and auto-connect
    '''
    def __init__(self, cortex):

        self.cx = cortex

        self.settings = load_config('config/settings.yaml')
        self.secrets = load_config('config/secrets.yaml')

        self.connect()


    '''
    Make those connections, you will feel so much more human.
    '''
    def connect(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.settings.irc.host, self.settings.irc.port))

        if hasattr(self.settings.irc, 'ssl') and self.settings.irc.ssl:
            self.sock = ssl.wrap_socket(sock)
        else:
            self.sock = sock

        self.sock.setblocking(0)

        self.introduce()


    '''
    Introduce yourself to the IRC server; it's only polite.
    '''
    def introduce(self):

        if not self.name:
            self.name = self.settings.bot.nick

        self.send('USER %s %s %s : %s' % (
            self.settings.bot.ident,
            self.settings.bot.ident,
            self.settings.bot.ident,
            self.settings.bot.realname
        ))
        self.send('NICK %s' % self.name)


    '''
    Read data in from the socket
    '''
    def read(self):

        try:
            data = self.sock.recv(256)
        except:
            return

        if data == b'':
            # TODO: Set up auto-reconnect here
            print 'Connection lost.'
            sys.exit()

        return data


    '''
    Send data out to the bound socket
    '''
    def send(self, data):

        # Temporary backwards compatibility as everything gets ported to the thalamus send
        data = data.rstrip('\r\n')

        self.sock.send('%s%s%s' % (data, chr(015), chr(012)))


    '''
    Process incoming data
    '''
    def process(self):

        data = self.read()

        if not data:
            return

        self.buffer += data
        lines = self.buffer.split(chr(012))
        self.buffer = lines.pop()

        for line in lines:
            if line[-1] == chr(015):
                line = line[:-1]

            if not line:
                continue

            source = ''
            target = '*'

            if line[0] == ':':
                source, line = line[1:].split(' ', 1)

            if line.find(' :') != -1:
                line, trailing = line.split(' :', 1)
                args = line.split()
                args.append(trailing)
            else:
                args = line.split()

            command = args.pop(0)

            method = getattr(self, '_cmd_%s' % command, None)

            try:
                if method is not None:
                    method(source, args)
            except Exception as e:
                print "DA FUQ?"
                print "%s" % e
                print traceback.format_exc()
                continue


    '''
    Handle the welcome to the server message by joining channels at this point
    '''
    def _cmd_001(self, source, args):

        for channel in self.secrets.channels:

            self.send('JOIN %s' % channel)


    '''
    Handle incoming server information
    '''
    def _cmd_004(self, source, args):

        self.name = args.pop(0)
        self.server = args.pop(0)

        self.regain_nick = True


    '''
    Handle joining a room
    '''
    def _cmd_353(self, source, args):

        users = args[-1]
        channel = args[-2]

        self.channels[channel] = {
            'users': {
                re.sub('^[@+]', '', u): re.sub('^([@+])?.*', lambda m: m.group(1) or '', u)
                for u in users.split()
            },
            'modes': self.secrets.channels.get(channel, {}),
        }


    '''
    Handle name already being in use
    '''
    def _cmd_433(self, source, args):

        self.name += '_'
        self.introduce()


    '''
    Respond to server PING request for keep-alive
    '''
    def _cmd_PING(self, source, args):

        self.send('PONG %s' % args[-1])


    '''
    Re-get all the names in the channel when a user leaves
    '''
    def _cmd_PART(self, source, args):

        channel = args.pop(0)

        self.send('NAMES %s' % channel)


    '''
    Handle when a new user joins the room
    '''
    def _cmd_JOIN(self, source, args):

        channel = args.pop(0)

        self.send('NAMES %s' % channel)


    '''
    '''
    def _cmd_QUIT(self, source, args):

        channel = args.pop(0)

        self.send('NAMES %s' % channel)


    '''
    Handle all incoming messages
    '''
    @Synapse('IRC_PRIVMSG')
    def _cmd_PRIVMSG(self, source, args):

        # Parse the incoming message for a command with the selected command prefix
        match = re.search('^{0}(\w+)[ ]?(.+)?'.format(self.settings.bot.command_prefix), args[-1])
        if not match:
            return (source, args)

        # Parse the user, targer, command and arguments information
        user = Id(source)
        target = args[0] if args[0] != self.name else user.nick
        command = match.group(1)
        arguments = match.group(2)

        print "*** target: %s; user: %s" % (target, user.nick)


        # Only listen to authenticated users
        if not user.is_authenticated:
            self.send('PRIVMSG %s :My daddy says not to listen to you.' % target)
            return (source, args)

        # If there was no command specified, return the source and args so any bound
        # Receptors can get triggered with the same information
        if not command:
            return (source, args)

        # Butler that command out yo
        if arguments:
            self.cx.values = arguments
        else:
            self.cx.values = False

        self.cx.context = target
        self.cx.butler.do(self.cx.command, (source, args[-1]))

        return (source, args)

