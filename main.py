import os
import json
import discord

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


class RoleReactClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.guild_id = None
        self.role_channel_id = None
        self.role_message_id = None
        self.role_message_text = None

        self.guild = None
        self.role_channel = None
        self.role_message = None

        self.role_dict = {}

    async def set_vars(self, message_data):
        self.guild_id = message_data["guild_id"]
        self.role_channel_id = message_data["channel_id"]
        self.role_message_id = message_data["message_id"]
        self.role_message_text = message_data["message_text"]
        self.guild = self.get_guild(self.guild_id)
        self.role_channel = self.get_channel(self.role_channel_id)
        self.role_message = await self.role_channel.fetch_message(self.role_message_id)

    async def on_ready(self):
        with open('message_data.json', 'r') as json_file:
            message_data = json.load(json_file)
            await self.set_vars(message_data)

    async def on_message(self, message):
        if message.content[0] == "!":
            cmd = message.content.split()
            print(cmd)
            if cmd[0] == "!reactionrole":
                msg = "React to this message to get your roles!"
                role_message = await message.channel.send(msg)
                message_data = {
                    "guild_id": role_message.guild.id,
                    "channel_id": role_message.channel.id,
                    "message_id": role_message.id,
                    "message_text": role_message.content
                }
                with open("message_data.json", "w") as outfile:
                    json.dump(message_data, outfile)
                await self.set_vars(message_data)

            if cmd[0] == "!addrole":
                emoji, txt = cmd[1], " ".join(cmd[2:])
                names = [role.name for role in self.guild.roles]
                if txt not in names and txt is not None:
                    await self.guild.create_role(name=txt)
                for role in self.guild.roles:
                    if txt == role.name:
                        self.role_dict[emoji] = role

                print(self.role_message_text)
                self.role_message_text += f"\n\t{emoji} - {txt} "
                message_data = {
                    "guild_id": self.guild_id,
                    "channel_id": self.role_channel_id,
                    "message_id": self.role_message_id,
                    "message_text": self.role_message_text
                }
                with open("message_data.json", "w") as outfile:
                    json.dump(message_data, outfile)

                await self.role_message.edit(content=self.role_message_text)
                await self.role_message.add_reaction(emoji)

    async def on_raw_reaction_add(self, payload):
        if payload.message_id == self.role_message_id:
            role = self.role_dict.get(str(payload.emoji))
            if payload.member != self.user:
                await payload.member.add_roles(role)

    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == self.role_message_id:
            member = await self.guild.fetch_member(payload.user_id)
            role = self.role_dict.get(str(payload.emoji))
            if role in member.roles:
                await member.remove_roles(role)


client = RoleReactClient()
client.run(TOKEN)
