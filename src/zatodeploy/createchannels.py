#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# zatodeploy/createchannels.py
#
"""Command-line script to create plain_http/SOAP Zato channels via JSON-HTTP.

Reads configuration file ``channels.conf`` by default.

Run ``zato-createchannels -h`` for usage help.

"""

from __future__ import absolute_import, print_function

import argparse
import logging
import re
import sys

from os.path import exists

# do not use relative import here, because this module should be executable
# as a command line script
from zatodeploy.common import (find_security_id, get_channel_list,
    get_service_list, json_call, read_ini_config)


log = logging.getLogger(__name__)

REQUIRED_FIELDS = {
    'plain_http': ('connection', 'data_format', 'name', 'service', 'transport',
        'url_path'),
    'soap': ('connection', 'data_format', 'name', 'service', 'soap_action',
        'soap_version', 'transport', 'url_path'),
}


def create_or_update_channel(config, channel, update=False):
    """Make a JSON-HTTP call to Zato to create/update an incoming channel."""
    # create POST data
    data = dict(
        connection='channel',
        cluster_id=config.cluster,
        is_active=True,
        is_internal=False,
        security_id=None
    )
    # updating possibly overwrites defaults
    data.update(channel)
    if update:
        data['id'] = update

    log.debug("Channel data: %r", data)

    # validate channel data
    if data['connection'] != 'channel':
        raise ValueError("'connection' field of channel data must be set to "
                         "'channel'.")

    transport = data.get('transport')

    if transport == 'soap':
        if data.setdefault('data_format', 'xml') != 'xml':
            raise ValueError("'data_format' of SOAP channels must be 'xml'.")
        if data.setdefault('soap_version', '1.1') != '1.1':
            raise ValueError("'soap_version' of SOAP channels must be '1.1'.")
    elif transport == 'plain_http':
        data.setdefault('data_format', '')

    if transport in ('plain_http', 'soap'):
        for field in REQUIRED_FIELDS[transport]:
            if data.get(field) is None:
                raise ValueError("Required field '{}' not set in channel "
                                 "data".format(field))
    else:
        raise ValueError("'transport' field of channel data must be either "
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
    log.info("Channel '{}' (ID: {}) {} operation successful.".format(
        channel['name'], res[response_name].id, method))


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
    ap.add_argument('--channels', default="channels.conf",
        help="Channel definition file (default: %(default)s)")
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
    if exists(args.channels):
        channels = read_ini_config(args.channels)
        log.debug("Channel definitions:\n%s", channels)
    else:
        log.warning("Channel definitions file '%s' not found. Nothing to do.",
            args.channels)
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

        target_channels = [ch.strip()
            for ch in config[target].get('channels', '').split(',')
                if ch.strip()]

        if target_channels == ['*']:
            target_channels = list(channels.keys())

        log.debug("Channels for target '{}': {}".format(
            target, ", ".join(target_channels)))

        existing_channels = dict((ch.name, ch)
                                 for ch in get_channel_list(config[target]))
        log.debug("Existing channels on zato cluster: %s",
                  ", ".join(existing_channels))

        config[target].setdefault('verbose', args.verbose)

        existing_services = [srv.name for srv in
                             get_service_list(config[target], '*')]
        log.debug("Existing (non-internal) services on zato cluster: %s",
                  ", ".join(existing_services))

        if target_channels:
            for ident in target_channels:
                channel = channels.get(ident)
                if channel:
                    service = channel.get('service')
                    if service not in existing_services:
                        raise ValueError("Channel '{}' references unknown "
                            "service '{}'".format(channel.name, service))

                    if channel.name in existing_channels:
                        log.info("Channel '{}' already exists in zato "
                                 "cluster. Updating.".format(channel.name))
                        create_or_update_channel(config[target], channel,
                            update=existing_channels[channel.name].id)
                    else:
                        create_or_update_channel(config[target], channel)
                else:
                    msg = ("Channel '{}' for target '{}' not found "
                        "in channel definitions".format(ident, target))
                    log.error(msg)
                    return msg
        else:
            log.info("No channels to create for target '{}'.".format(target))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
