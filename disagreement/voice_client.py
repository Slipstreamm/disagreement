"""Voice gateway and UDP audio client."""

from __future__ import annotations

import asyncio
import contextlib
import socket
import threading
from array import array


def _apply_volume(data: bytes, volume: float) -> bytes:
    samples = array("h")
    samples.frombytes(data)
    for i, sample in enumerate(samples):
        scaled = int(sample * volume)
        if scaled > 32767:
            scaled = 32767
        elif scaled < -32768:
            scaled = -32768
        samples[i] = scaled
    return samples.tobytes()


from typing import TYPE_CHECKING, Optional, Sequence

import aiohttp

# The following import is correct, but may be flagged by Pylance if the virtual
# environment is not configured correctly.
from nacl.secret import SecretBox

from .audio import AudioSink, AudioSource, FFmpegAudioSource
from .models import User

if TYPE_CHECKING:
    from .client import Client


class VoiceClient:
    """Handles the Discord voice WebSocket connection and UDP streaming."""

    def __init__(
        self,
        client: Client,
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
        self.client = client
        self.endpoint = endpoint
        self.session_id = session_id
        self.token = token
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = ws
        self._udp = udp
        self._session: Optional[aiohttp.ClientSession] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._udp_receive_thread: Optional[threading.Thread] = None
        self._heartbeat_interval: Optional[float] = None
        try:
            self._loop = loop or asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        self.verbose = verbose
        self.ssrc: Optional[int] = None
        self.secret_key: Optional[Sequence[int]] = None
        self._server_ip: Optional[str] = None
        self._server_port: Optional[int] = None
        self._current_source: Optional[AudioSource] = None
        self._play_task: Optional[asyncio.Task] = None
        self._sink: Optional[AudioSink] = None
        self._ssrc_map: dict[int, int] = {}
        self._ssrc_lock = threading.Lock()

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

    async def _receive_loop(self) -> None:
        assert self._ws is not None
        while True:
            try:
                msg = await self._ws.receive_json()
                op = msg.get("op")
                data = msg.get("d")
                if op == 5:  # Speaking
                    user_id = int(data["user_id"])
                    ssrc = data["ssrc"]
                    with self._ssrc_lock:
                        self._ssrc_map[ssrc] = user_id
            except (asyncio.CancelledError, aiohttp.ClientError):
                break

    def _udp_receive_loop(self) -> None:
        assert self._udp is not None
        assert self.secret_key is not None
        box = SecretBox(bytes(self.secret_key))
        while True:
            try:
                packet = self._udp.recv(4096)
                if len(packet) < 12:
                    continue

                ssrc = int.from_bytes(packet[8:12], "big")
                with self._ssrc_lock:
                    if ssrc not in self._ssrc_map:
                        continue
                    user_id = self._ssrc_map[ssrc]
                user = self.client._users.get(str(user_id))
                if not user:
                    continue

                decrypted = box.decrypt(packet[12:])
                if self._sink:
                    self._sink.write(user, decrypted)
            except (socket.error, asyncio.CancelledError):
                break
            except Exception as e:
                if self.verbose:
                    print(f"Error in UDP receive loop: {e}")

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
                volume = getattr(self._current_source, "volume", 1.0)
                if volume != 1.0:
                    data = _apply_volume(data, volume)
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

    def listen(self, sink: AudioSink) -> None:
        """Start listening to voice and routing to a sink."""
        if not isinstance(sink, AudioSink):
            raise TypeError("sink must be an AudioSink instance")

        self._sink = sink
        if not self._udp_receive_thread:
            self._udp_receive_thread = threading.Thread(
                target=self._udp_receive_loop, daemon=True
            )
            self._udp_receive_thread.start()

    async def close(self) -> None:
        await self.stop()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task
        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        if self._udp:
            self._udp.close()
        if self._udp_receive_thread:
            self._udp_receive_thread.join(timeout=1)
        if self._sink:
            self._sink.close()

    async def __aenter__(self) -> "VoiceClient":
        """Enter the context manager by connecting to the voice gateway."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc: Optional[BaseException],
        tb: Optional[BaseException],
    ) -> bool:
        """Exit the context manager and close the connection."""
        await self.close()
        return False
