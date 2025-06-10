# Gateway Connection and Reconnection

`GatewayClient` manages the library's WebSocket connection. When the connection drops unexpectedly, it will now automatically attempt to reconnect using an exponential backoff strategy with jitter.

The default behaviour tries up to five reconnect attempts, doubling the delay each time up to a configurable maximum. A small random jitter is added to spread out reconnect attempts when multiple clients restart at once.

You can control the maximum number of retries and the backoff cap when constructing `Client`.
These options are forwarded to `GatewayClient` as `max_retries` and `max_backoff`:

```python
bot = Client(
    token="your-token",
    gateway_max_retries=10,
    gateway_max_backoff=120.0,
)
```

These values are passed to `GatewayClient` and applied whenever the connection needs to be re-established.

## Gateway Intents

`GatewayIntent` values control which events your bot receives from the Gateway. Use
`GatewayIntent.none()` to opt out of all events entirely. It returns `0`, which
represents a bitmask with no intents enabled.
