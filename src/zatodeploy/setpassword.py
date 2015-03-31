#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Set/Update password of a zato HTTP basic auth security definition.

This works by calling the service to change the password through the
"zato service invoke" command line interface. That way one doesn't need to
know the current password protecting the internal zato services.

"""

from __future__ import print_function, unicode_literals

import argparse
import sys

from json import dumps
from subprocess import check_output, CalledProcessError, STDOUT


def set_password(server_path, cluster_id, username, password):
    """Call zato command client to set password for a securizty definition."""
    requestdata = dumps(dict(cluster_id=int(cluster_id)))

    try:
        secdefs = check_output(["zato", "service", "invoke", "--payload",
            requestdata, server_path, "zato.security.get-list"], stderr=STDOUT)
    except CalledProcessError as exc:
        raise IOError("Could not get list of security definitions: %s" % exc)
    else:
        secdefs = dict((s['username'], s) for s in eval(secdefs))

    if username in secdefs:
        requestdata = dumps(dict(id=secdefs[username]["id"],
            password1=password, password2=password))
        try:
            check_output(["zato", "service", "invoke", "--payload",
                requestdata, server_path,
                "zato.security.basic-auth.change-password"], stderr=STDOUT)
        except CalledProcessError as exc:
            raise IOError("Error setting password for user '%s': %s" %
                          (username, exc))
        else:
            print("Password updated sucessfully for user '%s'." % username)
    else:
        raise KeyError("No security definition with username '%s' found." %
                       username)


def main(args):
    """Main script entry point function.

    Parses command line arguments and calls the ``set_password`` function.

    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", default=1,
        help="ID of zato cluster (default: %(default)s)")
    ap.add_argument("serverpath", metavar="PATH",
        help="Path to zato server component")
    ap.add_argument("username", metavar="USERNAME",
        help="Username of HTTP basic auth security definition")
    ap.add_argument("password", metavar="PASSWD",
        help="New password to set")

    args = ap.parse_args(args if args is not None else sys.argv[1:])

    try:
        set_password(
            args.serverpath, args.cluster, args.username, args.password)
    except Exception as exc:
        print(exc.message)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
