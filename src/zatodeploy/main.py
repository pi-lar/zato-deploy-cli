#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# deploy/main.py
#
"""Main command line script for Zato service component deployment.

@author: carndt

"""

from __future__ import absolute_import, print_function, unicode_literals

# standard library
import logging
import os
import sys
import time

from os.path import basename, exists, expanduser, join

# local modules
from .createchannels import main as create_channels
from .createoutgoings import main as create_outgoings
from .createsecdefs import main as create_secdefs
from .storesettings import main as store_settings
from .uploadmodules import main as upload_modules

# EXTRA_PATH
ZATO_EXTRA_PATHS = "/opt/zato/1.1/zato_extra_paths/"
EXTRA_PATHS_FILE = "extra_paths.txt"
log = logging.getLogger(__name__)


def add_extra_paths_from_file():
    """Link all modules listed in extra_paths.txt into zato_extra_paths."""
    if exists(EXTRA_PATHS_FILE):
        with open(EXTRA_PATHS_FILE, 'r') as fp:
            for filepath in fp:
                filepath = expanduser(filepath.rstrip())
                symlink = join(ZATO_EXTRA_PATHS, basename(filepath))
                if not exists(filepath):
                    log.warning("Path listed in '%s' does not exist: %s "
                        "Skipping it.", EXTRA_PATHS_FILE, filepath)
                    continue
                if not exists(symlink):
                    os.symlink(filepath, symlink)
                else:
                    log.warning("Symlink '%s' already exists. Skipping it.",
                        symlink)


def main(args=None):
    """Execute all deployment tasks in the right order."""
    logging.basicConfig(level=logging.INFO)

    add_extra_paths_from_file()
    create_secdefs(args)
    create_outgoings(args)
    store_settings(args)
    upload_modules(args)
    # give asynchronous upload operation some time to finish
    time.sleep(2)
    create_channels(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
