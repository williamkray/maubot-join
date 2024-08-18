from typing import Type

from maubot import MessageEvent, Plugin
from maubot.handlers import command, event
from mautrix.types import EventType, Membership, RoomAlias, StateEvent
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("admins")
        helper.copy("servers")


class Join(Plugin):
    def is_user_trustworthy(self, sender):
        return (
            sender in self.config["admins"]
            or sender.split(":", 1)[1] in self.config["servers"]
        )

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

    @event.on(EventType.ROOM_MEMBER)
    async def handle_invite(self, evt: StateEvent) -> None:
        # i'm allergic to and statements
        if evt.state_key == self.client.mxid:
            if evt.content.membership == Membership.INVITE:
                if self.is_user_trustworthy(evt.sender):
                    await self.client.join_room(evt.room_id)
                else:
                    await self.client.leave_room(evt.room_id)

    @command.new("join", help="tell me a room to join and i'll do my scientific best")
    @command.argument("room", required=True)
    async def join_that_room(self, evt: MessageEvent, room: RoomAlias) -> None:
        if (room == "help") or len(room) == 0:
            await evt.reply(
                (
                    "pass me a room alias or id (like #someroom:example.com or "
                    "!someRoomId:example.com) and i will try to join it"
                )
            )
        else:
            if self.is_user_trustworthy(evt.sender):
                try:
                    mymsg = await evt.respond("trying, give me a minute...")
                    self.log.info(mymsg)
                    await self.client.join_room(room, max_retries=2)
                    await evt.respond("i'm in!", edits=mymsg)
                except Exception as e:
                    await evt.respond(
                        f"i tried, but couldn't join because: {e}", edits=mymsg
                    )
            else:
                await evt.reply("you're not the boss of me!")

    @command.new("part", help="tell me a room to leave and i'll do my scientific best")
    @command.argument("room", required=True)
    async def part_that_room(self, evt: MessageEvent, room: RoomAlias) -> None:
        if (room == "help") or len(room) == 0:
            await evt.reply(
                (
                    "pass me a room id or alias (like !someRoomId:server.tld or "
                    "#someroomalias:example.com) and i will try to leave it"
                )
            )
        else:
            self.log.debug(f"DEBUG sender is: {evt.sender}")
            self.log.debug(
                f"DEBUG trustworthy is: {self.is_user_trustworthy(evt.sender)}"
            )
            if self.is_user_trustworthy(evt.sender):
                if room.startswith("#"):
                    resolved = await self.client.resolve_room_alias(room)
                    room = resolved["room_id"]
                    self.log.debug(f"DEBUG: {room}")

                try:
                    mymsg = await evt.respond("trying, give me a minute...")
                    self.log.info(mymsg)
                    await self.client.leave_room(room)
                    await evt.respond("i'm out!", edits=mymsg)
                except Exception as e:
                    await evt.respond(
                        f"i tried, but couldn't leave because: {e}", edits=mymsg
                    )
            else:
                await evt.reply("you're not the boss of me!")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
