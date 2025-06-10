"""Audio source abstractions for the voice client."""

from __future__ import annotations

import asyncio
import contextlib
import io
from typing import Optional, Union


class AudioSource:
    """Abstract base class for audio sources."""

    async def read(self) -> bytes:
        """Read the next chunk of PCM audio.

        Subclasses must implement this and return raw PCM data
        at 48kHz stereo (3840 byte chunks).
        """

        raise NotImplementedError

    async def close(self) -> None:
        """Cleanup the source when playback ends."""

        return None


class FFmpegAudioSource(AudioSource):
    """Decode audio using FFmpeg.

    Parameters
    ----------
    source:
        A filename, URL, or file-like object to read from.
    """

    def __init__(self, source: Union[str, io.BufferedIOBase]):
        self.source = source
        self.process: Optional[asyncio.subprocess.Process] = None
        self._feeder: Optional[asyncio.Task] = None

    async def _spawn(self) -> None:
        if isinstance(self.source, str):
            args = [
                "ffmpeg",
                "-i",
                self.source,
                "-f",
                "s16le",
                "-ar",
                "48000",
                "-ac",
                "2",
                "pipe:1",
            ]
            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        else:
            args = [
                "ffmpeg",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-ar",
                "48000",
                "-ac",
                "2",
                "pipe:1",
            ]
            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            assert self.process.stdin is not None
            self._feeder = asyncio.create_task(self._feed())

    async def _feed(self) -> None:
        assert isinstance(self.source, io.BufferedIOBase)
        assert self.process is not None
        assert self.process.stdin is not None
        while True:
            data = await asyncio.to_thread(self.source.read, 4096)
            if not data:
                break
            self.process.stdin.write(data)
            await self.process.stdin.drain()
        self.process.stdin.close()

    async def read(self) -> bytes:
        if self.process is None:
            await self._spawn()
        assert self.process is not None
        assert self.process.stdout is not None
        data = await self.process.stdout.read(3840)
        if not data:
            await self.close()
        return data

    async def close(self) -> None:
        if self._feeder:
            self._feeder.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._feeder
        if self.process:
            await self.process.wait()
            self.process = None
        if isinstance(self.source, io.IOBase):
            with contextlib.suppress(Exception):
                self.source.close()
