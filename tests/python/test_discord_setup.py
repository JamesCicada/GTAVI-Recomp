"""Offline tests for the Discord setup script."""

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, call

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "discord_setup.py"
SPEC = importlib.util.spec_from_file_location("discord_setup", SCRIPT)
assert SPEC and SPEC.loader
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class TestEmbeds(unittest.TestCase):
    def test_exact_limit_and_paragraph_breaks(self):
        limit = setup.EMBED_LIMIT
        first = "a" * (limit - 3) + "\n\nb"
        embeds = setup.embeds_for(first + "\n\nend", "FAQ")
        self.assertEqual([e["description"] for e in embeds], [first, "end"])
        self.assertEqual([e["title"] for e in embeds], ["FAQ", None])

    def test_long_unbroken_paragraph_between_short_ones(self):
        limit = setup.EMBED_LIMIT
        paragraph = "x" * (2 * limit + 1)
        embeds = setup.embeds_for("intro\n\n" + paragraph + "\n\nend", "Rules")
        self.assertEqual([e["description"] for e in embeds],
                         ["intro", "x" * limit, "x" * limit, "x\n\nend"])

    def test_long_paragraph_preserves_words_and_line_breaks(self):
        paragraph = "one two\tthree\nfour " * 300
        embeds = setup.embeds_for(paragraph, "Welcome")
        parts = [e["description"] for e in embeds]
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(0 < len(p) <= setup.EMBED_LIMIT for p in parts))
        self.assertEqual("".join(parts), paragraph)
        for left, right in zip(parts, parts[1:]):
            self.assertTrue(left[-1].isspace() or right[0].isspace())


class TestWebhooks(unittest.TestCase):
    def test_apply_creates_once_and_keeps_the_existing_token_out_of_output(self):
        api = Mock()
        others = [
            {"type": 1, "name": "GTAVI-Recomp", "user": {"id": "someone-else"}},
            {"type": 1, "name": "GTAVI-Recomp"},
            {"type": 2, "name": "GTAVI-Recomp", "user": {"id": "bot"}},
            {"type": 1, "name": "other", "user": {"id": "bot"}},
        ]
        new = {"type": 1, "name": "GTAVI-Recomp", "user": {"id": "bot"}, "id": "1", "token": "fixture-token"}
        api.call.side_effect = [others, new, others + [new]]
        args = (api, "progress", {"id": "42"}, "bot", "DISCORD_WEBHOOK_PROGRESS")
        first, second = io.StringIO(), io.StringIO()
        with redirect_stdout(first):
            setup.setup_webhook(*args, apply=True)
        with redirect_stdout(second):
            setup.setup_webhook(*args, apply=True)
        path = "/channels/42/webhooks"
        self.assertEqual(api.call.call_args_list, [
            call("GET", path), call("POST", path, {"name": "GTAVI-Recomp"}), call("GET", path),
        ])
        self.assertIn("DISCORD_WEBHOOK_PROGRESS = https://discord.com/api/webhooks/1/fixture-token", first.getvalue())
        self.assertIn("already exists", second.getvalue())
        self.assertNotIn("fixture-token", second.getvalue())

    def test_plan_only_reads_existing_channels(self):
        api = Mock()
        api.call.return_value = []
        with redirect_stdout(io.StringIO()) as output:
            for channel in (None, {"id": "99"}):
                setup.setup_webhook(api, "announcements", channel, "bot", "DISCORD_WEBHOOK_ANNOUNCEMENTS", False)
        api.call.assert_called_once_with("GET", "/channels/99/webhooks")
        self.assertEqual(output.getvalue().count("+ webhook for #announcements"), 2)


if __name__ == "__main__":
    unittest.main()
