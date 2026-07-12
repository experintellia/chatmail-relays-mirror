#!/usr/bin/env python3
"""Extract chatmail relay hostnames from the rendered HTML of
https://chatmail.at/relays and emit the mirror's JSON snapshot.

This is a mechanical transformation, not curation: a relay entry is any
link (or heading) whose visible text is itself a bare DNS hostname. That
rule matches the relay list entries and never
matches decorative links (nav, docs, privacy, mailto, GitHub), whose text
is prose or a full URL. For links we additionally require the href's host
to equal the link text, so a stray hostname-looking label can't invent an
entry. When in doubt the parser drops a candidate rather than inventing
one — consumers apply their own reachability filtering anyway.

Output schema (pinned by downstream consumers — do not rename or
restructure existing fields; new OPTIONAL per-relay fields may be added):

    {
      "source": "https://chatmail.at/relays",
      "fetchedAt": "<ISO-8601 UTC>",
      "relays": [ { "host": "some.relay.example" }, ... ]
    }

Order follows the page; duplicates are removed (first occurrence wins).
Exits non-zero if no relays can be extracted, so the mirror workflow
fails loudly instead of publishing an empty list.

Stdlib only. Usage:
    parse_relays.py page.html [--fetched-at ISO8601] > relays.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit

SOURCE_URL = "https://chatmail.at/relays"

# Strict DNS hostname: lowercase dotted labels (LDH, no leading/trailing
# hyphen), at least two labels, letters-only TLD, no scheme/port/path.
HOSTNAME_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def normalize(text):
    """Lowercase and trim a candidate string; strip a trailing root dot."""
    return unescape(text).strip().lower().rstrip(".")


def is_hostname(text):
    return len(text) <= 253 and bool(HOSTNAME_RE.match(text))


class RelayExtractor(HTMLParser):
    """Collects text of <a> elements (with their href) and of headings."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.candidates = []  # (kind, text, href) in document order
        self._stack = []  # open (tag, href, text_parts)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            self._stack.append(("a", href, []))
        elif tag in HEADING_TAGS:
            self._stack.append((tag, None, []))

    def handle_endtag(self, tag):
        if not self._stack:
            return
        if tag == "a" or tag in HEADING_TAGS:
            open_tag, href, parts = self._stack.pop()
            kind = "a" if open_tag == "a" else "heading"
            self.candidates.append((kind, "".join(parts), href))

    def handle_data(self, data):
        for _, _, parts in self._stack:
            parts.append(data)


def extract_hosts(html):
    """Return relay hostnames from the page, in order, deduplicated."""
    parser = RelayExtractor()
    parser.feed(html)
    parser.close()

    hosts = []
    seen = set()
    for kind, text, href in parser.candidates:
        host = normalize(text)
        if not is_hostname(host):
            continue
        if kind == "a":
            # The entry's link must actually point at the named host;
            # otherwise drop it rather than invent an entry.
            url = urlsplit(href.strip())
            if url.scheme not in ("http", "https"):
                continue
            if (url.hostname or "").rstrip(".") != host:
                continue
        if host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def build_snapshot(html, fetched_at):
    hosts = extract_hosts(html)
    if not hosts:
        raise ValueError(
            "no relay hostnames extracted — refusing to produce an empty "
            "list (page layout may have changed)"
        )
    return {
        "source": SOURCE_URL,
        "fetchedAt": fetched_at,
        "relays": [{"host": h} for h in hosts],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html_file", help="path to the fetched relays page")
    ap.add_argument(
        "--fetched-at",
        default=None,
        help="ISO-8601 UTC fetch timestamp (default: now)",
    )
    args = ap.parse_args(argv)

    fetched_at = args.fetched_at or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    with open(args.html_file, encoding="utf-8", errors="replace") as f:
        html = f.read()

    try:
        snapshot = build_snapshot(html, fetched_at)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    json.dump(snapshot, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    print(f"extracted {len(snapshot['relays'])} relays", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
