# -*- coding: utf-8 -*-
"""Test services for deployment scripts tests.

@author: carndt

"""

from __future__ import absolute_import, print_function, unicode_literals

__all__ = ('DeployTestService1', 'DeployTestService2')

# zato
from zato.server.service import Service


class DeployTestService1(Service):
    """Test service 1 for deployment scripts."""

    @classmethod
    def get_name(cls):
        """Return service name."""
        return "deploy-test-service-1"

    def handle(self):
        """Handle request and return service name."""
        self.response.payload = '{"service": "%s"}' % self.get_name()


class DeployTestService2(DeployTestService1):
    """Test service 2 for deployment scripts."""

    @classmethod
    def get_name(cls):
        """Return service name."""
        return "deploy-test-service-2"
