#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# zatodeploy/common.py
#
"""Common functions for zato services deployment scripts."""

from __future__ import absolute_import, print_function, unicode_literals

# standard library
import logging

from collections import OrderedDict
from os.path import exists

try:
    from ConfigParser import SafeConfigParser
except ImportError:
    # Python 3
    from configparser import SafeConfigParser

# zato
from bunch import bunchify
from zato.client import JSONClient


__all__ = (
    'JSONCallResponseError',
    'find_security_id',
    'get_basic_auth_list',
    'get_channel_list',
    'get_http_soap_list',
    'get_outgoing_list',
    'get_security_list',
    'get_service_list',
    'json_call',
    'read_ini_config'
)

log = logging.getLogger(__name__)

SERVICE_URLS = {
    'zato.http-soap.create': "/zato/json/zato.http-soap.create",
    'zato.security.get-list': "/zato/json/zato.security.get-list",
    'zato.service.upload-package': "/zato/json/zato.service.upload-package",
    'zato.http-soap.get-list': "/zato/json/zato.http-soap.get-list",
    'zato.http-soap.edit': "/zato/json/zato.http-soap.edit",
    'zato.security.basic-auth.create':
        "/zato/json/zato.security.basic-auth.create",
    'zato.security.basic-auth.edit':
        "/zato/json/zato.security.basic-auth.edit",
    'zato.security.basic-auth.change-password':
        "/zato/json/zato.security.basic-auth.change-password",
    'zato.service.delete': "/zato/json/zato.service.delete",
    'zato.service.get-list': "/zato/json/zato.service.get-list"
}


class JSONCallResponseError(Exception):
    """Raised if a JSON service call does not return a proper Zato response.

    Or if it has a non-sucessfull result code.

    """


def json_call(service, data, config):
    """Make a call to a Zato service from a set list with JSON POST data.

    The service URLs are configured in the SERVICE_URL module global
    dictionary with the service name as written in the header of the Zato
    service documentation page as the key.

    @params service: service name
    @param data: dictionary of data to send a JSON post data
    @param config: configuration dictionary as read from 'deploy.conf'

    """
    address = 'http://%s:%s' % (config.lb_host, config.lb_port)
    try:
        path = SERVICE_URLS[service]
    except KeyError:
        log.error("Unknown zato JSON service name: 5s", service)
        raise

    auth = (config.http_user, config.http_password)
    client = JSONClient(address, path, auth)
    log.debug("Invoking service at '%s' with data: %s", path, data)
    res = client.invoke(data)

    if not res.ok:
        raise JSONCallResponseError(
            "Zato non-successful result code: {}".format(res))

    return bunchify(res.data)


def find_security_id(name, config):
    """Look up ID of security definition matching name.

    Does a simple substring match. Raises ValueError if there are multiple
    matches. Raises KeyError when no match is found.

    """
    result = None
    for secdef in get_security_list(config):
        if name in secdef.name:
            if result is not None:
                raise ValueError("Ambiguous security definition name '{}'. "
                    "Found mutiple matches".format(name))
            else:
                result = secdef.id

    if result is None:
        raise KeyError(
            "No security definition matching '{}' found.".format(name))

    return result


def get_security_list(config):
    """Return zato security definitions as a list of Bunch objects."""
    data = {'cluster_id': config.cluster}
    res = json_call('zato.security.get-list', data, config)
    return res.zato_security_get_list_response


def get_basic_auth_list(config):
    """Return zato HTTP Basic Auth security defs as a list of Bunch objects."""
    return [auth for auth in get_security_list(config)
        if auth.get('sec_type') == 'basic_auth']


def get_http_soap_list(config, connection, transport):
    """Return zato HTTP/SOAP objects as list of Bunch objects."""
    data = dict(cluster_id=int(config.cluster), connection=connection,
                transport=transport)
    res = json_call('zato.http-soap.get-list', data, config)
    return res.zato_http_soap_get_list_response


def get_channel_list(config):
    """Return zato channels as list of Bunch objects."""
    res = []
    for transport in ('plain_http', 'soap'):
        res.extend(get_http_soap_list(config, 'channel', transport))
    return res


def get_outgoing_list(config):
    """Return zato channels as list of Bunch objects."""
    res = []
    for transport in ('plain_http', 'soap'):
        res.extend(get_http_soap_list(config, 'outgoing', transport))
    return res


def get_service_list(config, filter=None):
    """Return zato services as list of Bunch objects."""
    data = dict(
        cluster_id=int(config.cluster),
        name_filter=filter or '*')
    res = json_call('zato.service.get-list', data, config)
    return res.zato_service_get_list_response


def _read_includes(cp):
    """Read included configuration files.

    Loop through options in 'include' section.

    Each option names a file to include. The value of the option is a
    comma-separated list of sections to read from the included file.

    """
    for option in cp.options('include'):
        sections = [sect.strip()
            for sect in cp.get('include', option).split(',')
            if sect.split()]

        inc = SafeConfigParser(allow_no_value=True)
        inc.read(option)

        inc_sections = inc.sections()
        cp_sections = cp.sections()

        if not sections:
            sections = [sect for sect in inc_sections if sect != 'include']

        for sect in sections:
            if sect in inc_sections:
                if sect not in cp_sections:
                    cp.add_section(sect)

                for opt, value in inc.items(sect):
                    if not cp.has_option(sect, opt):
                        cp.set(sect, opt, value)

    cp.remove_section('include')

def read_ini_config(filename):
    """Read INI config from given filename and return it as a nested dict."""
    if not exists(filename):
        raise IOError("Configuration file not found: {}".format(filename))

    cp = SafeConfigParser(allow_no_value=True)
    cp.read(filename)
    config = OrderedDict()

    if 'include' in cp.sections():
        _read_includes(cp)

    for section in cp.sections():
        s = OrderedDict()
        if 'zato' in cp.sections():
            for option in cp.options('zato'):
                s[option] = cp.get('zato', option)
        for option in cp.options(section):
            s[option] = cp.get(section, option)
        config[section] = bunchify(s)

    return config
