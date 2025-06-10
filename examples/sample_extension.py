from disagreement.ext import tasks


@tasks.loop(seconds=2.0)
async def ticker() -> None:
    print("Extension tick")


def setup() -> None:
    print("sample_extension setup")
    ticker.start()


def teardown() -> None:
    print("sample_extension teardown")
    ticker.stop()
