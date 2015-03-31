#!/usr/bin/env py
# -*- coding: utf-8 -*-
#
# zatodeploy/storesettings.py
#
"""Read service settings from JSON file and load them into a Redis DB."""

from __future__ import absolute_import, print_function, unicode_literals

# standard library
import argparse
import json
import logging
import sys

from os.path import exists

# third-party
import redis

# do not use relative import here, because this module should be executable
# as a command line script
from zatodeploy.common import read_ini_config


REDIS_HOST = 'localhost'
REDIS_PORT = 6379
SETTINGS_VERSION = "1.0"

log = logging.getLogger(__name__)


class SettingsError(Exception):
    """Exception raised when settings are malformed or incompatible."""


def read_settings(filename):
    """Read settings from a JSON file and return them as a dictionary."""
    with open(filename) as settingsfile:
        data = json.load(settingsfile)
        if (isinstance(data, dict) and
                data.get('version') == SETTINGS_VERSION and
                'settings' in data and 'urn' in data):
            return data['urn'], data['settings']
        else:
            raise SettingsError("Could not parse settings file '%s'." %
                                filename)


def write_settings_to_db(settings, urn, host, port, db=0, password=None):
    """Write given settings dictionary to Redis on specified host and port."""
    redisc = redis.StrictRedis(host=host, port=port, db=db, password=password)

    with redisc.pipeline() as pipe:
        pipe.delete(urn)
        pipe.set(urn, json.dumps(settings))
        pipe.execute()


def main(args=None):
    """Main script entry point function.

    Parses command line arguments and configuration file and loops through
    the deployment targets and performs the deployment task at hand on each
    requested target.

    """
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-v', '--verbose', action="store_true",
        help="Enable verbose output")
    ap.add_argument('-c', '--config', default="deploy.conf",
        help="Deployment configuration settings file (default: %(default)s)")
    ap.add_argument('target', nargs="*",
        help="Deployment target(s) (default: all)")

    args = ap.parse_args(args if args is not None else sys.argv[1:])

    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel)

    config = read_ini_config(args.config)
    log.debug("Deployment configuration:\n%s", config)
    targets = (args.target if args.target
               else [k for k in config if k != 'zato'])
    log.debug("Deployment targets: %s", ", ".join(targets))
    config.verbose = args.verbose

    if not targets:
        msg = "No deployment targets defined in deployment configuration."
        log.error(msg)
        return msg

    redis_connections = set()

    for target in targets:
        if target not in config:
            msg = ("Deployment target '{}' not defined in deployment "
                   "configuration.".format(target))
            log.error(msg)
            return msg

        settings_fn = config[target].get('settings')

        if settings_fn:
            if exists(settings_fn):
                try:
                    urn, settings = read_settings(settings_fn)
                except Exception as exc:
                    msg = "Could not load settings: %s" % exc
                    log.error(msg)
                    return(msg)
            else:
                msg = "Settings file '%s' not found. Aborting." % settings_fn
                log.warn(msg)
                return msg
        elif exists('settings.conf'):
            try:
                urn, settings = read_settings('settings.conf')
            except Exception as exc:
                msg = "Could not load settings: %s" % exc
                log.error(msg)
                return(msg)
        else:
            log.info("No settings file specified and no default file found.")
            continue

        host = config[target].get('kvdb_host') or REDIS_HOST
        port = int(config[target].get('kvdb_port') or REDIS_PORT)
        db = int(config[target].get('kvdb_db') or 0)
        password = config[target].get('kvdb_password') or None
        log.debug("Redis connection settings: host='%s' port=%s db=%i",
                  host, port, db)

        if (host, port) not in redis_connections:
            redis_connections.add((host, port, db))
            try:
                write_settings_to_db(settings, urn, host, port, db, password)
            except redis.ResponseError as exc:
                log.error("Could not write settings to Redis DB: %s", exc)
                return 1
        else:
            log.info("Redis database %i at %s:%s already updated.",
                     db, host, port)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
