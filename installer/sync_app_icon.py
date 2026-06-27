"""Synchronisiert App-Icon für App- und Setup-Build (PNG/ICO → Multi-Size-ICO)."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow fehlt — bitte installieren: pip install pillow")

# Größte zuerst — Windows Explorer / PyInstaller nutzen 256 px für große Ansichten.
ICON_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


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


def _load_best_source(png_path: Path, ico_path: Path) -> Image.Image:
    if png_path.exists():
        with Image.open(png_path) as img:
            return img.convert("RGBA")

    if ico_path.exists():
        with Image.open(ico_path) as img:
            best = img.convert("RGBA")
            count = getattr(img, "n_frames", 1)
            for index in range(count):
                img.seek(index)
                if img.size[0] >= best.size[0]:
                    best = img.convert("RGBA")
            return best

    raise FileNotFoundError(
        "Kein App-Icon gefunden. Bitte ablegen als:\n"
        "  assets/images/app_icon.png  (empfohlen, mind. 256×256)\n"
        "  oder assets/images/app_icon.ico"
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
    png_path = images_dir / "app_icon.png"
    project_ico = images_dir / "app_icon.ico"
    installer_ico = Path(__file__).resolve().parent / "assets" / "app_icon.ico"

    source_label = ""
    rebuild = force or _needs_rebuild(project_ico)

    if png_path.exists():
        png_mtime = png_path.stat().st_mtime
        ico_mtime = project_ico.stat().st_mtime if project_ico.exists() else 0
        if rebuild or png_mtime >= ico_mtime:
            with Image.open(png_path) as img:
                _save_multi_ico(img, project_ico)
            source_label = "assets/images/app_icon.png"
            if verbose:
                print(f"Icon: PNG -> Multi-Size-ICO ({project_ico})")
    elif rebuild:
        source = _load_best_source(png_path, project_ico)
        _save_multi_ico(source, project_ico)
        source_label = "assets/images/app_icon.ico (aufbereitet)"
        if verbose:
            print(f"Icon: ICO -> Multi-Size-ICO ({project_ico})")

    if not project_ico.exists():
        raise FileNotFoundError(
            "Kein App-Icon gefunden. Bitte ablegen als:\n"
            "  assets/images/app_icon.png  (empfohlen)\n"
            "  oder assets/images/app_icon.ico"
        )

    installer_ico.parent.mkdir(parents=True, exist_ok=True)
    installer_ico.write_bytes(project_ico.read_bytes())

    sizes = _ico_frame_sizes(project_ico)
    if verbose:
        label = source_label or "assets/images/app_icon.ico"
        print(f"App-Icon bereit ({label}): {project_ico}")
        print(f"  Groessen: {', '.join(f'{w}x{h}' for w, h in sizes)}")

    return project_ico


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
