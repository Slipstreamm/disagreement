from disagreement.utils import Paginator


def test_paginator_single_page():
    p = Paginator(limit=10)
    p.add_line("hi")
    p.add_line("there")
    assert p.pages == ["hi\nthere"]


def test_paginator_splits_pages():
    p = Paginator(limit=10)
    p.add_line("12345")
    p.add_line("67890")
    assert p.pages == ["12345", "67890"]
    p.add_line("xyz")
    assert p.pages == ["12345", "67890\nxyz"]


def test_paginator_handles_long_line():
    p = Paginator(limit=5)
    p.add_line("abcdef")
    assert p.pages == ["abcde", "f"]
