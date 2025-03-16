# dvrd_ratelimit

This package provides a simple but robust thread-safe rate limiter. The limiter can automatically delay calls when the
rate limit is exceeded, return `False` or raise an exception.

## Limiter

Rate limits are applied using `Limiter` objects. `Limiter` object should be defined globally and shared between threads.
A `Limiter` takes just one argument: `rate` (see below).

Rate limits are applied based on an identity. This allows limiters to be used for multiple resources, like functions
with similar rate limits.

```python
from dvrd_ratelimit import Limiter, Rate, Duration

# Create a limiter that allows 10 requests per minute
limiter = Limiter(Rate(10, Duration.MINUTE))

# 'id1' and 'id2' are given as identity parameter. This means the rates for both identities will have one entry (call). 
# They do not affect each other's rate.
limiter.ratelimit('id1')
limiter.ratelimit('id2')
```

### Exceeding rate limit
When a rate limit is exceeded the limiter will delay further calls until 
