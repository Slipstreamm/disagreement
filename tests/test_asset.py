from disagreement.models import User
from disagreement.asset import Asset


def test_user_avatar_returns_asset():
    user = User({"id": "1", "username": "u", "discriminator": "0001", "avatar": "abc"})
    avatar = user.avatar
    assert isinstance(avatar, Asset)
    assert avatar.url == "https://cdn.discordapp.com/avatars/1/abc.png"


def test_user_avatar_none():
    user = User({"id": "1", "username": "u", "discriminator": "0001"})
    assert user.avatar is None
