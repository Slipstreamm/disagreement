# HTTP Client Options

Disagreement uses `aiohttp` for all HTTP requests. Additional options for the
underlying `aiohttp.ClientSession` can be provided when constructing a
`Client` or an `HTTPClient` directly.

```python
import aiohttp
from disagreement import Client

connector = aiohttp.TCPConnector(limit=50)
client = Client(
    token="YOUR_TOKEN",
    http_options={"proxy": "http://localhost:8080", "connector": connector},
)
```

These options are passed through to `aiohttp.ClientSession` when the session is
created. You can set a proxy URL, provide a custom connector, or supply any
other supported session argument.
