#!/usr/bin/env python3
"""Rewrite assets/icon.png and assets/og.png.

The GitHub contents API used for the first publish stores file bodies as
UTF-8, which corrupts PNG bytes. This script runs in Actions and commits
the same images the product build writes.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

_GLYPHS: dict[str, tuple[str, ...]] = {
    " ": ("00000",) * 7,
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "\u00b7": ("00000", "00000", "00000", "00100", "00000", "00000", "00000"),
}


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png_rgb(path: Path, width: int, height: int, rgb: bytes | bytearray) -> None:
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        start = y * stride
        raw.extend(rgb[start : start + stride])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


def _fill(buf: bytearray, width: int, height: int, color: tuple[int, int, int]) -> None:
    pixel = bytes(color)
    row = pixel * width
    for y in range(height):
        start = y * width * 3
        buf[start : start + width * 3] = row


def _rect(
    buf: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(width, x1)
    y1 = min(height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    span = (x1 - x0) * 3
    for y in range(y0, y1):
        start = (y * width + x0) * 3
        buf[start : start + span] = row


def _text_width(text: str, scale: int) -> int:
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def _blit(
    buf: bytearray,
    width: int,
    height: int,
    text: str,
    x: int,
    y: int,
    scale: int,
    color: tuple[int, int, int],
) -> None:
    cursor = x
    for ch in text:
        glyph = _GLYPHS.get(ch, _GLYPHS[" "])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit != "1":
                    continue
                _rect(
                    buf,
                    width,
                    height,
                    cursor + col * scale,
                    y + row * scale,
                    cursor + (col + 1) * scale,
                    y + (row + 1) * scale,
                    color,
                )
        cursor += 6 * scale


def _centered(text: str, canvas: int, scale: int) -> int:
    return max(0, (canvas - _text_width(text, scale)) // 2)


def write_icon(path: Path) -> None:
    size = 64
    buf = bytearray(size * size * 3)
    _fill(buf, size, size, (14, 59, 50))
    _rect(buf, size, size, 0, 0, size, 6, (212, 168, 74))
    label = "V"
    scale = 6
    _blit(buf, size, size, label, _centered(label, size, scale), 14, scale, (244, 239, 228))
    write_png_rgb(path, size, size, buf)


def write_og(path: Path) -> None:
    width, height = 1200, 630
    buf = bytearray(width * height * 3)
    bg = (10, 26, 22)
    cream = (244, 239, 228)
    muted = (176, 198, 188)
    gold = (232, 196, 120)
    _fill(buf, width, height, bg)
    _rect(buf, width, height, 0, 0, width, 12, (212, 168, 74))
    _rect(buf, width, height, 36, 36, width - 36, height - 36, (28, 72, 60))
    _rect(buf, width, height, 40, 40, width - 40, height - 40, bg)
    lines = [
        (118, 16, "VMBRIDGE", cream),
        (268, 5, "FOR PARALLELS DESKTOP", muted),
        (360, 6, "LET YOUR AI AGENT DRIVE", cream),
        (430, 6, "PARALLELS DESKTOP VMS", cream),
        (520, 5, "$10 ONCE  \u00b7  7-DAY TRIAL", gold),
    ]
    for y, scale, text, color in lines:
        _blit(buf, width, height, text, _centered(text, width, scale), y, scale, color)
    _rect(buf, width, height, 420, 328, 780, 334, gold)
    write_png_rgb(path, width, height, buf)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    write_icon(assets / "icon.png")
    write_og(assets / "og.png")


if __name__ == "__main__":
    main()
