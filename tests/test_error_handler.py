import asyncio
import logging
from types import SimpleNamespace

import pytest

from disagreement.error_handler import setup_global_error_handler


@pytest.mark.asyncio
async def test_handle_exception_logs_error(monkeypatch, capsys):
    loop = asyncio.new_event_loop()
    records = []

    def fake_error(msg, *args, **kwargs):
        records.append(msg % args if args else msg)

    monkeypatch.setattr(logging, "error", fake_error)
    setup_global_error_handler(loop)
    exc = RuntimeError("boom")
    loop.call_exception_handler({"exception": exc})
    assert any("Unhandled exception" in r for r in records)
    loop.close()


@pytest.mark.asyncio
async def test_handle_message_logs_error(monkeypatch):
    loop = asyncio.new_event_loop()
    logged = {}

    def fake_error(msg, *args, **kwargs):
        logged["msg"] = msg % args if args else msg

    monkeypatch.setattr(logging, "error", fake_error)
    setup_global_error_handler(loop)
    loop.call_exception_handler({"message": "oops"})
    assert "oops" in logged["msg"]
    loop.close()
