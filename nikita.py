#!/usr/bin/env python2
# -*- coding: utf-8-*-

import os
import sys
import shutil
import logging
import MySQLdb
import yaml
import argparse

from client import tts, stt, nikitapath, diagnose
from client.conversation import Conversation

# Add nikitapath.LIB_PATH to sys.path
sys.path.append(nikitapath.LIB_PATH)

parser = argparse.ArgumentParser(description='Nikita Voice Control Center')
parser.add_argument('--local', action='store_true',
                    help='Use text input instead of a real microphone')
parser.add_argument('--no-network-check', action='store_true',
                    help='Disable the network connection check')
parser.add_argument('--diagnose', action='store_true',
                    help='Run diagnose and exit')
parser.add_argument('--debug', action='store_true', help='Show debug messages')
parser.add_argument('--test', action='store_true',
                    help='Display messages instead of logging')
args = parser.parse_args()

if args.local:
    from client.local_mic import Mic
else:
    from client.mic import Mic


class Nikita(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

        # Create config dir if it does not exist yet
        if not os.path.exists(nikitapath.CONFIG_PATH):
            try:
                os.makedirs(nikitapath.CONFIG_PATH)
            except OSError:
                self._logger.error("Could not create config dir: '%s'",
                                   nikitapath.CONFIG_PATH, exc_info=True)
                raise

        # Check if config dir is writable
        if not os.access(nikitapath.CONFIG_PATH, os.W_OK):
            self._logger.critical("Config dir %s is not writable. Nikita " +
                                  "won't work correctly.",
                                  nikitapath.CONFIG_PATH)

        # FIXME: For backwards compatibility, move old config file to newly
        #        created config dir
        old_configfile = os.path.join(nikitapath.LIB_PATH, 'profile.yml')
        new_configfile = nikitapath.config('profile.yml')
        if os.path.exists(old_configfile):
            if os.path.exists(new_configfile):
                self._logger.warning("Deprecated profile file found: '%s'. " +
                                     "Please remove it.", old_configfile)
            else:
                self._logger.warning("Deprecated profile file found: '%s'. " +
                                     "Trying to copy it to new location '%s'.",
                                     old_configfile, new_configfile)
                try:
                    shutil.copy2(old_configfile, new_configfile)
                except shutil.Error:
                    self._logger.error("Unable to copy config file. " +
                                       "Please copy it manually.",
                                       exc_info=True)
                    raise

        # Read config
        self._logger.debug("Trying to read config file: '%s'", new_configfile)
        try:
            with open(new_configfile, "r") as f:
                self.config = yaml.safe_load(f)
        except OSError:
            self._logger.error("Can't open config file: '%s'", new_configfile)
            raise

        # Reset the log level to what is configured in the profile
        try:
            logLevel = self.config['logging']
        except KeyError:
            logLevel = 'TRANSCRIPT'
        if not args.debug:
            logger.setLevel(logLevel)

        try:
            stt_engine_slug = self.config['stt_engine']
        except KeyError:
            stt_engine_slug = 'sphinx'
            logger.warning("stt_engine not specified in profile, defaulting " +
                           "to '%s'", stt_engine_slug)
        stt_engine_class = stt.get_engine_by_slug(stt_engine_slug)

        try:
            slug = self.config['stt_passive_engine']
            stt_passive_engine_class = stt.get_engine_by_slug(slug)
        except KeyError:
            stt_passive_engine_class = stt_engine_class

        try:
            tts_engine_slug = self.config['tts_engine']
        except KeyError:
            tts_engine_slug = tts.get_default_engine_slug()
            logger.warning("tts_engine not specified in profile, defaulting " +
                           "to '%s'", tts_engine_slug)
        tts_engine_class = tts.get_engine_by_slug(tts_engine_slug)

        # connect to MySQL server
        db = MySQLdb.connect(host=self.config['MySQL']['server'],
                             port=3306, user=self.config['MySQL']['user'],
                             passwd=self.config['MySQL']['password'],
                             db="NIKITA")

        # Initialize Mic
        self.mic = Mic(tts_engine_class.get_instance(),
                       stt_passive_engine_class.get_passive_instance(),
                       stt_engine_class.get_active_instance(), db, self.config)

    def run(self):
        if 'first_name' in self.config:
            salutation = ("How can I be of service, %s?"
                          % self.config["first_name"])
        else:
            salutation = "How can I be of service?"
        self.mic.say('A', salutation)

        conversation = Conversation("NIKITA", self.mic, self.config)
        conversation.handleForever()

if __name__ == "__main__":
    """
        Nikita client/server edition
    """

    # add new log level to logger for transcripts
    # transcript is between 'WARNING' and 'INFO'
    TRANS_LVL = 25
    logging.addLevelName(TRANS_LVL, "TRANSCRIPT")

    def transcript(self, message, *args, **kws):
        self._log(TRANS_LVL, message, args, **kws)
    logging.Logger.transcript = transcript

    if args.test:
        print("**********************************************")
        print("*       NIKITA - Client/Server Edition       *")
        print("*                Test Mode                   *")
        print("**********************************************")
        logging.basicConfig()
    else:
        logging.basicConfig(filename='/var/log/nikita/nikita.log',
                            filemode='w', maxBytes='1024', backupCount='5')
    logger = logging.getLogger()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if not args.no_network_check and not diagnose.check_network_connection():
        logger.warning("Network not connected. This may prevent Nikita from " +
                       "running properly.")

    if args.diagnose:
        failed_checks = diagnose.run()
        sys.exit(0 if not failed_checks else 1)

    try:
        app = Nikita()
    except Exception:
        logger.error("Error occured!", exc_info=True)
        sys.exit(1)

    app.run()
