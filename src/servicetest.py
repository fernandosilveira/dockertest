import unittest

import service


class ServiceTest(unittest.TestCase):
    """Abstract class to instatiate docker containers as test fixtures."""

    def run(self, result=None):
        if not getattr(self, 'SERVICE', None):
            raise TypeError('A ServiceTest must declare SERVICE')

        port_request = getattr(self, 'PORTS', None)
        if not port_request:
            port_request = getattr(self, 'PORT', None)
        if not port_request:
            raise TypeError('A ServiceTest must declare either PORTS or PORT')

        with service.Container(self.SERVICE, port_request) as port_map:
            self.port_map = port_map

            # special case - when only one port was requested
            if isinstance(port_map, tuple):
                # N.B., this is just a shortcut, we don't remove self.port_map
                self.host, self.port = port_map

            super(ServiceTest, self).run(result)
