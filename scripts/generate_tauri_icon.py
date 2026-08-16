import math
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "desktop-client" / "src-tauri" / "icons"
BLUE = (0, 118, 246, 255)
GREEN = (37, 197, 107, 255)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def inside_round_rect(px, py, x, y, w, h, r):
    if px < x or py < y or px > x + w or py > y + h:
        return False
    cx = min(max(px, x + r), x + w - r)
    cy = min(max(py, y + r), y + h - r)
    return (px - cx) ** 2 + (py - cy) ** 2 <= r**2


def inside_ellipse(px, py, cx, cy, rx, ry):
    return ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1


def inside_triangle(px, py, a, b, c):
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    p = (px, py)
    d1 = sign(p, a, b)
    d2 = sign(p, b, c)
    d3 = sign(p, c, a)
    has_neg = d1 < 0 or d2 < 0 or d3 < 0
    has_pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (has_neg and has_pos)


def distance_to_segment(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def feather_space(px, py):
    angle = -0.78
    dx = px - 256
    dy = py - 256
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    u = dx * cos_a + dy * sin_a
    v = -dx * sin_a + dy * cos_a
    return u, v


def feather_center_offset(t):
    return -18 * math.sin(math.pi * t) * (1 - 0.25 * t)


def feather_width(t):
    return 66 * (math.sin(math.pi * t) ** 0.58) * (1 - 0.08 * t)


def inside_feather(px, py):
    u, v = feather_space(px, py)
    if u < -142 or u > 150:
        return False
    t = (u + 142) / 292
    return abs(v - feather_center_offset(t)) <= feather_width(t)


def inside_feather_cut(px, py):
    u, v = feather_space(px, py)
    if -118 <= u <= 126:
        t = (u + 142) / 292
        if abs(v - feather_center_offset(t)) <= 4.5:
            return True
    cuts = [
        (-70, 0, -116, -38),
        (-36, -3, -92, -54),
        (0, -6, -56, -60),
        (34, -8, -14, -58),
        (64, -8, 28, -48),
        (-58, 8, -105, 42),
        (-18, 7, -70, 54),
        (22, 5, -22, 52),
        (60, 1, 26, 38),
    ]
    for ax, ay, bx, by in cuts:
        if distance_to_segment(u, v, ax, ay, bx, by) <= 3.2:
            return True
    return False


def paint(buffer, size, predicate, color):
    for y in range(size):
        row = y * size * 4
        for x in range(size):
            if predicate(x, y):
                i = row + x * 4
                buffer[i : i + 4] = bytes(color)


def render(size):
    scale = 4
    canvas = size * scale
    buffer = bytearray(TRANSPARENT * (canvas * canvas))
    f = canvas / 512

    paint(
        buffer,
        canvas,
        lambda x, y: inside_round_rect(x, y, 58 * f, 58 * f, 396 * f, 396 * f, 112 * f),
        BLUE,
    )
    paint(buffer, canvas, lambda x, y: inside_feather(x / f, y / f), WHITE)
    paint(buffer, canvas, lambda x, y: inside_feather_cut(x / f, y / f), BLUE)

    output = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            sums = [0, 0, 0, 0]
            for sy in range(scale):
                for sx in range(scale):
                    source = ((y * scale + sy) * canvas + (x * scale + sx)) * 4
                    for channel in range(4):
                        sums[channel] += buffer[source + channel]
            target = (y * size + x) * 4
            for channel in range(4):
                output[target + channel] = math.floor(sums[channel] / (scale * scale))
    return bytes(output)


def png_bytes(width, height, rgba):
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(rgba[y * stride : (y + 1) * stride])

    def chunk(kind, data):
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def write_png(path, width, height, rgba):
    path.write_bytes(png_bytes(width, height, rgba))


def write_icns(path):
    entries = []
    for kind, size in {
        "icp4": 16,
        "icp5": 32,
        "icp6": 64,
        "ic07": 128,
        "ic08": 256,
        "ic09": 512,
        "ic10": 1024,
    }.items():
        entries.append((kind.encode("ascii"), png_bytes(size, size, render(size))))

    total = 8 + sum(8 + len(data) for _, data in entries)
    output = bytearray(b"icns" + struct.pack(">I", total))
    for kind, data in entries:
        output.extend(kind)
        output.extend(struct.pack(">I", 8 + len(data)))
        output.extend(data)
    path.write_bytes(output)


def main():
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    pngs = {
        "icon.png": 512,
        "128x128@2x.png": 256,
        "128x128.png": 128,
        "32x32.png": 32,
    }
    for filename, size in pngs.items():
        write_png(ICON_DIR / filename, size, size, render(size))

    write_icns(ICON_DIR / "icon.icns")


if __name__ == "__main__":
    main()
