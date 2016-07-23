import logging
import requests
import sys
import time
import unittest

import service


class ServiceTest(unittest.TestCase):
    """Abstract class to instatiate docker containers as test fixtures."""

    def run(self, result=None):
        if not getattr(self, 'SERVICE', None):
            raise TypeError('A ServiceTest must declare SERVICE')

        ports = getattr(self, 'PORTS', None)
        if not ports:
            ports = getattr(self, 'PORT', None)
        if not ports:
            raise TypeError('A ServiceTest must declare either PORTS or PORT')

        extras = {}

        def _add_extra(key):
            value = getattr(self, key, None)
            if value is not None:
                extras[key.lower()] = value

        _add_extra('VOLUMES')
        _add_extra('ENVIRONMENT')

        with service.Container(self.SERVICE, ports, extras) as port_map:
            self.port_map = port_map

            # special case - when only one port was requested
            if isinstance(port_map, tuple):
                # N.B., this is just a shortcut, we don't remove self.port_map
                self.host, self.port = port_map

            super(ServiceTest, self).run(result)


class HttpServiceTest(unittest.TestCase):
    """Abstract class to instantiate containers providing HTTP services."""

    def run(self, result=None):
        if not getattr(self, 'SERVICE', None):
            raise TypeError('A HttpServiceTest must declare SERVICE')

        port = getattr(self, 'PORT', None)
        if not port:
            raise TypeError('A HttpServiceTest must declare PORT')

        extras = {}

        def _add_extra(key):
            value = getattr(self, key, None)
            if value is not None:
                extras[key.lower()] = value

        _add_extra('VOLUMES')
        _add_extra('ENVIRONMENT')

        with service.Container(self.SERVICE, port, extras) as port_map:
            self.host, self.port = port_map
            self.base_url = 'http://{}:{}'.format(self.host, self.port)

            with requests.Session() as session:
                self.http_session = session
                self._connect()

                super(HttpServiceTest, self).run(result)

    def build_url(self, endpoint):
        separator = '' if endpoint.startswith('/') else '/'
        return self.base_url + separator + endpoint

    def get(self, endpoint):
        url = self.build_url(endpoint)
        response = self.http_session.get(url)
        response.raise_for_status()
        return response

    def get_json(self, endpoint):
        return self.get(endpoint).json()

    def post(self, endpoint, data=None, json=None):
        url = self.build_url(endpoint)
        response = self.http_session.post(url, data=data, json=json)
        response.raise_for_status()
        return response

    def _connect(self, max_tries=10, min_interval=0.1, max_interval=10):
        interval = min_interval
        for index in range(1, max_tries + 1):
            try:
                self.http_session.options(self.build_url('/'))
            except requests.ConnectionError:
                logging.info('Failed to connect (attempt #{})'.format(index))
                if index < max_tries:
                    time.sleep(interval)
                    interval = min(max_interval, 2 * interval)
