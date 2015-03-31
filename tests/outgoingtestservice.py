# -*- coding: utf-8 -*-
"""
Created on 25.02.2015

@author: carndt

"""

__all__ = ('OutgoingTestService')

from zato.server.service import Service

class OutgoingTestService(Service):
    name = "outgoing-test-service"
    out_name = "outgoing-test"

    def handle(self):
        self.logger.info("OutgoingTestService.handle called.")
        self.logger.info("Getting outgoing with name '%s'.", self.out_name)
        outgoing = self.outgoing.plain_http.get(self.out_name)
        self.logger.info("Outgoing: %r", outgoing)
