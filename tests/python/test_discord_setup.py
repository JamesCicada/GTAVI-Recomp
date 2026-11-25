"""Offline tests for the embeds posted by scripts/discord_setup.py."""

import importlib.util
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
