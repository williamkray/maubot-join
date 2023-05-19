from typing import Type

from mautrix.types import RoomAlias
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("admins")


class Join(Plugin):
    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

    @command.new("join", help="tell me a room to join and i'll do my scientific best")
    @command.argument("room", required=True)
    async def join_that_room(self, evt: MessageEvent, room: RoomAlias) -> None:
        if (room == "help") or len(room) == 0:
            await evt.reply(
                "pass me a room alias or id (like #someroom:example.com or !someRoomId:example.com) \
                            and i will try to join it"
            )
        else:
            if evt.sender in self.config["admins"]:
                try:
                    mymsg = await evt.respond(f"trying, give me a minute...")
                    self.log.info(mymsg)
                    await self.client.join_room(room, max_retries=2)
                    await evt.respond(f"i'm in!", edits=mymsg)
                except Exception as e:
                    await evt.respond(
                        f'i tried, but couldn\'t join because "{e}"', edits=mymsg
                    )
            else:
                await evt.reply("you're not the boss of me!")

    @command.new("part", help="tell me a room to leave and i'll do my scientific best")
    @command.argument("room", required=True)
    async def part_that_room(self, evt: MessageEvent, room: RoomAlias) -> None:
        if (room == "help") or len(room) == 0:
            await evt.reply(
                "pass me a room id or alias (like !someRoomId:server.tld or #someroomalias:example.com)\
                            and i will try to leave it"
            )
        else:
            if evt.sender in self.config["admins"]:
                if room.startswith("#"):
                    resolved = await self.client.resolve_room_alias(room)
                    room = resolved["room_id"]
                    self.log.debug(f"DEBUG: {room}")

                try:
                    mymsg = await evt.respond(f"trying, give me a minute...")
                    self.log.info(mymsg)
                    await self.client.leave_room(room)
                    await evt.respond(f"i'm out!", edits=mymsg)
                except Exception as e:
                    await evt.respond(
                        f'i tried, but couldn\'t leave because "{e}"', edits=mymsg
                    )
            else:
                await evt.reply("you're not the boss of me!")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
