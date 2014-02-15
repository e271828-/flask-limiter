import unittest
import time

import hiro
import redis
from flask.ext.limiter.strategies import FixedWindowRateLimiter

from flask.ext.limiter.util import get_dependency, storage_from_string
from flask.ext.limiter.errors import ConfigurationError
from flask.ext.limiter.limits import PER_MINUTE, PER_SECOND
from flask.ext.limiter.storage import MemoryStorage, RedisStorage, MemcachedStorage


class StorageTests(unittest.TestCase):
    def setUp(self):
        redis.Redis().flushall()

    def test_storage_string(self):
        self.assertTrue(isinstance(storage_from_string("memory://"), MemoryStorage))
        self.assertTrue(isinstance(storage_from_string("redis://localhost:6379"), RedisStorage))
        if get_dependency("memcache"):
            self.assertTrue(isinstance(storage_from_string("memcached://localhost:11211"), MemcachedStorage))
        self.assertRaises(ConfigurationError, storage_from_string, "blah://")

    def test_in_memory(self):
        with hiro.Timeline().freeze() as timeline:
            storage = MemoryStorage()
            limiter = FixedWindowRateLimiter(storage)
            per_min = PER_MINUTE(10)
            for i in range(0,10):
                self.assertTrue(limiter.hit(per_min))
            self.assertFalse(limiter.hit(per_min))
            timeline.forward(61)
            self.assertTrue(limiter.hit(per_min))

    def test_redis(self):
        storage = RedisStorage("redis://localhost:6379")
        limiter = FixedWindowRateLimiter(storage)
        per_min = PER_SECOND(10)
        start = time.time()
        count = 0
        while time.time() - start < 0.5 and count < 10:
            self.assertTrue(limiter.hit(per_min))
            count += 1
        self.assertFalse(limiter.hit(per_min))
        while time.time() - start < 1:
            time.sleep(0.1)
        self.assertTrue(limiter.hit(per_min))

    def test_memcached(self):
        storage = MemcachedStorage("localhost", 11211)
        limiter = FixedWindowRateLimiter(storage)
        per_min = PER_SECOND(10)
        start = time.time()
        count = 0
        while time.time() - start < 0.5 and count < 10:
            self.assertTrue(limiter.hit(per_min))
            count += 1
        self.assertFalse(limiter.hit(per_min))
        while time.time() - start < 1:
            time.sleep(0.1)
        self.assertTrue(limiter.hit(per_min))
