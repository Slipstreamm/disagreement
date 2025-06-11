from disagreement.models import Embed


def test_embed_helper_methods():
    embed = (
        Embed()
        .set_author(name="name", url="url", icon_url="icon")
        .add_field(name="n", value="v")
        .set_footer(text="footer", icon_url="icon")
        .set_image(url="https://example.com/image.png")
    )

    assert embed.author.name == "name"
    assert embed.author.url == "url"
    assert embed.author.icon_url == "icon"
    assert len(embed.fields) == 1 and embed.fields[0].name == "n"
    assert embed.footer.text == "footer"
    assert embed.image.url == "https://example.com/image.png"
