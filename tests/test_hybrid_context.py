import asyncio
import pytest

from disagreement.hybrid_context import HybridContext
from disagreement.ext.app_commands.context import AppCommandContext


class DummyCommandCtx:
    def __init__(self):
        self.sent = []

    async def reply(self, *a, **kw):
        self.sent.append(("reply", a, kw))

    async def edit(self, *a, **kw):
        self.sent.append(("edit", a, kw))


class DummyAppCtx(AppCommandContext):
    def __init__(self):
        self.sent = []

    async def send(self, *a, **kw):
        self.sent.append(("send", a, kw))


@pytest.mark.asyncio
async def test_send_routes_based_on_context():
    cctx = DummyCommandCtx()
    actx = DummyAppCtx()
    await HybridContext(cctx).send("hi")
    await HybridContext(actx).send("hi")
    assert cctx.sent[0][0] == "reply"
    assert actx.sent[0][0] == "send"


@pytest.mark.asyncio
async def test_edit_delegation_and_error():
    cctx = DummyCommandCtx()
    hctx = HybridContext(cctx)
    await hctx.edit("m")
    assert cctx.sent[0][0] == "edit"
    with pytest.raises(AttributeError):
        await HybridContext(DummyAppCtx()).edit("m")
