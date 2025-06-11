import types
from disagreement.models import Message


def make_message(content: str) -> Message:
    data = {
        "id": "1",
        "channel_id": "c",
        "author": {"id": "2", "username": "u", "discriminator": "0001"},
        "content": content,
        "timestamp": "t",
    }
    return Message(data, client_instance=types.SimpleNamespace())


def test_clean_content_removes_mentions():
    msg = make_message("Hello <@123> <#456> <@&789> world")
    assert msg.clean_content == "Hello world"


def test_clean_content_no_mentions():
    msg = make_message("Just text")
    assert msg.clean_content == "Just text"
