import sys
import cortex

from config import load_config
from time import sleep, mktime, localtime

# Welcome to the beginning of a very strained brain metaphor!
# This is the shell for running the cortex. Ideally, this will never
# fail and you never have to reboot. Hah! I make funny, yes? More
# important, if you make changes to this file, you have to reboot as
# a reload won't change it.
class Medulla:
    def __init__(self):

        print '* Becoming self-aware'
        self.settings = settings = load_config('config/settings.yaml')
        self.secrets = secrets = load_config('config/secrets.yaml')

        self.ENABLED = self.settings.plugins.values().pop(0)
        self.active = True
        self.brain = cortex.Cortex(self)

        # The pulse file is set as a measure of how
        # long the bot has been spinning its gears
        # in a process. If it can't set the pulse
        # for too long, a signal kills it and reboots.
        # Note: this has become less of an issue
        # since all the bot's commands became threaded
        print '* Establishing pulse'
        self.setpulse()

        print '* Running monitor'

        while True:
            sleep(0.1)
            self.brain.monitor()
            if mktime(localtime()) - self.lastpulse > 10:
                self.setpulse()

    # Reload has to be run from here to update the
    # cortex.
    def reload(self, quiet=False):
        if self.brain.values and len(self.brain.values[0]):
            quiet = True

        if not quiet:
            self.brain.act('strokes out.')
        else:
            self.brain.act('strokes out.', False, self.secrets.owner)

        for channel in self.secrets.channels:
            name, attr = channel.popitem()
            if attr.primary:
                continue
            self.brain.brainmeats['channeling'].leave(name)

        self.active = False

        self.settings = settings = load_config('config/settings.yaml')
        self.secrets = secrets = load_config('config/secrets.yaml')

        import datastore
        import util
        import autonomic
        import cortex
        reload(datastore)
        reload(autonomic)
        reload(util)
        reload(cortex)
        self.brain = cortex.Cortex(self)
        self.brain.loadbrains(True)
        self.brain.getnames()

        self.active = True

        if not quiet:
            self.brain.act('comes to.')
        else:
            self.brain.act('comes to.', False, self.secrets.owner)

    def setpulse(self):
        self.lastpulse = mktime(localtime())
        pulse = open(self.settings.sys.pulse, 'w')
        pulse.write(str(self.lastpulse))
        pulse.close()

    def die(self, msg=None):
        if msg is not None:
            print msg
        sys.exit()

connect = Medulla()
