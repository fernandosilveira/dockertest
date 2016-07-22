"""Example of a service test.

This test uses ServiceTest to instantiate redis containers and
send commands to it.
"""

import redis

import servicetest


class RedisTest(servicetest.ServiceTest):
    SERVICE = 'redis'
    PORT = 6379

    def setUp(self):
        self.redis = redis.StrictRedis(host=self.host, port=self.port,
                                       decode_responses=True)

    def test_when_key_is_set_value_can_be_retrieved(self):
        self.redis.set('foo', 'bar')
        value = self.redis.get('foo')
        self.assertEqual(value, 'bar')
