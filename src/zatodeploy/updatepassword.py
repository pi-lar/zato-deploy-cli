#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# zatodeploy/updatepassword.py
#
"""Command-line script to update password of a security definition in Zato ODB.

Run ``updatepassword -h`` for usage help.

This script changes the password directly in the Zato ODB.

"""

from __future__ import absolute_import, print_function

import argparse

from json import load
from os.path import join

from bunch import bunchify

import sqlalchemy

from zato.cli import ManageCommand
from zato.cli.zato_command import add_opts
from zato.common.crypto import CryptoManager
from zato.common.odb.model import HTTPBasicAuth


def get_arg_parser(opts):
    """Create and return argument parser for command."""
    parser = argparse.ArgumentParser()

    # copied form zato.ci.zato_command.get_parser()
    parser.add_argument('--store-log',
        help='Whether to store an execution log', action='store_true')
    parser.add_argument('--verbose',
        help='Show verbose output', action='store_true')
    parser.add_argument('--store-config', action='store_true',
        help='Whether to store config options in a file for a later use')
    add_opts(parser, opts)

    return parser


class UpdateSecDefPassword(ManageCommand):
    """Update the Password of a security definition in the Zato ODB."""

    opts = [
        {
            'name': 'path',
            'help': 'Path to the Zato web-admin component'
        },
        {
            'name': 'secdef',
            'help': 'Name of security definition to change the password of'
        },
        {
            'name': 'password',
            'help': 'New password for security definition'
        }
    ]

    def __init__(self):
        """Initialize this zato.cli.ZatoCommand sub-class with command line."""
        parser = get_arg_parser(self.opts)
        self.args = parser.parse_args()
        super(UpdateSecDefPassword, self).__init__(self.args)

    def _on_web_admin(self, args):
        """Load ODB using component config and update security definition."""
        config_file = join(self.config_dir, 'repo', 'web-admin.conf')

        with open(config_file) as fp:
            c = bunchify(load(fp))

        private_key = join(self.config_dir, 'repo', 'web-admin-priv-key.pem')
        cm = CryptoManager(priv_key_location=private_key)
        cm.load_keys()
        db_password = cm.decrypt(c.DATABASE_PASSWORD)

        engine_url = "%s://%s:%s@%s:%s/%s" % (
            c.db_type,
            c.DATABASE_USER,
            db_password,
            c.DATABASE_HOST,
            c.DATABASE_PORT,
            c.DATABASE_NAME)

        engine = sqlalchemy.create_engine(engine_url)
        session = self._get_session(engine)

        if engine.dialect.has_table(engine.connect(), 'sec_basic_auth'):
            try:
                secdef = session.query(HTTPBasicAuth).filter(
                    HTTPBasicAuth.name == args.secdef).one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.logger.error(
                    "Security definition '%s' not found.", args.secdef)
                return 1

            self.logger.info("Security definition: %s" % secdef.name)
            self.logger.info("Username: %s" % secdef.username)
            self.logger.info("Old password: %s" % secdef.password)
            self.logger.info("Setting new password.")
            secdef.password = args.password
            session.commit()
            self.logger.info('OK')
        else:
            msg = "Zato ODB does not seem to have been set up yet."
            self.logger.error(msg)
            return self.SYS_ERROR.NO_ODB_FOUND

    def _on_lb(self, args):
        """Print error when wrong zato component is specified."""
        msg = "Component specified by path must be a Zato web-admin instance."
        self.logger.error(msg)
        return 1

    _on_server = _on_lb


if __name__ == '__main__':
    cmd = UpdateSecDefPassword()
    cmd.run(cmd.args)
