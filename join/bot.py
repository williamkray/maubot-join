from typing import Final, Type

from maubot import MessageEvent, Plugin
from maubot.handlers import command, event
from mautrix.errors import MatrixRequestError
from mautrix.types import (EventID, EventType, Membership, RoomAlias, RoomID, StateEvent)
from mautrix.types.event.state import CanonicalAliasStateEventContent
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

SAFE_EXCEPTION: Final[str] = '***SAFE_EXCEPTION***'


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

    def is_command_for_me(self, evt: MessageEvent, everyone: bool = True) -> bool:
        mentions = evt.content.get('m.mentions', [])
        if mentions:
            return self.client.mxid in mentions['user_ids']
        return everyone

    def is_command_for_me_only(self, evt: MessageEvent) -> bool:
        return self.is_command_for_me(evt, False)

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

    async def get_room_alias(self, room_id: RoomID) -> RoomAlias | None:
        try:
            alias_event: CanonicalAliasStateEventContent = await self.client.get_state_event(
                room_id, EventType.ROOM_CANONICAL_ALIAS)
            if alias_event:
                return alias_event.canonical_alias
            else:
                return None
        except MatrixRequestError as e:
            self.log.exception(f"{SAFE_EXCEPTION} Failed to get alias for {room_id}: {e}")
            return None

    @command.new("list_rooms", help="Tell me all the rooms the bot has joined.")
    @command.argument("a_mention", required=True, pass_raw=True)
    async def list_rooms(self, evt: MessageEvent, a_mention: str) -> None:
        if not self.is_command_for_me_only(evt):
            return

        if self.is_user_trustworthy(evt.sender):
            event_id: EventID = EventID("")
            try:
                event_id = await evt.respond(f"I am checking the rooms, please give me a moment...")
                self.log.info(event_id)
                room_ids = await self.client.get_joined_rooms()
                rooms_alias = [(room_id, await self.get_room_alias(room_id)) for room_id in room_ids]
                rooms_alias.sort(key=lambda x: (x[1] is None, x[1]))
                rooms = []
                for room_id, alias in rooms_alias:
                    alias_info = f'\n\nAlias: {alias}' if alias else ""
                    line = f'Room ID: `{room_id}`{alias_info}'
                    rooms.append(line)

                rooms_list = '\n\n'.join(rooms)
                await evt.respond(f"I'm in the following rooms :\n\n{rooms_list}", markdown=True, edits=event_id)
            except Exception as e:
                self.log.exception(f"{SAFE_EXCEPTION} list_rooms {a_mention}: {e}", exc_info=e)
                await evt.respond(f"I couldn't check rooms because of :\n{e}", edits=event_id)
        else:
            await evt.reply(f"Please check with the admins({self.config['admins']}) to see which rooms I am in.")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
