#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# zatodeploy/createoutgoings.py
#
"""Command line script to create zato Plain HTTP/SOAP outgoings via JSON-HTTP.

Reads configuration file ``outgoings.conf`` by default.

Run ``zato-createoutgoings -h`` for usage help.

"""

from __future__ import absolute_import, print_function

import argparse
import logging
import re
import sys

from os.path import exists

# do not use relative import here, because this module should be executable
# as a command line script
from zatodeploy.common import (find_security_id, get_outgoing_list,
    json_call, read_ini_config)


log = logging.getLogger(__name__)

REQUIRED_FIELDS = {
    'plain_http': ('connection', 'host', 'name', 'transport', 'url_path'),
    'soap': ('connection', 'host', 'name', 'soap_action', 'soap_version',
        'transport', 'url_path'),
}


def create_or_update_outgoing(config, outgoing, update=False):
    """Make a JSON-HTTP call to Zato to create/update an outgoing channel."""
    # create POST data
    data = dict(
        connection='outgoing',
        cluster_id=config.cluster,
        is_active=True,
        is_internal=False,
        ping_method='HEAD',
        pool_size=200,
        timeout=10
    )
    # updating possibly overwrites defaults
    data.update(outgoing)
    if update:
        data['id'] = update

    log.debug("Outgoing data: %r", data)

    # validate outgoing data
    if data['connection'] != 'outgoing':
        raise ValueError("'connection' field of outgoing data must be set to "
                         "'outgoing'.")

    transport = data.get('transport')

    if transport == 'soap':
        if data.setdefault('soap_version', '1.1') not in ('1.1', '1.2'):
            raise ValueError("'soap_version' of SOAP outgoings must be '1.1'"
                             "or '1.2'.")

    if transport in ('plain_http', 'soap'):
        for field in REQUIRED_FIELDS[transport]:
            if data.get(field) is None:
                raise ValueError("Required field '{}' not set in outgoing "
                                 "data".format(field))
    else:
        raise ValueError("'transport' field of outgoing data must be either "
                         "'plain_http' or 'soap'.")

    # check dependencies
    # is security_id a name?
    if isinstance(data.get('security_id'), basestring):
        data['security_id'] = data['security_id'].strip()
    if data.get('security_id') and not re.match(r'\d+', data['security_id']):
        data['security_id'] = find_security_id(data['security_id'], config)
    # Fix empty value
    if not data.get('security_id'):
        data['security_id'] = None

    # do JSON call
    method = 'edit' if update else 'create'
    method_name = 'zato.http-soap.%s' % method
    response_name = 'zato_http_soap_%s_response' % method
    res = json_call(method_name, data, config)
    log.info("Outgoing '{}' (ID: {}) {} operation successful.".format(
        outgoing['name'], res[response_name].id, method))


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
    ap.add_argument('--outgoings', default="outgoings.conf",
        help="Outgoing definition file (default: %(default)s)")
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
    if exists(args.outgoings):
        outgoings = read_ini_config(args.outgoings)
        log.debug("Outgoing definitions:\n%s", outgoings)
    else:
        log.warning("Outgoing definitions file '%s' not found. Nothing to do.",
            args.outgoings)
        return 0

    targets = (args.targets if args.targets
               else [k for k in config if k != 'zato'])
    log.debug("Deployment targets: %s", ", ".join(targets))

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

        target_outgoings = [og.strip()
            for og in config[target].get('outgoings', '').split(',')
                if og.strip()]

        if target_outgoings == ['*']:
            target_outgoings = list(outgoings.keys())

        log.debug("Outgoings for target '{}': {}".format(
            target, ", ".join(target_outgoings)))

        existing_outgoings = dict((ch.name, ch)
                                 for ch in get_outgoing_list(config[target]))
        log.debug("Existing outgoings on zato cluster: %s",
                  ", ".join(existing_outgoings))

        config[target].setdefault('verbose', args.verbose)

        if target_outgoings:
            for ident in target_outgoings:
                outgoing = outgoings.get(ident)
                if outgoing:
                    if outgoing.name in existing_outgoings:
                        log.info("Outgoing '{}' already exists in zato "
                                 "cluster. Updating.".format(outgoing.name))
                        create_or_update_outgoing(config[target], outgoing,
                            update=existing_outgoings[outgoing.name].id)
                    else:
                        create_or_update_outgoing(config[target], outgoing)
                else:
                    msg = ("Outgoing '{}' for target '{}' not found "
                        "in outgoing definitions".format(ident, target))
                    log.error(msg)
                    return msg
        else:
            log.info("No outgoings to create for target '{}'.".format(target))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
