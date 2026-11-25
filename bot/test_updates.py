import unittest
from unittest.mock import MagicMock

import discord

import cal_hampton as cal


class UpdatesTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = cal.CalHampton(123)
        self.command = self.bot.tree.get_command("updates")
        self.interaction = MagicMock(spec=discord.Interaction)
        self.interaction.response = MagicMock(spec=discord.InteractionResponse)
        self.member = MagicMock(spec=discord.Member)
        self.interaction.user = self.member
        self.role = MagicMock(spec=discord.Role)
        self.role.name = cal.UPDATES_ROLE
        self.interaction.guild.roles = [self.role]

    async def asyncTearDown(self):
        await self.bot.close()

    async def test_toggle_acknowledges_privately_before_changing_role(self):
        async def check_ack(role, *, reason):
            self.interaction.response.defer.assert_awaited_once_with(ephemeral=True, thinking=True)
            self.interaction.edit_original_response.assert_not_awaited()

        for subscribed in (False, True):
            with self.subTest(subscribed=subscribed):
                self.interaction.reset_mock()
                self.member.roles = [self.role] if subscribed else []
                self.member.add_roles.side_effect = self.member.remove_roles.side_effect = check_ack
                await self.command.callback(self.interaction)
                changed = self.member.remove_roles if subscribed else self.member.add_roles
                untouched = self.member.add_roles if subscribed else self.member.remove_roles
                changed.assert_awaited_once_with(self.role, reason="/updates")
                untouched.assert_not_awaited()
                self.interaction.edit_original_response.assert_awaited_once()
                content = self.interaction.edit_original_response.await_args.kwargs["content"]
                self.assertIn("won't be pinged" if subscribed else "you'll be pinged", content)

    async def test_permission_error_updates_the_private_reply(self):
        self.member.roles = []
        self.member.add_roles.side_effect = discord.Forbidden(
            MagicMock(status=403, reason="Forbidden"), "Missing permissions"
        )
        with self.assertLogs(cal.LOG, level="WARNING"):
            await self.command.callback(self.interaction)
        self.interaction.response.defer.assert_awaited_once_with(ephemeral=True, thinking=True)
        self.interaction.edit_original_response.assert_awaited_once()
        self.assertIn("moderator", self.interaction.edit_original_response.await_args.kwargs["content"])

    async def test_missing_role_replies_immediately(self):
        self.interaction.guild.roles = []
        await self.command.callback(self.interaction)
        self.interaction.response.send_message.assert_awaited_once()
        self.assertTrue(self.interaction.response.send_message.await_args.kwargs["ephemeral"])
        self.interaction.response.defer.assert_not_awaited()
        self.member.add_roles.assert_not_awaited()
        self.member.remove_roles.assert_not_awaited()
