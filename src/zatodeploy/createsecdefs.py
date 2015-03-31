#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# zatodeploy/createsecdefs.py
#
"""Command line script to create zato HHTP Basis Auth security definitions.

Reads configuration file ``secdefs.conf`` by default.

Run ``zato-createsecdefs -h`` for usage help.

"""

from __future__ import absolute_import, print_function

import argparse
import logging
import sys

from os.path import exists

# do not use relative import here, because this module should be executable
# as a command line script
from zatodeploy.common import (get_security_list, json_call,
    read_ini_config)


log = logging.getLogger(__name__)

REQUIRED_FIELDS = ('name', 'username', 'realm', 'password')


def create_or_update_secdef(config, secdef, update=False):
    """Make a JSON-HTTP call to Zato to create/update a security definition."""
    # create POST data
    data = dict(
        cluster_id=config.cluster,
        is_active=True
    )
    # updating possibly overwrites defaults
    data.update(secdef)
    if update:
        data['id'] = update

    log.debug("Security definition data: %r", data)

    # validate secdef data
    for field in REQUIRED_FIELDS:
        if data.get(field) is None:
            raise ValueError("Required field '{}' not set in security "
                             "definition data".format(field))

    password = data.pop('password')

    # do JSON call
    method = 'edit' if update else 'create'
    res = json_call('zato.security.basic-auth.%s' % method, data, config)
    if res.zato_env.result == "ZATO_OK":
        secdef_id = res['zato_security_basic_auth_%s_response' % method].id
        log.info("Security definition '%s' (ID: %s) %s operation successful.",
            secdef['name'], secdef_id, method)
        data = dict(id=secdef_id, password1=password, password2=password)
        res = json_call('zato.security.basic-auth.change-password',
                        data, config)
        log.info("Security definition '%s' password updated.", secdef['name'])


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
    ap.add_argument('--secdefs', default="secdefs.conf",
        help="Security definitions file (default: %(default)s)")
    ap.add_argument('targets', nargs="*",
        help="Deployment targets (default: all)")

    args = ap.parse_args(args if args is not None else sys.argv[1:])

    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel)

    config = read_ini_config(args.config)
    log.debug("Deployment configuration:\n%s", config)
    if exists(args.secdefs):
        secdefs = read_ini_config(args.secdefs)
        log.debug("Security definitions:\n%s", secdefs)
    else:
        log.warning("Security definitions file '%s' not found. Nothing to do.",
            args.secdefs)
        return 0

    targets = (args.targets if args.targets
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

        target_secdefs = [ch.strip()
            for ch in config[target].get('secdefs', '').split(',')
                if ch.strip()]

        if target_secdefs == ['*']:
            target_secdefs = list(secdefs.keys())

        log.debug("Security definitions for target '%s': %s", target,
                  ", ".join(target_secdefs))

        existing_secdefs = dict((ch.name, ch)
                                for ch in get_security_list(config[target]))
        log.debug("Existing security definitions on zato cluster: %s",
                  ", ".join(existing_secdefs))

        config[target].setdefault('verbose', args.verbose)

        if target_secdefs:
            for ident in target_secdefs:
                secdef = secdefs.get(ident)
                if secdef:
                    if secdef.name in existing_secdefs:
                        log.info("Security definition '%s' already exists in "
                                 "zato cluster. Updating.", secdef.name)
                        create_or_update_secdef(config[target], secdef,
                            update=existing_secdefs[secdef.name].id)
                    else:
                        create_or_update_secdef(config[target], secdef)
                else:
                    msg = ("Security definition '{}' for target '{}' not found"
                           " in definitions".format(ident, target))
                    log.error(msg)
                    return msg
        else:
            log.info("No security definitions to create for target '%s'.",
                     target)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
