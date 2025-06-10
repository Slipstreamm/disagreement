from disagreement.models import Member


def _make_member(member_id: str, username: str, nick: str | None):
    data = {
        "user": {"id": member_id, "username": username, "discriminator": "0001"},
        "joined_at": "t",
        "roles": [],
    }
    if nick is not None:
        data["nick"] = nick
    return Member(data, client_instance=None)


def test_display_name_prefers_nick():
    member = _make_member("1", "u", "nickname")
    assert member.display_name == "nickname"


def test_display_name_falls_back_to_username():
    member = _make_member("2", "u2", None)
    assert member.display_name == "u2"
