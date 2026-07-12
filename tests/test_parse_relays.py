"""Fixture-based tests for scripts/parse_relays.py.

The fixture reproduces the exact HTML structure of https://chatmail.at/relays
(as of 2026-07-12), but every relay hostname is replaced with a fake one
under the RFC 2606-reserved .example TLD, so this repo's machinery carries
no copy of the real relay list — the data branch is the only place real
data lives. The fakes preserve the structural variety of the real page:
two relays sharing one <li>, single-character labels, hyphenated labels,
and deep subdomains.

If the page layout drifts and the parser needs updating, refresh the
structure from the data branch (relays.html), re-fake the hostnames, and
adjust the expectations below.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.pardir, "scripts")
)

import parse_relays

FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "relays-sample.html"
)

EXPECTED_HOSTS = [
    "nine.relay-a.example",
    "relay-b.example",
    "relay-c.example",
    "chatmail.relay-d.example",
    "chatmail.relay-e.example",
    "chat.relay-f.example",
    "chika.deeply.nested.example",
    "relay-g.example",
    "d.relay-h.example",
    "relay-i.example",
    "relay-j.example",
    "e2ee-k.example",
    "chat.relay-l.example",
    "e2ee-m.example",
    "relay-n.example",
    "relay-o.example",
    "chat.in-the-p.example",
    "chat.relay-q.example",
    "relay-r.example",
    "chat.relay-s.example",
    "chat.relay-t.example",
    "delta.relay-u.example",
    "chat.relay-v.example",
    "relay-w.example",
    "relay-x.example",
    "delta.relay-y.example",
]


def fixture_html():
    with open(FIXTURE, encoding="utf-8") as f:
        return f.read()


class TestExtractHosts(unittest.TestCase):
    def test_fixture_hosts_in_page_order(self):
        self.assertEqual(parse_relays.extract_hosts(fixture_html()), EXPECTED_HOSTS)

    def test_all_hosts_pass_validation(self):
        for host in parse_relays.extract_hosts(fixture_html()):
            self.assertTrue(parse_relays.is_hostname(host), host)

    def test_decorative_links_excluded(self):
        hosts = parse_relays.extract_hosts(fixture_html())
        self.assertNotIn("chatmail.at", hosts)
        self.assertNotIn("delta.chat", hosts)

    def test_deduplication(self):
        html = fixture_html() * 2
        self.assertEqual(parse_relays.extract_hosts(html), EXPECTED_HOSTS)

    def test_link_text_must_match_href_host(self):
        html = '<a href="https://evil.example">honest.relay.example</a>'
        self.assertEqual(parse_relays.extract_hosts(html), [])

    def test_non_hostname_text_ignored(self):
        html = '<a href="https://chatmail.at/doc/relay">documentation</a>'
        self.assertEqual(parse_relays.extract_hosts(html), [])

    def test_bare_hostname_heading_accepted(self):
        html = "<h3>relay.example.org</h3>"
        self.assertEqual(parse_relays.extract_hosts(html), ["relay.example.org"])


class TestSnapshot(unittest.TestCase):
    def test_schema(self):
        snap = parse_relays.build_snapshot(fixture_html(), "2026-07-12T00:00:00Z")
        self.assertEqual(snap["source"], "https://chatmail.at/relays")
        self.assertEqual(snap["fetchedAt"], "2026-07-12T00:00:00Z")
        self.assertEqual(snap["relays"], [{"host": h} for h in EXPECTED_HOSTS])

    def test_empty_page_fails_loudly(self):
        with self.assertRaises(ValueError):
            parse_relays.build_snapshot("<html><body>nothing</body></html>", "x")


if __name__ == "__main__":
    unittest.main()
