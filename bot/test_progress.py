import json
import time
import unittest
from unittest.mock import AsyncMock, MagicMock

import aiohttp

import cal_hampton as cal


def report(done):
    shaders = {"translated": 1, "total": 2}
    return json.dumps({
        "roadmap": {"done": done, "open": 1, "blocked": 0, "phases": []},
        "anyps5": {
            "commit": "1234567", "library_count": 1, "core_libraries": [],
            "libraries": {"done": 1, "total": 2}, "shaders": {"rdna2": shaders, "gfx1013": shaders},
        },
    })


class ProgressTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = cal.CalHampton(123)
        self.bot.session = MagicMock(spec=aiohttp.ClientSession)
        self.command = self.bot.tree.get_command("progress")
        self.interaction = MagicMock()
        self.interaction.response.defer = AsyncMock()
        self.interaction.followup.send = AsyncMock()
        self.response = self.bot.session.get.return_value.__aenter__.return_value
        self.response.raise_for_status = MagicMock()
        self.response.text = AsyncMock()
        self.addAsyncCleanup(self.bot.close)

    async def test_incomplete_first_response_finishes_the_deferred_reply(self):
        self.response.text.return_value = '{"roadmap": {}}'
        with self.assertLogs(cal.LOG, level="ERROR"):
            await self.command.callback(self.interaction)
        self.interaction.response.defer.assert_awaited_once_with(thinking=True)
        self.interaction.followup.send.assert_awaited_once()
        self.assertIn(cal.SITE_URL, self.interaction.followup.send.await_args.args[0])
        self.assertIsNone(self.bot.progress.value)

    async def test_refresh_keeps_previous_embed_and_recovers_on_next_request(self):
        self.response.text.side_effect = [report(1), "{}", report(2)]
        send = self.interaction.followup.send
        await self.command.callback(self.interaction)
        self.assertIn("1 / 2", send.await_args.kwargs["embed"].description)
        self.bot.progress.fetched = time.monotonic() - cal.CACHE_SECONDS - 1
        with self.assertLogs(cal.LOG, level="ERROR"):
            await self.command.callback(self.interaction)
        self.assertIn("1 / 2", send.await_args.kwargs["embed"].description)
        await self.command.callback(self.interaction)
        self.assertIn("2 / 3", send.await_args.kwargs["embed"].description)
