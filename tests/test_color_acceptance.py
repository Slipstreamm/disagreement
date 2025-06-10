from disagreement.color import Color
from disagreement.models import Embed, Container, Component


def test_color_parse():
    assert Color.parse(0x123456).value == 0x123456
    assert Color.parse("#123456").value == 0x123456
    c = Color(0xABCDEF)
    assert Color.parse(c) is c
    assert Color.parse(None) is None
    assert Color.parse((255, 0, 0)).value == 0xFF0000


def test_embed_color_parsing():
    e = Embed({"color": "#FF0000"})
    assert e.color.value == 0xFF0000
    e = Embed({"color": Color(0x00FF00)})
    assert e.color.value == 0x00FF00
    e = Embed({"color": 0x0000FF})
    assert e.color.value == 0x0000FF


def test_container_accent_color_parsing():
    container = Container(components=[], accent_color="#010203")
    assert container.accent_color.value == 0x010203
    container = Container(components=[], accent_color=Color(0x111111))
    assert container.accent_color.value == 0x111111
    container = Container(components=[], accent_color=0x222222)
    assert container.accent_color.value == 0x222222
