# Embeds

`Embed` objects can be constructed piece by piece much like in `discord.py`.
These helper methods return the embed instance so you can chain calls.

```python
from disagreement import Embed

embed = (
    Embed()
    .set_author(name="Disagreement", url="https://example.com", icon_url="https://cdn.example.com/bot.png")
    .add_field(name="Info", value="Some details")
    .set_footer(text="Made with Disagreement")
    .set_image(url="https://cdn.example.com/image.png")
)
```

Call `to_dict()` to convert the embed back to a payload dictionary before sending:

```python
payload = embed.to_dict()
```
