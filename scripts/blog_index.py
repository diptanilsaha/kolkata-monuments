#!/usr/bin/env python3
"""Further-reading links to Deepanjan Ghosh's Kolkata heritage blog,
double-dolphin.blogspot.com.

Only post titles and URLs are used; the writing stays on his site.

`blog_links.json` is the source of truth and every entry in it has been checked
by hand, because title similarity is not enough to establish that a post is
about a given building: the blog has a post on the Victoria Memorial in
*Lucknow*, one on Gillander House on *Clive Street*, and one on the Small Causes
Court on *Bankshall Street* — none of which are the Kolkata monuments whose
names they resemble.

Run this module directly to re-fetch the feed and propose candidates for any
monument that has no link yet; then add the good ones to blog_links.json.
"""
import json
import pathlib
import re
import time
import urllib.request

HERE = pathlib.Path(__file__).parent
CACHE = HERE / "cache"
LINKS = HERE / "blog_links.json"

FEED = ("https://double-dolphin.blogspot.com/feeds/posts/summary"
        "?alt=json&max-results=100&start-index={start}")
UA = {"User-Agent": "kolkata-monuments/1.0 (dataset build script)"}
CREDIT = "Deepanjan Ghosh — double-dolphin.blogspot.com"


def fetch_posts(refresh=False):
    dest = CACHE / "blog_posts.json"
    if dest.exists() and not refresh:
        return json.loads(dest.read_text())

    posts, start = [], 1
    while True:
        req = urllib.request.Request(FEED.format(start=start), headers=UA)
        feed = json.loads(urllib.request.urlopen(req, timeout=60).read())["feed"]
        entries = feed.get("entry", [])
        if not entries:
            break
        for entry in entries:
            posts.append({
                "title": entry["title"]["$t"],
                "url": next(l["href"] for l in entry["link"] if l["rel"] == "alternate"),
            })
        start += len(entries)
        total = int(feed.get("openSearch$totalResults", {}).get("$t", 0))
        if total and start > total:
            break
        time.sleep(0.5)

    CACHE.mkdir(exist_ok=True)
    dest.write_text(json.dumps(posts, indent=1, ensure_ascii=False))
    return posts


def load_links():
    """{qid: {title, url, credit}} for build_data.py."""
    if not LINKS.exists():
        return {}
    return {qid: {"title": v["title"], "url": v["url"], "credit": CREDIT}
            for qid, v in json.loads(LINKS.read_text()).items()}


# ───────────────────── candidate proposal (review aid) ─────────────────────

STOPWORDS = {"the", "of", "a", "an", "and", "in", "at", "to", "is", "was", "that",
             "kolkata", "calcutta", "forgotten", "history", "story", "part", "how",
             "why", "photo", "feature", "print"}


def keywords(text):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
            if len(w) > 2 and w not in STOPWORDS}


def propose(monuments, posts, already):
    """Monument names whose distinctive words all appear in a post title.
    These are candidates for a human to accept or reject, never a final answer."""
    indexed = [(keywords(p["title"]), p) for p in posts]
    for m in monuments:
        if m["id"] in already:
            continue
        want = keywords(m["name"])
        if len(want) < 2:
            continue
        for have, post in indexed:
            if want <= have:
                yield m, post
                break


if __name__ == "__main__":
    posts = fetch_posts()
    monuments = json.loads((HERE.parent / "monuments.json").read_text())
    already = load_links()
    print(f"{len(posts)} posts indexed, {len(already)} links already reviewed\n")
    print("Unreviewed candidates (check each before adding to blog_links.json):")
    found = False
    for monument, post in propose(monuments, posts, already):
        found = True
        print(f"  {monument['id']:<12} {monument['name']}\n"
              f"               -> {post['title']}\n"
              f"                  {post['url']}")
    if not found:
        print("  (none)")
