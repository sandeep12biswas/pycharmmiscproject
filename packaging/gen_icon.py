"""Generates the NoteApp icon set from a single vector-ish drawing routine.

Run once (or whenever the design changes) with the dev venv active:

    pip install Pillow numpy
    python packaging/gen_icon.py

Writes resources/icons/icon.png (1024x1024 master), a set of PNG sizes for
the Linux hicolor icon theme, and icon.ico (multi-resolution) for the
Windows installer/shortcut.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = PROJECT_ROOT / "resources" / "icons"

SS = 4  # supersample factor for antialiasing
SIZE = 1024
CANVAS = SIZE * SS

TOP_COLOR = (91, 110, 225)      # #5B6EE1 indigo
BOTTOM_COLOR = (124, 77, 219)   # #7C4DDB violet
PAGE_COLOR = (250, 250, 252)
LINE_COLOR = (120, 110, 190)
FOLD_COLOR = (222, 220, 240)
FOLD_SHADOW = (200, 197, 225)


def diagonal_gradient(size: int, c1: tuple[int, int, int], c2: tuple[int, int, int]) -> Image.Image:
    t = (np.arange(size) + np.arange(size)[:, None]) / (2 * (size - 1))
    t = t[..., None]
    c1_arr = np.array(c1, dtype=np.float32)
    c2_arr = np.array(c2, dtype=np.float32)
    rgb = (c1_arr * (1 - t) + c2_arr * t).astype(np.uint8)
    alpha = np.full((size, size, 1), 255, dtype=np.uint8)
    return Image.fromarray(np.concatenate([rgb, alpha], axis=-1), mode="RGBA")


def build_master() -> Image.Image:
    bg = diagonal_gradient(CANVAS, TOP_COLOR, BOTTOM_COLOR)

    mask = Image.new("L", (CANVAS, CANVAS), 0)
    mdraw = ImageDraw.Draw(mask)
    pad = int(CANVAS * 0.04)
    radius = int(CANVAS * 0.22)
    mdraw.rounded_rectangle([pad, pad, CANVAS - pad, CANVAS - pad], radius=radius, fill=255)

    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(bg, (0, 0), mask)
    draw = ImageDraw.Draw(canvas)

    # Page (notepad) body, inset within the rounded-square background.
    page_l = int(CANVAS * 0.26)
    page_t = int(CANVAS * 0.18)
    page_r = int(CANVAS * 0.76)
    page_b = int(CANVAS * 0.84)
    page_radius = int(CANVAS * 0.04)
    fold = int((page_r - page_l) * 0.28)

    draw.rounded_rectangle([page_l, page_t, page_r, page_b], radius=page_radius, fill=PAGE_COLOR)

    # Folded top-right corner.
    draw.polygon(
        [
            (page_r - fold, page_t),
            (page_r, page_t + fold),
            (page_r - fold, page_t + fold),
        ],
        fill=FOLD_SHADOW,
    )
    draw.polygon(
        [
            (page_r - fold, page_t),
            (page_r - fold, page_t + fold),
            (page_r - int(fold * 0.08), page_t + int(fold * 0.08)),
        ],
        fill=FOLD_COLOR,
    )

    # Text lines.
    line_h = int(CANVAS * 0.028)
    line_x0 = page_l + int(CANVAS * 0.07)
    line_widths = [0.62, 0.62, 0.42]
    line_gap = int(CANVAS * 0.10)
    line_y = page_t + int(CANVAS * 0.20)
    for frac in line_widths:
        line_x1 = line_x0 + int((page_r - page_l - int(CANVAS * 0.14)) * frac)
        draw.rounded_rectangle(
            [line_x0, line_y, line_x1, line_y + line_h], radius=line_h // 2, fill=LINE_COLOR
        )
        line_y += line_gap

    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    master = build_master()
    master.save(ICONS_DIR / "icon.png")

    hicolor_sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    for size in hicolor_sizes:
        resized = master.resize((size, size), Image.LANCZOS)
        resized.save(ICONS_DIR / f"icon_{size}.png")

    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    master.save(ICONS_DIR / "icon.ico", sizes=ico_sizes)

    print(f"Wrote icon set to {ICONS_DIR}")


if __name__ == "__main__":
    main()
