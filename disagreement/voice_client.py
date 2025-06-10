# disagreement/voice_client.py
"""Voice gateway and UDP audio client."""

from __future__ import annotations

import asyncio
import contextlib
import socket
from typing import Optional, Sequence

import aiohttp

from .audio import AudioSource, FFmpegAudioSource


class VoiceClient:
    """Handles the Discord voice WebSocket connection and UDP streaming."""

    def __init__(
        self,
        endpoint: str,
        session_id: str,
        token: str,
        guild_id: int,
        user_id: int,
        *,
        ws=None,
        udp: Optional[socket.socket] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        verbose: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.session_id = session_id
        self.token = token
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = ws
        self._udp = udp
        self._session: Optional[aiohttp.ClientSession] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval: Optional[float] = None
        self._loop = loop or asyncio.get_event_loop()
        self.verbose = verbose
        self.ssrc: Optional[int] = None
        self.secret_key: Optional[Sequence[int]] = None
        self._server_ip: Optional[str] = None
        self._server_port: Optional[int] = None
        self._current_source: Optional[AudioSource] = None
        self._play_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        if self._ws is None:
            self._session = aiohttp.ClientSession()
            self._ws = await self._session.ws_connect(self.endpoint)

        hello = await self._ws.receive_json()
        self._heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000
        self._heartbeat_task = self._loop.create_task(self._heartbeat())

        await self._ws.send_json(
            {
                "op": 0,
                "d": {
                    "server_id": self.guild_id,
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "token": self.token,
                },
            }
        )

        ready = await self._ws.receive_json()
        data = ready["d"]
        self.ssrc = data["ssrc"]
        self._server_ip = data["ip"]
        self._server_port = data["port"]

        if self._udp is None:
            self._udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp.connect((self._server_ip, self._server_port))

        await self._ws.send_json(
            {
                "op": 1,
                "d": {
                    "protocol": "udp",
                    "data": {
                        "address": self._udp.getsockname()[0],
                        "port": self._udp.getsockname()[1],
                        "mode": "xsalsa20_poly1305",
                    },
                },
            }
        )

        session_desc = await self._ws.receive_json()
        self.secret_key = session_desc["d"].get("secret_key")

    async def _heartbeat(self) -> None:
        assert self._ws is not None
        assert self._heartbeat_interval is not None
        try:
            while True:
                await self._ws.send_json({"op": 3, "d": int(self._loop.time() * 1000)})
                await asyncio.sleep(self._heartbeat_interval)
        except asyncio.CancelledError:
            pass

    async def send_audio_frame(self, frame: bytes) -> None:
        if not self._udp:
            raise RuntimeError("UDP socket not initialised")
        self._udp.send(frame)

    async def _play_loop(self) -> None:
        assert self._current_source is not None
        try:
            while True:
                data = await self._current_source.read()
                if not data:
                    break
                await self.send_audio_frame(data)
        finally:
            await self._current_source.close()
            self._current_source = None
            self._play_task = None

    async def stop(self) -> None:
        if self._play_task:
            self._play_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._play_task
            self._play_task = None
        if self._current_source:
            await self._current_source.close()
            self._current_source = None

    async def play(self, source: AudioSource, *, wait: bool = True) -> None:
        """|coro| Play an :class:`AudioSource` on the voice connection."""

        await self.stop()
        self._current_source = source
        self._play_task = self._loop.create_task(self._play_loop())
        if wait:
            await self._play_task

    async def play_file(self, filename: str, *, wait: bool = True) -> None:
        """|coro| Stream an audio file or URL using FFmpeg."""

        await self.play(FFmpegAudioSource(filename), wait=wait)

    async def close(self) -> None:
        await self.stop()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        if self._udp:
            self._udp.close()
