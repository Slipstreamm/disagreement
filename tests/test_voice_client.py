import asyncio
import io
from array import array
import pytest

from disagreement.audio import AudioSource, FFmpegAudioSource

from disagreement.voice_client import VoiceClient
from disagreement.client import Client


class DummyVoiceClient(Client):
    def __init__(self):
        super().__init__(token="test")


class DummyWebSocket:
    def __init__(self, messages):
        self.sent = []
        self._queue = asyncio.Queue()
        for m in messages:
            self._queue.put_nowait(m)

    async def send_json(self, data):
        self.sent.append(data)

    async def receive_json(self):
        return await self._queue.get()

    async def close(self):
        pass


class DummyUDP:
    def __init__(self):
        self.connected = None
        self.sent = []

    def connect(self, address):
        self.connected = address

    def send(self, data):
        self.sent.append(data)

    def getsockname(self):
        return ("127.0.0.1", 12345)

    def close(self):
        pass


class DummySource(AudioSource):
    def __init__(self, chunks):
        self.chunks = list(chunks)

    async def read(self) -> bytes:
        if self.chunks:
            return self.chunks.pop(0)
        return b""


@pytest.mark.asyncio
async def test_voice_client_handshake():
    hello = {"d": {"heartbeat_interval": 50}}
    ready = {"d": {"ssrc": 1, "ip": "127.0.0.1", "port": 4000}}
    session_desc = {"d": {"secret_key": [1, 2, 3]}}
    ws = DummyWebSocket([hello, ready, session_desc])
    udp = DummyUDP()

    vc = VoiceClient(
        client=DummyVoiceClient(),
        endpoint="ws://localhost",
        session_id="sess",
        token="tok",
        guild_id=1,
        user_id=2,
        ws=ws,
        udp=udp,
    )
    await vc.connect()
    vc._heartbeat_task.cancel()

    assert ws.sent[0]["op"] == 0
    assert ws.sent[1]["op"] == 1
    assert udp.connected == ("127.0.0.1", 4000)
    assert vc.secret_key == [1, 2, 3]


@pytest.mark.asyncio
async def test_send_audio_frame():
    ws = DummyWebSocket(
        [
            {"d": {"heartbeat_interval": 50}},
            {"d": {"ssrc": 1, "ip": "127.0.0.1", "port": 4000}},
            {"d": {"secret_key": []}},
        ]
    )
    udp = DummyUDP()
    vc = VoiceClient(
        client=DummyVoiceClient(),
        endpoint="ws://localhost",
        session_id="sess",
        token="tok",
        guild_id=1,
        user_id=2,
        ws=ws,
        udp=udp,
    )
    await vc.connect()
    vc._heartbeat_task.cancel()

    await vc.send_audio_frame(b"abc")
    assert udp.sent[-1] == b"abc"


@pytest.mark.asyncio
async def test_play_and_switch_sources():
    ws = DummyWebSocket(
        [
            {"d": {"heartbeat_interval": 50}},
            {"d": {"ssrc": 1, "ip": "127.0.0.1", "port": 4000}},
            {"d": {"secret_key": []}},
        ]
    )
    udp = DummyUDP()
    vc = VoiceClient(
        client=DummyVoiceClient(),
        endpoint="ws://localhost",
        session_id="sess",
        token="tok",
        guild_id=1,
        user_id=2,
        ws=ws,
        udp=udp,
    )
    await vc.connect()
    vc._heartbeat_task.cancel()

    await vc.play(DummySource([b"a", b"b"]))
    await vc.play(DummySource([b"c"]))

    assert udp.sent == [b"a", b"b", b"c"]


@pytest.mark.asyncio
async def test_ffmpeg_source_custom_options(monkeypatch):
    captured = {}

    class DummyProcess:
        def __init__(self):
            self.stdout = io.BytesIO(b"")

        async def wait(self):
            return 0

    async def fake_exec(*args, **kwargs):
        captured["args"] = args
        return DummyProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    src = FFmpegAudioSource(
        "file.mp3", before_options="-reconnect 1", options="-vn", volume=0.5
    )

    await src._spawn()

    cmd = captured["args"]
    assert "-reconnect" in cmd
    assert "-vn" in cmd
    assert src.volume == 0.5


@pytest.mark.asyncio
async def test_voice_client_volume_scaling(monkeypatch):
    ws = DummyWebSocket(
        [
            {"d": {"heartbeat_interval": 50}},
            {"d": {"ssrc": 1, "ip": "127.0.0.1", "port": 4000}},
            {"d": {"secret_key": []}},
        ]
    )
    udp = DummyUDP()
    vc = VoiceClient(
        client=DummyVoiceClient(),
        endpoint="ws://localhost",
        session_id="sess",
        token="tok",
        guild_id=1,
        user_id=2,
        ws=ws,
        udp=udp,
    )
    await vc.connect()
    vc._heartbeat_task.cancel()

    chunk = b"\x10\x00\x10\x00"
    src = DummySource([chunk])
    src.volume = 0.5

    await vc.play(src)

    samples = array("h")
    samples.frombytes(chunk)
    samples[0] = int(samples[0] * 0.5)
    samples[1] = int(samples[1] * 0.5)
    expected = samples.tobytes()
    assert udp.sent == [expected]
