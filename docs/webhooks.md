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

## Create a Webhook from a URL

You can construct a `Webhook` object from an existing webhook URL without any API calls:

```python
from disagreement.models import Webhook

webhook = Webhook.from_url("https://discord.com/api/webhooks/123/token")
print(webhook.id, webhook.token)
```

## Send a message through a Webhook

Once you have a `Webhook` instance bound to a :class:`Client`, you can send messages using it:

```python
webhook = await client.create_webhook("123", {"name": "Bot Webhook"})
await webhook.send(content="Hello from my webhook!", username="Bot")
```
