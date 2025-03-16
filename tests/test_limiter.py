import time
import unittest

from dvrd_ratelimit import Limiter, Rate, Duration
from dvrd_ratelimit.limiter import RateLimitExceeded


class TestLimiter(unittest.TestCase):
    def test_limiter_passes(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            self.assertTrue(limiter.ratelimit('test'))

    def test_limiter_raises(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))
        calls_passed = 0

        def runner():
            nonlocal calls_passed, limiter
            # Should raise at the eleventh call
            for _ in range(11):
                self.assertTrue(limiter.ratelimit('test', delay=False))
                calls_passed += 1

        self.assertRaises(RateLimitExceeded, runner)
        self.assertEqual(10, calls_passed)

    def test_max_delay_raises(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))
        # Should run fine
        for _ in range(10):
            self.assertTrue(limiter.ratelimit('test', max_delay=1))
        # Eleventh call, should raise
        self.assertRaises(RateLimitExceeded, limiter.ratelimit, 'test', max_delay=1)

    def test_decorator_passes(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))

        @limiter('test')
        def runner():
            pass

        # Should run without issues
        for _ in range(10):
            runner()

    def test_decorator_raises(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))
        calls_passed = 0

        @limiter('test', delay=False)
        def runner():
            pass

        def runner2():
            nonlocal calls_passed
            # Should fail at eleventh call
            for _ in range(11):
                runner()
                calls_passed += 1

        self.assertRaises(RateLimitExceeded, runner2)
        self.assertEqual(10, calls_passed)

    def test_delay(self):
        """
        Test the limiter waits 5 seconds before executing the eleventh call
        """
        limiter = Limiter(Rate(limit=10, duration=5))
        start = time.monotonic()
        for _ in range(10):
            self.assertTrue(limiter.ratelimit('test'))
        end = time.monotonic()
        self.assertAlmostEqual(end, start, 1)

        # Eleventh cal
        self.assertTrue(limiter.ratelimit('test'))
        end = time.monotonic()
        self.assertAlmostEqual(end - start, 5, 0)

    def test_bool_passes(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            # Specifying return_bool is not needed since ratelimit always returns True when successful
            self.assertTrue(limiter.ratelimit('test'))

    def test_bool_fails(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            # Specifying return_bool is not needed since ratelimit always returns True when successful
            self.assertTrue(limiter.ratelimit('test'))

        # Eleventh call, should return False
        self.assertFalse(limiter.ratelimit('test', return_bool=True, delay=False))

    def test_bool_max_delay_fails(self):
        limiter = Limiter(Rate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            # Specifying return_bool is not needed since ratelimit always returns True when successful
            self.assertTrue(limiter.ratelimit('test'))

        # Eleventh call, should return False
        self.assertFalse(limiter.ratelimit('test', return_bool=True, max_delay=1))

    def test_limit_zero(self):
        limiter = Limiter(Rate(limit=0, duration=Duration.MINUTE))
        self.assertRaises(RateLimitExceeded, limiter.ratelimit, 'test', delay=False)
