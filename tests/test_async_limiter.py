import time
from unittest import IsolatedAsyncioTestCase

from dvrd_ratelimit import AsyncLimiter, AsyncRate, Duration, Rate
from dvrd_ratelimit.limiter import RateLimitExceeded


class MyTestCase(IsolatedAsyncioTestCase):
    async def test_limiter_passes(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            self.assertTrue(await limiter.ratelimit('test'))

        # Limiter can also be initialized using a "regular" Rate, which gets converted to an AsyncRate automatically
        limiter = AsyncLimiter(Rate(limit=10, duration=Duration.MINUTE))
        self.assertIsInstance(limiter._rate, AsyncRate)
        # Should run without issues
        for _ in range(10):
            self.assertTrue(await limiter.ratelimit('test'))

    async def test_limiter_raises(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))
        calls_passed = 0

        async def runner():
            nonlocal calls_passed, limiter
            # Should raise at the eleventh call
            for _ in range(11):
                self.assertTrue(await limiter.ratelimit('test', delay=False))
                calls_passed += 1

        with self.assertRaises(RateLimitExceeded):
            await runner()
        self.assertEqual(10, calls_passed)

    async def test_max_delay_raises(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))
        # Should run fine
        for _ in range(10):
            self.assertTrue(await limiter.ratelimit('test', max_delay=1))
        # Eleventh call, should raise
        with self.assertRaises(RateLimitExceeded):
            await limiter.ratelimit('test', max_delay=1)

    async def test_decorator_passes(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))

        @limiter('test')
        async def runner():
            pass

        # Should run without issues
        for _ in range(10):
            await runner()

    async def test_decorator_raises(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))
        calls_passed = 0

        @limiter('test', delay=False)
        async def runner():
            pass

        async def runner2():
            nonlocal calls_passed
            # Should fail at eleventh call
            for _ in range(11):
                await runner()
                calls_passed += 1

        with self.assertRaises(RateLimitExceeded):
            await runner2()
        self.assertEqual(10, calls_passed)

    async def test_delay(self):
        """
        Test the limiter waits 5 seconds before executing the eleventh call
        """
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=5))
        start = time.monotonic()
        for _ in range(10):
            self.assertTrue(await limiter.ratelimit('test'))
        end = time.monotonic()
        self.assertAlmostEqual(end, start, 1)

        # Eleventh cal
        self.assertTrue(await limiter.ratelimit('test'))
        end = time.monotonic()
        self.assertAlmostEqual(end - start, 5, 0)

    async def test_bool_passes(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            # Specifying return_bool is not needed since ratelimit always returns True when successful
            self.assertTrue(await limiter.ratelimit('test'))

    async def test_bool_fails(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            # Specifying return_bool is not needed since ratelimit always returns True when successful
            self.assertTrue(await limiter.ratelimit('test'))

        # Eleventh call, should return False
        self.assertFalse(await limiter.ratelimit('test', return_bool=True, delay=False))

    async def test_bool_max_delay_fails(self):
        limiter = AsyncLimiter(AsyncRate(limit=10, duration=Duration.MINUTE))
        # Should run without issues
        for _ in range(10):
            # Specifying return_bool is not needed since ratelimit always returns True when successful
            self.assertTrue(await limiter.ratelimit('test'))

        # Eleventh call, should return False
        self.assertFalse(await limiter.ratelimit('test', return_bool=True, max_delay=1))

    async def test_limit_zero(self):
        limiter = AsyncLimiter(AsyncRate(limit=0, duration=Duration.MINUTE))
        with self.assertRaises(RateLimitExceeded):
            await limiter.ratelimit('test', delay=False)
