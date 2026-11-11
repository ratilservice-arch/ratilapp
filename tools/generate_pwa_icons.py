"""Generate simple branded PNG icons using only the Python standard library."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAVY = (44, 62, 80)
ORANGE = (230, 126, 34)
WHITE = (255, 255, 255)
FONT = {
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
}


def png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def draw_icon(size: int, destination: Path) -> None:
    image = bytearray(NAVY * (size * size))

    def pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < size and 0 <= y < size:
            offset = (y * size + x) * 3
            image[offset : offset + 3] = bytes(color)

    def line(x1: float, y1: float, x2: float, y2: float, width: float, color: tuple[int, int, int]) -> None:
        radius = width / 2
        min_x = max(0, int(min(x1, x2) - radius - 1))
        max_x = min(size - 1, int(max(x1, x2) + radius + 1))
        min_y = max(0, int(min(y1, y2) - radius - 1))
        max_y = min(size - 1, int(max(y1, y2) + radius + 1))
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                t = 0 if length_sq == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / length_sq))
                near_x, near_y = x1 + t * dx, y1 + t * dy
                if (x - near_x) ** 2 + (y - near_y) ** 2 <= radius * radius:
                    pixel(x, y, color)

    def ring(cx: float, cy: float, radius: float, thickness: float, color: tuple[int, int, int]) -> None:
        outer_sq, inner_sq = (radius + thickness / 2) ** 2, (radius - thickness / 2) ** 2
        for y in range(max(0, int(cy - radius - thickness)), min(size, int(cy + radius + thickness + 1))):
            for x in range(max(0, int(cx - radius - thickness)), min(size, int(cx + radius + thickness + 1))):
                distance_sq = (x - cx) ** 2 + (y - cy) ** 2
                if inner_sq <= distance_sq <= outer_sq:
                    pixel(x, y, color)

    # Keep all artwork within the maskable-icon safe zone.
    ring(size * 0.5, size * 0.44, size * 0.30, size * 0.025, ORANGE)
    stroke = size * 0.075
    x_left, x_right = size * 0.39, size * 0.61
    y_top, y_mid, y_bottom = size * 0.27, size * 0.48, size * 0.68
    line(x_left, y_top, x_left, y_bottom, stroke, WHITE)
    line(x_left, y_top, x_right, y_top, stroke, WHITE)
    line(x_right, y_top, x_right, y_mid, stroke, WHITE)
    line(x_left, y_mid, x_right, y_mid, stroke, WHITE)
    line(size * 0.50, y_mid, size * 0.66, y_bottom, stroke, WHITE)

    cell = max(2, round(size / 72))
    gap = cell
    text_width = (5 * cell + gap) * 5 - gap
    start_x = (size - text_width) // 2
    start_y = round(size * 0.79)
    for index, character in enumerate("RATIL"):
        glyph_x = start_x + index * (5 * cell + gap)
        for row, bits in enumerate(FONT[character]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    for py in range(row * cell, (row + 1) * cell):
                        for px in range(column * cell, (column + 1) * cell):
                            pixel(glyph_x + px, start_y + py, ORANGE)

    raw = b"".join(b"\x00" + image[y * size * 3 : (y + 1) * size * 3] for y in range(size))
    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(png)


if __name__ == "__main__":
    draw_icon(192, ROOT / "icons" / "icon-192.png")
    draw_icon(512, ROOT / "icons" / "icon-512.png")
    draw_icon(512, ROOT / "icons" / "icon-512-maskable.png")
    print("Generated 192px and 512px RATIL PWA icons.")
