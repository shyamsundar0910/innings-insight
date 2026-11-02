#!/usr/bin/env python3
"""Refresh public Innings Insiders posts from the Substack RSS feed."""
import json
import re
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://inningsinsiders.substack.com/feed"
DEST = Path(__file__).resolve().parents[1] / "site" / "articles.json"

def plain(value):
    value = re.sub(r"<[^>]*>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def refresh():
    request = urllib.request.Request(FEED, headers={"User-Agent": "InningsInsightArticleSync/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        xml = response.read()
    root = ET.fromstring(xml)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Not an RSS channel")
    posts = []
    for item in channel.findall("item")[:12]:
        title = plain(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        if not title or not link.startswith("https://inningsinsiders.substack.com/"):
            continue
        description = plain(item.findtext("description"))[:210]
        date_raw = item.findtext("pubDate") or ""
        try:
            date = parsedate_to_datetime(date_raw).astimezone(timezone.utc).date().isoformat()
        except (ValueError, TypeError):
            date = ""
        image = ""
        enclosure = item.find("enclosure")
        if enclosure is not None and enclosure.attrib.get("type", "").startswith("image/"):
            image = enclosure.attrib.get("url", "")
        if not image:
            media = item.find("{http://search.yahoo.com/mrss/}content")
            if media is not None:
                image = media.attrib.get("url", "")
        if not image:
            content = item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or ""
            m = re.search(r'<img[^>]+src=["\'](https?[^"\']+)', content)
            if m:
                image = html.unescape(m.group(1))
        if not image.startswith("https://"):
            image = ""
        posts.append({"title": title, "url": link, "date": date, "description": description, "image": image})
    if not posts:
        raise ValueError("RSS returned no posts; refusing to replace existing articles")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({"source": FEED, "posts": posts}, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {len(posts)} articles")

if __name__ == "__main__":
    refresh()
