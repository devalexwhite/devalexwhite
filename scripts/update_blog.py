#!/usr/bin/env python3
"""Sync the latest posts from https://thatalexguy.dev/feed.xml into README.md."""

from __future__ import annotations

import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED_URL = "https://thatalexguy.dev/feed.xml"
MAX_POSTS = 5
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def escape_md(text: str) -> str:
    return text.replace("[", r"\[").replace("]", r"\]")


def fetch_posts(feed_url: str, limit: int) -> list[str]:
    req = urllib.request.Request(
        feed_url,
        headers={"User-Agent": "devalexwhite-profile-sync/1.0 (+https://github.com/devalexwhite)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        xml_bytes = resp.read()

    root = ET.fromstring(xml_bytes)
    lines: list[str] = []

    for item in root.findall("./channel/item")[:limit]:
        raw_title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()

        if not raw_title or not link:
            continue

        date_suffix = ""
        if pub_date:
            try:
                dt = parsedate_to_datetime(pub_date)
                date_suffix = f" *({dt.strftime('%b %d, %Y')})*"
            except (TypeError, ValueError):
                date_suffix = ""

        lines.append(f"- [{escape_md(raw_title)}]({link}){date_suffix}")

    if not lines:
        raise RuntimeError("No posts found in RSS feed.")

    return lines


def update_readme(readme_path: Path, post_lines: list[str]) -> bool:
    content = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"({re.escape(START_MARKER)}\n)(.*?)(\n{re.escape(END_MARKER)})",
        re.DOTALL,
    )
    if not pattern.search(content):
        raise RuntimeError("Blog post markers not found in README.md.")

    block = "\n".join(post_lines)
    updated = pattern.sub(lambda m: f"{m.group(1)}{block}{m.group(3)}", content, count=1)

    if updated == content:
        return False

    readme_path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    posts = fetch_posts(FEED_URL, MAX_POSTS)
    changed = update_readme(README_PATH, posts)
    print(f"Fetched {len(posts)} posts; README {'updated' if changed else 'already up to date'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
