import random
import os

from autonomic import axon, alias, help, Dendrite, Cerebellum, Receptor
from config import load_config
from util import totp


# Allz the webs stuff.
@Cerebellum
class Webserver(Dendrite):

    def __init__(self, cortex):
        super(Webserver, self).__init__(cortex)

    def _setaccess(self):
        return totp.now()

    @axon
    @help("<Get one-time link to chat log>")
    def chatlink(self):
        num = self._setaccess()
        link = "%s/chatlogs?onetime=%s" % (self.config.website.url, str(num))
        self.chat(link)

    @axon
    @help("<Get one-time link to error log>")
    def errorlink(self):
        num = self._setaccess()
        link = "%s/errorlog?onetime=%s" % (self.config.website.url, str(num))
        self.chat(link)

    @axon
    @help("<get link to appropriate [sic] http codes for describing dating>")
    def pigs(self):
        link = "%s/codez" % self.config.website.url
        self.chat(link)

    @axon
    @help("<Reload uwsgi server>")
    def reloadserver(self, quiet=False):
        os.system('touch %' % self.config.website.reload)
        if not quiet:
            self.chat("Reloaded uwsgi")
