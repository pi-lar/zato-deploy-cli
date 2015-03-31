#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# zatodeploy/deleteservices.py
#
"""Command line script to delete a zato service via JSON-HTTP.

Call this script to delete one or more services from the Zato cluster.

The script looks for a configuration file named 'undeploy.conf' in the current
directory by default. The ``-c|--config` commmand line option can be used to
specify another configuration file.
In this configuration file the script looks for a section ``[zato]`` with the
general settings of the Zato cluster. See the documentation for the
``deploy.conf`` configuration file for more information. All other sections
define (un-)deployment targets. By default, the script acts on all defined
targets, but you can also specify one or more targets on the command line as
positional arguments.

The ``deleteservices.py`` script looks in each target section for a setting
named ``services``. This setting must be a comma-separated list of service name
patterns. Every service existing in the Zato cluster with a name matching one
of the patterns will be deleted. All incoming channels referrring to a deleted
service will be deleted by Zato as well!

The syntax of this script's configuration file is compatible with the
configuration file used by other deployment scripts. The deployment scripts,
which create objects in the Zato cluster or upload service modules, use a
configuration file named ``deploy.conf`` by default. Since they use different
settings in the target sections, it is safe to use the same configuration file
for all scripts. You could e.g. just make a symlink from ``deploy.conf`` to
``undeploy.conf``. The scripts use different default names to make it harder to
delete objects in the Zato server by mistake.

"""

from __future__ import absolute_import, print_function

import argparse
import fnmatch
import logging
import sys

# do not use relative import here, because this module should be executable
# as a command line script
from zatodeploy.common import (get_service_list, json_call, read_ini_config)


log = logging.getLogger(__name__)

REQUIRED_FIELDS = {
    'plain_http': ('connection', 'data_format', 'name', 'service', 'transport',
        'url_path'),
    'soap': ('connection', 'data_format', 'name', 'service', 'soap_action',
        'soap_version', 'transport', 'url_path'),
}


def delete_service(config, service_id):
    """Delete an already deployed service via JSON call."""
    # create POST data
    data = dict(id=service_id)

    # do JSON call
    json_call('zato.service.delete', data, config)
    log.info("Service with ID {} deleted.".format(service_id))


def main(args=None):
    """Main script entry point function.

    Parses command line arguments and configuration file and loops through
    the deployment targets and performs the deployment task at hand on each
    requested target.

    """
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-v', '--verbose', action="store_true",
        help="Enable verbose output")
    ap.add_argument('-c', '--config', default="undeploy.conf",
        help="Deployment configuration settings file (default: %(default)s)")
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

        existing_services = get_service_list(config[target])
        log.debug("Existing (non-internal) services on zato cluster: %s",
                  ", ".join(srv.name for srv in existing_services))

        patterns = [ptn.strip()
            for ptn in config[target].get('services', '').split(',')
                if ptn.strip()]

        log.debug("Service patterns for target '{}': {}".format(
            target, ", ".join(patterns)))

        target_services = set()
        for service in existing_services:
            for ptn in patterns:
                if fnmatch.fnmatch(service.name, ptn):
                    target_services.add((service.name, service.id))

        log.debug("Services matching patterns for target '{}': {}".format(
            target, ", ".join(srv[0] for srv in target_services)))

        config[target].setdefault('verbose', args.verbose)

        if target_services:
            for name, id_ in target_services:
                delete_service(config[target], id_)
        else:
            log.info("No services to delete for target '{}'.".format(target))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
