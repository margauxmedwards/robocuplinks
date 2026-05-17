#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Dict, Set, Tuple
from urllib.parse import urlparse

import qrcode
from PIL import Image, ImageDraw, ImageFont


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_redirect_html(target_url: str) -> str:
    escaped = escape_html(target_url)
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta http-equiv='refresh' content='0; url={escaped}'>"
        "<meta name='robots' content='noindex'>"
        f"<link rel='canonical' href='{escaped}'>"
        "<title>Redirecting...</title></head><body>"
        f"<noscript><a href='{escaped}'>Continue</a></noscript>"
        f"<script>location.replace(\"{escaped}\");</script>"
        "</body></html>"
    )


def compose_short_url(short_base_url: str, relative_html_path: str) -> str:
    base = short_base_url.rstrip("/")
    normalized = relative_html_path.lstrip("/")

    if normalized.endswith("/index.html"):
        without_index = normalized[: -len("index.html")]
        return f"{base}/{without_index}"

    if normalized.endswith(".html"):
        return f"{base}/{normalized}"

    raise ValueError(f"Unsupported redirect path for short URL: {relative_html_path}")


def make_qr_image(short_url: str, caption: str) -> Image.Image:
    qr = qrcode.QRCode(border=4, box_size=9, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(short_url)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = 360
    qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    font = ImageFont.load_default()
    padding = 18
    text_height = 18
    canvas_width = qr_size + (padding * 2)
    canvas_height = qr_size + text_height + (padding * 3)
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    canvas.paste(qr_image, (padding, padding))

    draw = ImageDraw.Draw(canvas)
    text_bbox = draw.textbbox((0, 0), caption, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = max((canvas_width - text_width) // 2, padding)
    text_y = qr_size + (padding * 2)
    draw.text((text_x, text_y), caption, fill="black", font=font)
    return canvas


def qr_output_path_for_html(repo_root: Path, qr_dir: str, relative_html_path: str) -> Path:
    html_path = Path(relative_html_path)
    if html_path.suffix.lower() != ".html":
        raise ValueError(f"QR generation expects an .html path, got: {relative_html_path}")
    png_relative = html_path.with_suffix(".png")
    return repo_root / qr_dir / png_relative


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def assert_safe_relative_html_path(path: str) -> None:
    path_obj = Path(path)
    if path_obj.is_absolute():
        raise ValueError(f"Path must be relative: {path}")
    if ".." in path_obj.parts:
        raise ValueError(f"Path cannot contain '..': {path}")
    if path_obj.suffix.lower() != ".html":
        raise ValueError(f"Path must end with .html: {path}")


def load_config(config_path: Path) -> Dict[str, str]:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, dict):
        raise ValueError("Config must be a JSON object of {path: url} pairs.")
    return config


def write_redirect_files(repo_root: Path, redirects: Dict[str, str]) -> int:
    updates = 0
    for relative_path, target_url in redirects.items():
        if not isinstance(relative_path, str) or not isinstance(target_url, str):
            raise ValueError("Each redirect mapping must be string:string.")

        assert_safe_relative_html_path(relative_path)
        if not is_valid_url(target_url):
            raise ValueError(f"Invalid URL for '{relative_path}': {target_url}")

        output_path = repo_root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        new_content = render_redirect_html(target_url)
        old_content = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        if old_content != new_content:
            output_path.write_text(new_content, encoding="utf-8")
            updates += 1

    return updates


def write_qr_files(
    repo_root: Path,
    redirects: Dict[str, str],
    short_base_url: str,
    qr_dir: str,
) -> Tuple[int, Set[Path]]:
    updates = 0
    expected_paths: Set[Path] = set()

    for relative_path in redirects:
        assert_safe_relative_html_path(relative_path)
        short_url = compose_short_url(short_base_url, relative_path)
        output_path = qr_output_path_for_html(repo_root, qr_dir, relative_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        image = make_qr_image(short_url=short_url, caption=short_url)
        expected_paths.add(output_path.resolve())

        current_bytes = output_path.read_bytes() if output_path.exists() else None
        with output_path.open("wb") as handle:
            image.save(handle, format="PNG")
        new_bytes = output_path.read_bytes()
        if current_bytes != new_bytes:
            updates += 1

    return updates, expected_paths


def prune_stale_qr_files(repo_root: Path, qr_dir: str, expected_paths: Set[Path]) -> int:
    qr_root = (repo_root / qr_dir).resolve()
    if not qr_root.exists():
        return 0

    removed = 0
    for file_path in qr_root.rglob("*.png"):
        resolved = file_path.resolve()
        if resolved not in expected_paths:
            file_path.unlink()
            removed += 1
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Update redirect HTML files from JSON config.")
    parser.add_argument(
        "--config",
        default="redirects.json",
        help="Path to redirects JSON file (default: redirects.json)",
    )
    parser.add_argument(
        "--short-base-url",
        default="https://margauxmedwards.github.io/robocuplinks",
        help="Base URL used for generated short-link QR captions",
    )
    parser.add_argument(
        "--qr-dir",
        default="qr",
        help="Directory for generated QR image files",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    config_path = (repo_root / args.config).resolve()
    redirects = load_config(config_path)
    updated_count = write_redirect_files(repo_root, redirects)
    qr_updated_count, expected_qr_paths = write_qr_files(
        repo_root=repo_root,
        redirects=redirects,
        short_base_url=args.short_base_url,
        qr_dir=args.qr_dir,
    )
    qr_removed_count = prune_stale_qr_files(repo_root, args.qr_dir, expected_qr_paths)

    print(
        f"Processed {len(redirects)} redirects. "
        f"Updated {updated_count} redirect file(s), "
        f"updated {qr_updated_count} QR file(s), "
        f"removed {qr_removed_count} stale QR file(s)."
    )


if __name__ == "__main__":
    main()