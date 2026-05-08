#!/usr/bin/env python3
"""Update the website blog index and home Latest block from blog HTML posts.

Conservative automation: this script only rewrites generated card lists. It does not
invent posts, publish externally, or touch non-blog content.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
BLOG = WEB / "blog"
BLOG_INDEX = BLOG / "index.html"
HOME = WEB / "index.html"

DATE_RE = re.compile(r'<div class="blog-date"[^>]*>(.*?)</div>', re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
META_DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)


@dataclass(order=True)
class Post:
    sort_date: datetime
    filename: str
    date: str
    title: str
    excerpt: str


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(re.sub(r"\s+", " ", text).strip())


def parse_date(value: str) -> datetime:
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported blog date: {value!r}")


def parse_post(path: Path) -> Post | None:
    if path.name == "index.html":
        return None
    text = path.read_text(encoding="utf-8-sig")
    date_m = DATE_RE.search(text)
    h1_m = H1_RE.search(text)
    if not date_m or not h1_m:
        return None
    date = clean(date_m.group(1))
    title = clean(h1_m.group(1))
    meta_m = META_DESC_RE.search(text)
    excerpt = html.unescape(meta_m.group(1)).strip() if meta_m else title
    return Post(parse_date(date), path.name, date, title, excerpt)


def card(post: Post, stagger: int = 1) -> str:
    return f'''        <a href="/blog/{post.filename}" class="blog-card animate-in stagger-{stagger}">
            <div class="blog-date">{html.escape(post.date)}</div>
            <div class="blog-title">{html.escape(post.title)}</div>
            <p class="blog-excerpt">{html.escape(post.excerpt)}</p>
        </a>'''


def replace_blog_list(text: str, cards: str) -> str:
    pattern = re.compile(r'(<div class="blog-list">)\s*.*?(\s*</div>\s*\n\s*<footer>)', re.S)
    new, count = pattern.subn(r"\1\n" + cards + r"\2", text, count=1)
    if count != 1:
        raise RuntimeError("Could not find blog index .blog-list block")
    return new


def replace_home_latest(text: str, cards: str) -> str:
    pattern = re.compile(r'(<div class="section-title animate-in">Latest</div>\s*<div class="blog-list">)\s*.*?(\s*</div>\s*\n\s*<div class="section-title animate-in">By the Numbers</div>)', re.S)
    new, count = pattern.subn(r"\1\n" + cards + r"\2", text, count=1)
    if count != 1:
        raise RuntimeError("Could not find home Latest block")
    return new


def main() -> int:
    posts = [p for p in (parse_post(path) for path in BLOG.glob("*.html")) if p]
    posts.sort(reverse=True)
    if not posts:
        raise RuntimeError("No blog posts found")

    index_cards = "\n\n".join(card(post, (i % 4) + 1) for i, post in enumerate(posts))
    home_cards = "\n\n".join(card(post, (i % 3) + 1) for i, post in enumerate(posts[:3]))

    BLOG_INDEX.write_text(replace_blog_list(BLOG_INDEX.read_text(encoding="utf-8-sig"), index_cards), encoding="utf-8")
    HOME.write_text(replace_home_latest(HOME.read_text(encoding="utf-8"), home_cards), encoding="utf-8")

    print(f"Updated blog/index.html with {len(posts)} posts")
    print(f"Updated index.html Latest with {min(3, len(posts))} posts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
