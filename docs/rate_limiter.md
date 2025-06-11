# Rate Limiter

The HTTP client uses an asynchronous `RateLimiter` to respect Discord's per-route and global rate limits. Each request acquires a bucket associated with the route. The limiter delays requests when the bucket is exhausted and handles global rate limits automatically.

```python
from disagreement.rate_limiter import RateLimiter

rl = RateLimiter()
bucket = await rl.acquire("GET:/channels/1")
# perform request
rl.release("GET:/channels/1", response_headers)
```

`handle_rate_limit(route, retry_after, is_global)` can be used when the API returns a rate limit response.
