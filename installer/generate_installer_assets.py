"""Erzeugt Launcher-Stil Installer-Grafiken und App-Icon."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pillow", "-q"]
    )
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

INSTALLER_BG = (920, 580)
SIDEBAR = (200, 580)
SMALL = (64, 64)
ICON_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# RSI Launcher Polish (star_citizen.qss)
COL_BG_TOP = (10, 13, 18)
COL_BG_MID = (16, 22, 32)
COL_BG_BOT = (7, 9, 13)
COL_ORANGE = (224, 122, 42)
COL_CYAN = (66, 212, 245)
COL_TEXT = (230, 238, 245)
COL_MUTED = (143, 163, 184)
COL_PANEL = (21, 29, 39)


def read_version_meta(root: Path) -> dict[str, str]:
    version_file = root / "config" / "version.py"
    content = version_file.read_text(encoding="utf-8")
    meta = {
        "app_name": "SC Salvage Tracker",
        "version": "0.14.2 Alpha",
        "build": "2026.06",
        "codename": "Live Update",
        "developer": "Christian",
        "alias": "Xan-Gan-Du",
    }
    for key, pattern in (
        ("app_name", r'APP_NAME\s*=\s*"([^"]+)"'),
        ("version", r'APP_VERSION\s*=\s*"([^"]+)"'),
        ("build", r'APP_BUILD\s*=\s*"([^"]+)"'),
        ("codename", r'APP_CODENAME\s*=\s*"([^"]+)"'),
        ("developer", r'DEVELOPER_NAME\s*=\s*"([^"]+)"'),
        ("alias", r'DEVELOPER_ALIAS\s*=\s*"([^"]+)"'),
    ):
        match = re.search(pattern, content)
        if match:
            meta[key] = match.group(1)
    return meta


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend([
            "C:/Windows/Fonts/Orbitron-Bold.ttf",
            str(Path(__file__).resolve().parent.parent / "assets/fonts/Orbitron-Bold.ttf"),
            "C:/Windows/Fonts/Rajdhani-Bold.ttf",
        ])
    else:
        candidates.extend([
            "C:/Windows/Fonts/Rajdhani-Regular.ttf",
            str(Path(__file__).resolve().parent.parent / "assets/fonts/Rajdhani-Regular.ttf"),
            "C:/Windows/Fonts/segoeui.ttf",
        ])
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_launcher_background(
    size: tuple[int, int],
    meta: dict[str, str],
    splash: Image.Image | None,
) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, COL_BG_TOP)
    draw = ImageDraw.Draw(img)

    for y in range(h):
        t = y / max(h - 1, 1)
        if t < 0.45:
            blend = t / 0.45
            r = int(COL_BG_TOP[0] + (COL_BG_MID[0] - COL_BG_TOP[0]) * blend)
            g = int(COL_BG_TOP[1] + (COL_BG_MID[1] - COL_BG_TOP[1]) * blend)
            b = int(COL_BG_TOP[2] + (COL_BG_MID[2] - COL_BG_TOP[2]) * blend)
        else:
            blend = (t - 0.45) / 0.55
            r = int(COL_BG_MID[0] + (COL_BG_BOT[0] - COL_BG_MID[0]) * blend)
            g = int(COL_BG_MID[1] + (COL_BG_BOT[1] - COL_BG_MID[1]) * blend)
            b = int(COL_BG_MID[2] + (COL_BG_BOT[2] - COL_BG_MID[2]) * blend)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    panel_top = 58
    panel_left = 24
    panel_right = w - 24
    panel_bottom = h - 52
    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=2,
        fill=COL_PANEL,
        outline=(30, 42, 56),
        width=1,
    )
    draw.rectangle(
        (panel_left, panel_top, panel_left + 4, panel_bottom),
        fill=COL_ORANGE,
    )

    draw.line(
        [(panel_left + 12, panel_top + 1), (panel_right - 12, panel_top + 1)],
        fill=COL_CYAN,
        width=1,
    )

    title_font = _font(26, bold=True)
    sub_font = _font(14)
    small_font = _font(11)

    draw.text((36, 14), "SC SALVAGE TRACKER", fill=COL_TEXT, font=title_font)
    draw.text(
        (36, 46),
        f"SETUP · {meta['version']} · Build {meta['build']}",
        fill=COL_MUTED,
        font=small_font,
    )
    draw.text(
        (36, panel_top + 18),
        "◆ INSTALLATIONSASSISTENT",
        fill=COL_ORANGE,
        font=sub_font,
    )
    draw.text(
        (36, panel_top + 42),
        (
            "Salvage Tracker · Raffinerie · Verkäufe · "
            "Crew-Auszahlung"
        ),
        fill=COL_MUTED,
        font=small_font,
    )

    footer = (
        f"{meta['codename']} · {meta['developer']} · {meta['alias']}"
    )
    draw.text((36, h - 28), footer, fill=COL_MUTED, font=small_font)

    if splash is not None:
        emblem = cover_crop(splash, 280, 280, focus_y=0.32)
        emblem = emblem.filter(ImageFilter.GaussianBlur(radius=0.3))
        emblem.putalpha(90)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(emblem, (w - 320, panel_top + 40), emblem)
        img = Image.alpha_composite(
            Image.new("RGBA", size, (0, 0, 0, 0)),
            img_rgba,
        ).convert("RGB")

    return img


def cover_crop(
    img: Image.Image,
    target_w: int,
    target_h: int,
    *,
    focus_y: float = 0.5,
) -> Image.Image:
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = int((new_h - target_h) * focus_y)
    top = max(0, min(top, new_h - target_h))
    return resized.crop((left, top, left + target_w, top + target_h))


def emblem_crop(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = int(min(w, h) * 0.52)
    left = (w - side) // 2
    top = int(h * 0.14)
    top = min(top, h - side)
    return img.crop((left, top, left + side, top + side))


def save_icon(emblem: Image.Image, target: Path) -> None:
    frames = [
        emblem.resize(size, Image.Resampling.LANCZOS)
        for size in ICON_SIZES
    ]
    frames[0].save(
        target,
        format="ICO",
        sizes=ICON_SIZES,
        append_images=frames[1:],
    )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    splash_path = root / "assets" / "images" / "splash.png"
    assets_dir = Path(__file__).resolve().parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    meta = read_version_meta(root)
    splash = None
    if splash_path.exists():
        splash = Image.open(splash_path).convert("RGBA")

    bg = draw_launcher_background(INSTALLER_BG, meta, splash)
    bg.save(assets_dir / "install_bg.png", optimize=True)

    if splash is not None:
        cover_crop(splash, *SIDEBAR, focus_y=0.35).save(
            assets_dir / "wizard_sidebar.png",
            optimize=True,
        )
        emblem = emblem_crop(splash)
        emblem.resize(SMALL, Image.Resampling.LANCZOS).save(
            assets_dir / "wizard_small.png",
            optimize=True,
        )
        save_icon(emblem, assets_dir / "app_icon.ico")
    else:
        fallback = Image.new("RGBA", (256, 256), (*COL_ORANGE, 255))
        save_icon(fallback, assets_dir / "app_icon.ico")

    project_icon = root / "assets" / "images" / "app_icon.ico"
    project_icon.parent.mkdir(parents=True, exist_ok=True)
    project_icon.write_bytes((assets_dir / "app_icon.ico").read_bytes())

    print(f"Installer-Grafiken (Launcher-Stil): {assets_dir}")
    print(f"  Version: {meta['version']} · {meta['codename']}")
    print(f"  install_bg.png      {INSTALLER_BG[0]}x{INSTALLER_BG[1]}")
    print(f"  app_icon.ico")
    print(f"Projekt-Icon: {project_icon}")


if __name__ == "__main__":
    main()
