#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse


FIELD_LABELS = {
    "event_slug": "Event slug",
    "event_overview": "Event overview URL",
    "paste_links": "Paste links (Name: URL)",
    "line": "Line URL",
    "maze": "Maze URL",
    "onstage": "OnStage URL",
    "soccer": "Soccer URL",
    "sumo": "Sumo URL",
    "extra_links": "Extra links",
}

COMPONENT_ALIASES = {
    "line": "line",
    "maze": "maze",
    "onstage": "onstage",
    "on-stage": "onstage",
    "on-stage-stage": "onstage",
    "soccer": "soccer",
    "sumo": "sumo",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-")


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return bool(parsed.scheme and parsed.netloc)


def normalize_url(value: str) -> str:
    cleaned = value.strip().strip('"').strip("'").strip()
    # Accept accidental unmatched leading quote from copy-paste.
    if cleaned.startswith('"') or cleaned.startswith("'"):
        cleaned = cleaned[1:].strip()
    if cleaned.endswith('"') or cleaned.endswith("'"):
        cleaned = cleaned[:-1].strip()
    return cleaned


def extract_field(body: str, label: str) -> str:
    pattern = rf"^###\s+{re.escape(label)}\s*$\n(.*?)(?=^###\s+|\Z)"
    match = re.search(pattern, body, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    value = match.group(1).strip()
    if value == "_No response_":
        return ""
    return value


def parse_extra_links(raw: str) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    if not raw:
        return items

    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        if "," not in text:
            raise ValueError(f"Invalid extra link format: '{text}'. Use slug,url")
        link_slug, link_url = [piece.strip() for piece in text.split(",", 1)]
        link_url = normalize_url(link_url)
        clean_slug = slugify(link_slug)
        if not clean_slug:
            raise ValueError(f"Invalid extra link slug: '{link_slug}'")
        if not is_valid_url(link_url):
            raise ValueError(f"Invalid extra link URL for '{clean_slug}': '{link_url}'")
        items.append((clean_slug, link_url))
    return items


def parse_named_links(raw: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    if not raw:
        return pairs

    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("- ") or text.startswith("* "):
            text = text[2:].strip()
        if ":" not in text:
            raise ValueError(f"Invalid pasted link line: '{text}'. Use Name: URL")

        name, link_url = [piece.strip() for piece in text.split(":", 1)]
        clean_name = slugify(name)
        clean_url = normalize_url(link_url)

        if not clean_name:
            raise ValueError(f"Invalid pasted link name: '{name}'")
        if not is_valid_url(clean_url):
            raise ValueError(f"Invalid pasted link URL for '{clean_name}': '{clean_url}'")
        pairs.append((clean_name, clean_url))
    return pairs


def load_redirects(path: Path) -> Dict[str, str]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("redirects.json must be a JSON object.")
    return data


def save_redirects(path: Path, redirects: Dict[str, str]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(dict(sorted(redirects.items())), handle, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply event links from issue form body.")
    parser.add_argument("--issue-body", required=True, help="Path to issue body markdown text")
    parser.add_argument("--redirects", default="redirects.json", help="Path to redirects.json")
    args = parser.parse_args()

    body_path = Path(args.issue_body)
    redirects_path = Path(args.redirects)

    body = body_path.read_text(encoding="utf-8")
    event_slug_raw = extract_field(body, FIELD_LABELS["event_slug"])
    event_slug = slugify(event_slug_raw)
    if not event_slug:
        raise ValueError("Event slug is required.")

    event_overview = extract_field(body, FIELD_LABELS["event_overview"]).strip()
    paste_links_raw = extract_field(body, FIELD_LABELS["paste_links"])
    line_url = normalize_url(extract_field(body, FIELD_LABELS["line"]))
    maze_url = normalize_url(extract_field(body, FIELD_LABELS["maze"]))
    onstage_url = normalize_url(extract_field(body, FIELD_LABELS["onstage"]))
    soccer_url = normalize_url(extract_field(body, FIELD_LABELS["soccer"]))
    sumo_url = normalize_url(extract_field(body, FIELD_LABELS["sumo"]))
    extra_links_raw = extract_field(body, FIELD_LABELS["extra_links"])

    component_map = {
        "line": line_url,
        "maze": maze_url,
        "onstage": onstage_url,
        "soccer": soccer_url,
        "sumo": sumo_url,
    }

    for link_name, link_url in parse_named_links(paste_links_raw):
        canonical_name = COMPONENT_ALIASES.get(link_name)
        if canonical_name:
            component_map[canonical_name] = link_url
        else:
            component_map[link_name] = link_url

    redirects = load_redirects(redirects_path)

    updates: Dict[str, str] = {}
    if event_overview:
        event_overview = normalize_url(event_overview)
        if not is_valid_url(event_overview):
            raise ValueError("Event overview URL is invalid.")
        updates[f"r/{event_slug}.html"] = event_overview
        updates[f"r/{event_slug}/index.html"] = event_overview

    for component, url in component_map.items():
        if not url:
            continue
        if not is_valid_url(url):
            raise ValueError(f"{component} URL is invalid.")
        updates[f"r/{event_slug}/{component}.html"] = url

    for link_slug, link_url in parse_extra_links(extra_links_raw):
        updates[f"r/{event_slug}/{link_slug}.html"] = link_url

    if not updates:
        raise ValueError("At least one URL must be provided.")

    redirects.update(updates)
    save_redirects(redirects_path, redirects)

    print(f"event_slug={event_slug}")
    print(f"updated_paths={','.join(sorted(updates.keys()))}")


if __name__ == "__main__":
    main()