import pytest

from disagreement.client import Client


def _add_message(client: Client, message_id: str) -> None:
    data = {
        "id": message_id,
        "channel_id": "c",
        "author": {"id": "u", "username": "u", "discriminator": "0001"},
        "content": "hi",
        "timestamp": "t",
    }
    client.parse_message(data)


def test_client_message_cache_size():
    client = Client(token="t", message_cache_maxlen=1)
    _add_message(client, "1")
    assert client._messages.get("1").id == "1"
    _add_message(client, "2")
    assert client._messages.get("1") is None
    assert client._messages.get("2").id == "2"
