# Working with Webhooks

The `HTTPClient` includes helper methods for creating, editing and deleting Discord webhooks.

## Create a webhook

```python
from disagreement.http import HTTPClient

http = HTTPClient(token="TOKEN")
payload = {"name": "My Webhook"}
webhook = await http.create_webhook("123", payload)
```

## Edit a webhook

```python
await http.edit_webhook("456", {"name": "Renamed"})
```

## Delete a webhook

```python
await http.delete_webhook("456")
```

The methods now return a `Webhook` object directly:

```python
from disagreement.models import Webhook

print(webhook.id, webhook.name)
```
