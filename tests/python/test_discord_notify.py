#!/usr/bin/env python3
"""Tests for scripts/discord_notify.py.

discord_notify.py runs in GitHub Actions on every push to main and every
published release. These tests cover payload formatting, Discord API edge cases
(omitting empty embed URLs, skipping draft releases, commit truncation, never
pinging users), secret redaction on network errors, and the CLI dry-run / unset
webhook paths without making network calls.

Run with: python3 -m unittest discover -s tests/python -v
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "discord_notify", REPO / "scripts" / "discord_notify.py"
)
assert SPEC and SPEC.loader
notify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = notify
SPEC.loader.exec_module(notify)


FAKE_FIELDS = [
    {"name": "Roadmap", "value": "10 / 20 tasks done (50%)", "inline": False},
    {"name": "Progress page", "value": "https://example.invalid/progress", "inline": False},
]


class TestClip(unittest.TestCase):
    def test_short_text_is_unchanged(self) -> None:
        self.assertEqual(notify.clip("hello", 10), "hello")
        self.assertEqual(notify.clip("hello", 5), "hello")

    def test_long_text_is_truncated_with_ellipsis(self) -> None:
        clipped = notify.clip("abcdefgh", 5)
        self.assertEqual(clipped, "abcd…")
        self.assertEqual(len(clipped), 5)


class TestPushMessage(unittest.TestCase):
    def test_empty_commits_returns_none(self) -> None:
        self.assertIsNone(notify.push_message({"commits": []}))
        self.assertIsNone(notify.push_message({}))

    @mock.patch.object(notify, "progress_fields", return_value=FAKE_FIELDS)
    def test_single_commit_formats_link_branch_and_no_pings(self, _fields: mock.Mock) -> None:
        event = {
            "ref": "refs/heads/main",
            "compare": "https://github.com/example/repo/compare/aaa...bbb",
            "commits": [
                {
                    "id": "abcdef1234567890",
                    "url": "https://github.com/example/repo/commit/abcdef1",
                    "message": "Add audio stub\n\nExtra body line",
                    "author": {"name": "Alice"},
                }
            ],
        }
        payload = notify.push_message(event)
        assert payload is not None
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        embed = payload["embeds"][0]
        self.assertEqual(embed["title"], "1 new commit to main")
        self.assertEqual(embed["url"], event["compare"])
        self.assertEqual(
            embed["description"],
            "[`abcdef1`](https://github.com/example/repo/commit/abcdef1) Add audio stub · Alice",
        )
        self.assertEqual(embed["color"], notify.GREEN)
        self.assertEqual(len(embed["fields"]), 2)

    @mock.patch.object(notify, "progress_fields", return_value=FAKE_FIELDS)
    def test_missing_urls_are_omitted_instead_of_empty_strings(self, _fields: mock.Mock) -> None:
        event = {
            "ref": "refs/heads/dev",
            "commits": [
                {"id": "1234567890", "message": "No commit URL"},
                {"message": "No sha or url"},
            ],
        }
        payload = notify.push_message(event)
        assert payload is not None
        embed = payload["embeds"][0]
        self.assertEqual(embed["title"], "2 new commits to dev")
        # Discord rejects embeds containing an empty string for "url".
        self.assertNotIn("url", embed)
        lines = embed["description"].splitlines()
        self.assertEqual(lines[0], "`1234567` No commit URL")
        self.assertEqual(lines[1], "No sha or url")

    @mock.patch.object(notify, "progress_fields", return_value=FAKE_FIELDS)
    def test_truncates_commit_list_beyond_max_commits(self, _fields: mock.Mock) -> None:
        commits = [
            {"id": f"{i:07d}", "message": f"Commit {i}"}
            for i in range(notify.MAX_COMMITS + 3)
        ]
        payload = notify.push_message({"ref": "refs/heads/main", "commits": commits})
        assert payload is not None
        lines = payload["embeds"][0]["description"].splitlines()
        self.assertEqual(len(lines), notify.MAX_COMMITS + 1)
        self.assertEqual(lines[-1], "…and 3 more")


class TestReleaseMessage(unittest.TestCase):
    def test_skips_non_published_actions_and_drafts(self) -> None:
        base = {"release": {"name": "v0.1.0", "html_url": "https://example.invalid/r"}}
        self.assertIsNone(notify.release_message({**base, "action": "edited"}))
        self.assertIsNone(notify.release_message({**base, "action": "created"}))
        self.assertIsNone(
            notify.release_message(
                {"action": "published", "release": {"name": "v0.1.0", "draft": True}}
            )
        )
        self.assertIsNone(notify.release_message({"action": "published"}))

    def test_published_release_uses_tag_fallback_and_omits_empty_url(self) -> None:
        payload = notify.release_message(
            {
                "action": "published",
                "release": {"tag_name": "v0.2.0", "body": ""},
            }
        )
        assert payload is not None
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        embed = payload["embeds"][0]
        self.assertEqual(embed["title"], "Release: v0.2.0")
        self.assertNotIn("url", embed)
        self.assertEqual(embed["description"], "See the release page for details.")
        self.assertEqual(embed["color"], notify.BLUE)

    def test_published_release_includes_url_and_clips_long_body(self) -> None:
        long_body = "x" * 2500
        payload = notify.release_message(
            {
                "action": "published",
                "release": {
                    "name": "Milestone 1",
                    "html_url": "https://github.com/example/repo/releases/tag/v0.1",
                    "body": long_body,
                },
            }
        )
        assert payload is not None
        embed = payload["embeds"][0]
        self.assertEqual(embed["url"], "https://github.com/example/repo/releases/tag/v0.1")
        self.assertEqual(len(embed["description"]), 2000)
        self.assertTrue(embed["description"].endswith("…"))


class TestSendAndCli(unittest.TestCase):
    def test_send_waits_for_discord_before_retrying_the_same_payload(self) -> None:
        url = "https://example.invalid/webhook"
        payload = {"content": "release"}
        for headers, body, delay in [
            ({"Retry-After": "2"}, b"rate limited", 2),
            ({}, b'{"retry_after":0.25}', 0.25),
        ]:
            with self.subTest(headers=headers):
                limited = urllib.error.HTTPError(url, 429, "Too Many Requests", headers, io.BytesIO(body))
                response = mock.MagicMock()
                response.__enter__.return_value.status = 204
                with mock.patch("urllib.request.urlopen", side_effect=[limited, response]) as http, \
                     mock.patch("time.sleep") as sleep:
                    notify.send(url, payload)
                sleep.assert_called_once_with(delay)
                self.assertEqual(http.call_count, 2)
                self.assertEqual([json.loads(call.args[0].data) for call in http.call_args_list],
                                 [payload, payload])

    def test_send_stops_after_repeated_rate_limits(self) -> None:
        url = "https://example.invalid/webhook"
        errors = [urllib.error.HTTPError(url, 429, "Too Many Requests", {"Retry-After": "1"},
                                         io.BytesIO(b"rate limited")) for _ in range(3)]
        with mock.patch("urllib.request.urlopen", side_effect=errors) as http, mock.patch("time.sleep") as sleep:
            with self.assertRaisesRegex(SystemExit, "HTTP 429"):
                notify.send(url, {})
        self.assertEqual(http.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(1)])

    def test_send_reports_unusable_or_long_delays_without_retrying(self) -> None:
        for body in (b'{}', b'null', b'not JSON', b'{"retry_after":false}', b'{"retry_after":-1}',
                     b'{"retry_after":3600}'):
            with self.subTest(body=body):
                url = "https://example.invalid/webhook"
                error = urllib.error.HTTPError(url, 429, "Too Many Requests", {}, io.BytesIO(body))
                with mock.patch("urllib.request.urlopen", side_effect=error) as http, mock.patch("time.sleep") as sleep:
                    with self.assertRaisesRegex(SystemExit, "HTTP 429"):
                        notify.send(url, {})
                http.assert_called_once()
                sleep.assert_not_called()

    def test_send_redacts_webhook_url_on_http_and_url_errors(self) -> None:
        secret = "https://discord.com/api/webhooks/12345/SUPER_SECRET_TOKEN"
        http_err = urllib.error.HTTPError(
            secret, 400, "Bad Request", {}, io.BytesIO(f"bad {secret}".encode("utf-8"))
        )
        with mock.patch("urllib.request.urlopen", side_effect=http_err):
            with self.assertRaises(SystemExit) as cm:
                notify.send(secret, {"embeds": []})
            self.assertNotIn("SUPER_SECRET_TOKEN", str(cm.exception))
            self.assertIn("<webhook>", str(cm.exception))

        url_err = urllib.error.URLError(f"failed connecting to {secret}")
        with mock.patch("urllib.request.urlopen", side_effect=url_err):
            with self.assertRaises(SystemExit) as cm:
                notify.send(secret, {"embeds": []})
            self.assertNotIn("SUPER_SECRET_TOKEN", str(cm.exception))
            self.assertIn("<webhook>", str(cm.exception))

    def test_main_dry_run_outputs_valid_json_without_network(self) -> None:
        event = {
            "action": "published",
            "release": {
                "name": "v0.1.0",
                "html_url": "https://github.com/example/repo/releases/tag/v0.1.0",
                "body": "Initial milestone.",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            buf = io.StringIO()
            with mock.patch.object(notify, "send") as mock_send:
                with contextlib.redirect_stdout(buf):
                    rc = notify.main(
                        ["--event", "release", "--event-path", str(event_path), "--dry-run"]
                    )
            self.assertEqual(rc, 0)
            mock_send.assert_not_called()
            parsed = json.loads(buf.getvalue())
            self.assertEqual(parsed["embeds"][0]["title"], "Release: v0.1.0")

    def test_main_skips_cleanly_when_webhook_env_unset(self) -> None:
        event = {
            "action": "published",
            "release": {"name": "v0.1.0", "body": "Notes"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            buf = io.StringIO()
            with mock.patch.object(notify.os, "environ", {}):
                with mock.patch.object(notify, "send") as mock_send:
                    with contextlib.redirect_stdout(buf):
                        rc = notify.main(
                            ["--event", "release", "--event-path", str(event_path)]
                        )
            self.assertEqual(rc, 0)
            mock_send.assert_not_called()
            self.assertIn("skipping", buf.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
