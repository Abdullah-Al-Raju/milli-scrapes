"""
tests/test_visual_verifier.py
=============================
Tests for MilliVisualVerifier:
- Positive portrait verification
- Anti-hallucination rejection of cakes, food, flat objects, and blanks
- Document/table structured edge verification
- Corrupt buffer resilience
"""

import io
import numpy as np
from PIL import Image, ImageDraw
import pytest

from milli_scrapes import MilliVisualVerifier, VisualCategory


def create_mock_portrait() -> bytes:
    """Generates synthetic portrait with skin-toned oval face and facial features."""
    img = Image.new("RGB", (200, 260), color=(30, 30, 40))
    draw = ImageDraw.Draw(img)
    # Human skin-tone oval: RGB(220, 160, 130) -> YCbCr Cb ~112, Cr ~150 (perfect human skin range)
    draw.ellipse([(40, 30), (160, 200)], fill=(220, 160, 130))
    # Eyes
    draw.ellipse([(65, 85), (85, 100)], fill=(40, 20, 15))
    draw.ellipse([(115, 85), (135, 100)], fill=(40, 20, 15))
    # Mouth
    draw.line([(80, 155), (120, 155)], fill=(160, 50, 50), width=4)
    # Hair
    draw.ellipse([(35, 15), (165, 75)], fill=(30, 20, 15))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_mock_cake_biscuit() -> bytes:
    """Generates synthetic cookie/biscuit with chocolate text (simulating Biscoito_Assinado_Selena_Gomez)."""
    # Brown biscuit color RGB(110, 60, 20) -> outside the human skin envelope
    img = Image.new("RGB", (200, 200), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (180, 180)], fill=(100, 55, 20))
    draw.text((40, 90), "Selena Gomez", fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_mock_table_document() -> bytes:
    """Generates synthetic table with text and grid lines."""
    img = Image.new("RGB", (300, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for y in range(20, 190, 30):
        draw.line([(20, y), (280, y)], fill=(50, 50, 50), width=2)
    for x in range(20, 290, 65):
        draw.line([(x, 20), (x, 170)], fill=(50, 50, 50), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_portrait_verification_success():
    portrait_bytes = create_mock_portrait()
    res = MilliVisualVerifier.verify_buffer(portrait_bytes, target_category=VisualCategory.PORTRAIT)
    assert res.is_valid is True
    assert res.confidence >= 0.6
    assert res.category == VisualCategory.PORTRAIT
    assert "Verified human portrait" in res.reason


def test_cake_biscuit_rejection_anti_hallucination():
    cake_bytes = create_mock_cake_biscuit()
    res = MilliVisualVerifier.verify_buffer(cake_bytes, target_category=VisualCategory.PORTRAIT)
    assert res.is_valid is False
    assert "No human facial complexion detected" in res.reason or "rejected" in res.reason


def test_blank_placeholder_rejection():
    # Solid white placeholder
    img = Image.new("RGB", (150, 150), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    res = MilliVisualVerifier.verify_buffer(buf.getvalue(), target_category=VisualCategory.PORTRAIT)
    assert res.is_valid is False
    assert "monochromatic" in res.reason.lower() or "variance" in res.reason.lower()


def test_corrupt_buffer_handling():
    corrupt_bytes = b"NOT_AN_IMAGE_PAYLOAD_GARBAGE_BYTES_12345"
    res = MilliVisualVerifier.verify_buffer(corrupt_bytes, target_category=VisualCategory.PORTRAIT)
    assert res.is_valid is False
    assert "decode failure" in res.reason.lower() or "too small" in res.reason.lower()


def test_document_table_verification():
    table_bytes = create_mock_table_document()
    res = MilliVisualVerifier.verify_buffer(table_bytes, target_category=VisualCategory.TABLE)
    assert res.is_valid is True
    assert res.category == VisualCategory.TABLE
    assert res.confidence >= 0.7
