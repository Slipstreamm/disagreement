import pytest  # pylint: disable=import-error

from disagreement.i18n import set_translations, translate
from disagreement.ext.app_commands.commands import SlashCommand


async def dummy(ctx):
    pass


def test_translate_lookup():
    set_translations("xx", {"hello": "bonjour"})
    assert translate("hello", "xx") == "bonjour"
    assert translate("missing", "xx") == "missing"


def test_appcommand_uses_locale():
    set_translations("xx", {"cmd": "c", "desc": "d"})
    cmd = SlashCommand(dummy, name="cmd", description="desc", locale="xx")
    assert cmd.name == "c"
    assert cmd.description == "d"
