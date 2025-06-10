# Voice Features

Disagreement includes experimental support for connecting to voice channels. You can join a voice channel and play audio using an FFmpeg subprocess.

```python
voice = await client.join_voice(guild_id, channel_id)
await voice.play_file("welcome.mp3")
await voice.close()
```

Voice support is optional and may require additional system dependencies such as FFmpeg.

## Next Steps

- [Components](using_components.md)
- [Slash Commands](slash_commands.md)
- [Caching](caching.md)

