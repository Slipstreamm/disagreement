from disagreement.color import Color


def test_from_rgb():
    color = Color.from_rgb(255, 127, 0)
    assert color.value == 0xFF7F00
    assert color.to_rgb() == (255, 127, 0)


def test_static_colors():
    assert Color.red().value == 0xFF0000
    assert Color.green().value == 0x00FF00
    assert Color.blue().value == 0x0000FF
    assert Color.blurple().value == 0x5865F2
    assert Color.light_blurple().value == 0xE0E3FF
    assert Color.legacy_blurple().value == 0x7289DA
