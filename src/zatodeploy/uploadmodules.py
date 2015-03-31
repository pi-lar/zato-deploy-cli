#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# zatodeploy/uploadmodules.py
#
"""Command line script to hot-deploy zato service modules via JSON-HTTP."""

from __future__ import absolute_import, print_function

import argparse
import base64
import glob
import logging
import sys

from os.path import basename, exists

# do not use relative import here, because this module should be executable
# as a command line script
from zatodeploy.common import json_call, read_ini_config


log = logging.getLogger(__name__)


def upload_service(config, filename):
    """Make a JSON-HTTP call to Zato to upload a service module.

    The service module is read from the given local Python source file, encoded
    with base64 and then uploaded via the 'zato.service.upload-package'
    service.

    """
    data = {
        'cluster_id': config.cluster,
        'payload_name': basename(filename)
    }

    with open(filename) as py:
        data['payload'] = base64.b64encode(py.read())

    json_call('zato.service.upload-package', data, config)
    log.info("Service module {} uploaded successfully.".format(filename))


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

    for target in targets:
        if target not in config:
            msg = ("Deployment target '{}' not defined in deployment "
                   "configuration.".format(target))
            log.error(msg)
            return msg

        target_services = []
        for srv in config[target].get('modules', '').split(','):
            srv = srv.strip()

            if not srv:
                continue

            target_services.extend(glob.glob(srv))

        log.debug("Service modules to deploy to target '{}': {}".format(
            target, ", ".join(target_services)))

        config[target].setdefault('verbose', args.verbose)

        if target_services:
            for module in target_services:
                if exists(module):
                    upload_service(config[target], module)
                else:
                    msg = ("Service module file '{}' not found. "
                           "Aborting.".format(module))
                    log.error(msg)
                    return msg
        else:
            log.info(
                "No service modules to deploy for target '{}'.".format(target))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
