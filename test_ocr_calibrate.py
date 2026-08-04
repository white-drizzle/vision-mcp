import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import ocr_extract


def test_engine_singleton_reused():
    e1 = ocr_extract._get_engine()
    e2 = ocr_extract._get_engine()
    assert e1 is e2


def test_guess_mime():
    assert ocr_extract._guess_mime("x.png", b"\x89PNG\r\n") == "image/png"
    assert ocr_extract._guess_mime("x.jpg", b"\xff\xd8\xff\xe0") == "image/jpeg"
