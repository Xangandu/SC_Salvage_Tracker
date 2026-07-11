"""Synchronisiert scst_solo_logo.ico für App- und Setup-Build."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow fehlt — bitte installieren: pip install pillow")

from config.app_icon import (
    SOLO_APP_ICON_NAME,
    SOLO_APP_ICON_PNG,
    installer_app_icon_path,
)

# Größte zuerst — Windows Explorer / PyInstaller nutzen 256 px für große Ansichten.
ICON_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def _root() -> Path:
    return _ROOT


def _ico_frame_sizes(path: Path) -> list[tuple[int, int]]:
    with Image.open(path) as img:
        info_sizes = img.info.get("sizes") if img.info else None
        if info_sizes:
            return sorted({tuple(size) for size in info_sizes}, reverse=True)

        count = getattr(img, "n_frames", 1)
        sizes: list[tuple[int, int]] = []
        for index in range(count):
            img.seek(index)
            sizes.append(img.size)
        return sizes


def _load_best_source(ico_path: Path, png_path: Path) -> Image.Image:
    if ico_path.exists():
        with Image.open(ico_path) as img:
            best = img.convert("RGBA")
            count = getattr(img, "n_frames", 1)
            for index in range(count):
                img.seek(index)
                if img.size[0] >= best.size[0]:
                    best = img.convert("RGBA")
            return best

    if png_path.exists():
        with Image.open(png_path) as img:
            return img.convert("RGBA")

    raise FileNotFoundError(
        "Kein App-Icon gefunden. Bitte ablegen als:\n"
        f"  assets/images/{SOLO_APP_ICON_NAME}  (empfohlen)\n"
        f"  oder assets/images/{SOLO_APP_ICON_PNG}"
    )


def _save_multi_ico(source: Image.Image, target: Path) -> None:
    rgba = source.convert("RGBA")
    side = max(rgba.size)
    if side < 256:
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        scale = min(256 / rgba.width, 256 / rgba.height)
        new_w = max(1, int(rgba.width * scale))
        new_h = max(1, int(rgba.height * scale))
        resized = rgba.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas.paste(
            resized,
            ((256 - new_w) // 2, (256 - new_h) // 2),
            resized,
        )
        rgba = canvas

    target.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(
        target,
        format="ICO",
        sizes=ICON_SIZES + [(24, 24)],
    )


def _needs_rebuild(ico_path: Path) -> bool:
    if not ico_path.exists():
        return True
    sizes = _ico_frame_sizes(ico_path)
    if len(sizes) < 4:
        return True
    return max(max(w, h) for w, h in sizes) < 256


def sync_app_icon(*, verbose: bool = True, force: bool = False) -> Path:
    root = _root()
    images_dir = root / "assets" / "images"
    ico_path = images_dir / SOLO_APP_ICON_NAME
    png_path = images_dir / SOLO_APP_ICON_PNG
    installer_ico = installer_app_icon_path(Path(__file__).resolve().parent)

    source_label = ""

    if ico_path.exists():
        if force or _needs_rebuild(ico_path):
            source = _load_best_source(ico_path, png_path)
            _save_multi_ico(source, ico_path)
            source_label = f"assets/images/{SOLO_APP_ICON_NAME} (aufbereitet)"
            if verbose:
                print(f"Icon: ICO -> Multi-Size-ICO ({ico_path})")
        else:
            source_label = f"assets/images/{SOLO_APP_ICON_NAME}"
    elif png_path.exists():
        with Image.open(png_path) as img:
            _save_multi_ico(img, ico_path)
        source_label = f"assets/images/{SOLO_APP_ICON_PNG}"
        if verbose:
            print(f"Icon: PNG -> Multi-Size-ICO ({ico_path})")
    else:
        raise FileNotFoundError(
            "Kein App-Icon gefunden. Bitte ablegen als:\n"
            f"  assets/images/{SOLO_APP_ICON_NAME}\n"
            f"  oder assets/images/{SOLO_APP_ICON_PNG}"
        )

    installer_ico.parent.mkdir(parents=True, exist_ok=True)
    installer_ico.write_bytes(ico_path.read_bytes())

    sizes = _ico_frame_sizes(ico_path)
    if verbose:
        label = source_label or f"assets/images/{SOLO_APP_ICON_NAME}"
        print(f"App-Icon bereit ({label}): {ico_path}")
        print(f"  Installer-Kopie: {installer_ico}")
        print(f"  Groessen: {', '.join(f'{w}x{h}' for w, h in sizes)}")

    return ico_path


def main() -> int:
    force = "--force" in sys.argv
    try:
        sync_app_icon(verbose=True, force=force)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
