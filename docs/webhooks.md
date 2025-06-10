# Working with Webhooks

The `HTTPClient` includes helper methods for creating, editing and deleting Discord webhooks.

## Create a webhook

```python
from disagreement.http import HTTPClient

http = HTTPClient(token="TOKEN")
payload = {"name": "My Webhook"}
webhook_data = await http.create_webhook("123", payload)
```

## Edit a webhook

```python
await http.edit_webhook("456", {"name": "Renamed"})
```

## Delete a webhook

```python
await http.delete_webhook("456")
```

The methods return the raw webhook JSON. You can construct a `Webhook` model if needed:

```python
from disagreement.models import Webhook

webhook = Webhook(webhook_data)
print(webhook.id, webhook.name)
```
