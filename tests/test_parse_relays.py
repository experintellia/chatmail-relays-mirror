"""Fixture-based tests for scripts/parse_relays.py.

The fixture is a verbatim copy of https://chatmail.at/relays as fetched
on 2026-07-12. If the page layout drifts and the parser needs updating,
refresh the fixture from the data branch (relays.html) and adjust the
expectations below.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.pardir, "scripts")
)

import parse_relays

FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "relays-2026-07-12.html"
)

EXPECTED_HOSTS = [
    "nine.testrun.org",
    "mehl.cloud",
    "mailchat.pl",
    "chatmail.woodpeckersnest.space",
    "chatmail.culturanerd.it",
    "chat.adminforge.de",
    "chika.aangat.lahat.computer",
    "tarpit.fun",
    "d.gaufr.es",
    "chtml.ca",
    "chatmail.au",
    "e2ee.wang",
    "chat.privittytech.com",
    "e2ee.im",
    "chatmail.email",
    "danneskjold.de",
    "chat.in-the.eu",
    "chat.nuvon.app",
    "nibblehole.com",
    "chat.zashm.org",
    "chat.sus.fr",
    "delta.thelab.uno",
    "chat.vim.wtf",
    "uninterest.ing",
    "sweetfern.net",
    "delta.disobey.net",
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
        html = '<a href="https://evil.example">nine.testrun.org</a>'
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
        self.assertIn({"host": "nine.testrun.org"}, snap["relays"])

    def test_empty_page_fails_loudly(self):
        with self.assertRaises(ValueError):
            parse_relays.build_snapshot("<html><body>nothing</body></html>", "x")


if __name__ == "__main__":
    unittest.main()
