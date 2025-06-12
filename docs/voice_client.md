# VoiceClient

`VoiceClient` provides a minimal interface to Discord's voice gateway. It handles the WebSocket handshake and lets you stream audio over UDP.

## Basic Usage

```python
import asyncio
import os
import disagreement

async def main():
    async with disagreement.VoiceClient(
        os.environ["DISCORD_VOICE_ENDPOINT"],
        os.environ["DISCORD_SESSION_ID"],
        os.environ["DISCORD_VOICE_TOKEN"],
        int(os.environ["DISCORD_GUILD_ID"]),
        int(os.environ["DISCORD_USER_ID"]),
    ) as vc:
        await vc.send_audio_frame(b"...")

asyncio.run(main())
```

After connecting you can send raw Opus frames:

```python
await vc.send_audio_frame(opus_bytes)
```

Or stream audio using an :class:`AudioSource`:

```python
from disagreement import FFmpegAudioSource

source = FFmpegAudioSource("welcome.mp3")
await vc.play(source)
```

You can switch sources while connected:

```python
await vc.play(FFmpegAudioSource("other.mp3"))
```

The connection will be closed automatically when leaving the `async with` block.

## Fetching Available Voice Regions

Use :meth:`Client.fetch_voice_regions` to list the voice regions that Discord
currently offers. The method returns a list of :class:`VoiceRegion` values.

```python
regions = await client.fetch_voice_regions()
for region in regions:
    print(region.value)
```
