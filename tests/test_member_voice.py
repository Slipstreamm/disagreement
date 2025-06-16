from disagreement.models import Member, VoiceState


def test_member_voice_dataclass():
    data = {
        "user": {"id": "1", "username": "u", "discriminator": "0001"},
        "joined_at": "t",
        "roles": [],
        "voice_state": {
            "guild_id": "g",
            "channel_id": "c",
            "user_id": "1",
            "session_id": "s",
            "deaf": False,
            "mute": True,
            "self_deaf": False,
            "self_mute": False,
            "self_video": False,
            "suppress": False,
        },
    }
    member = Member(data, client_instance=None)
    voice = member.voice
    assert isinstance(voice, VoiceState)
    assert voice.channel_id == "c"
    assert voice.mute is True


def test_member_voice_none():
    data = {
        "user": {"id": "2", "username": "u2", "discriminator": "0001"},
        "joined_at": "t",
        "roles": [],
    }
    member = Member(data, client_instance=None)
    assert member.voice is None
