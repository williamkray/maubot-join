from typing import Type

from maubot import MessageEvent, Plugin
from maubot.handlers import command, event
from mautrix.types import EventType, Membership, RoomAlias, StateEvent
from mautrix.types.event.state import CanonicalAliasStateEventContent, RoomNameStateEventContent
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
    @command.argument("room", required=False)
    async def join_base(self, evt: MessageEvent, room: RoomAlias = None) -> None:
        if room == "list":
            await self.join_list(evt)
            return
        
        if not room or room == "help":
            await evt.reply(
                (
                    "pass me a room alias or id (like #someroom:example.com or "
                    "!someRoomId:example.com) and i will try to join it, or use "
                    "!join list to see all rooms i'm in"
                )
            )
            return
        
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
        if room == "list":
            await evt.reply(
                "use !join list to see all rooms i'm in"
            )
            return
        
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

                    if room == evt.room_id:
                        await evt.reply(
                            (
                                "looks like you're asking me to leave THIS room. run that command from somewhere "
                                "else so i don't get stuck in a perpetual join-then-leave-again loop if you invite "
                                "me back (i might try to process old requests after joining), or just kick me out "
                                "normally if you have the power!"
                            )
                        )
                        return

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

    async def join_list(self, evt: MessageEvent) -> None:
        if not self.is_user_trustworthy(evt.sender):
            await evt.reply("you're not the boss of me!")
            return

        mymsg = None
        try:
            mymsg = await evt.respond("fetching rooms, give me a minute...")
            joined_rooms = await self.client.get_joined_rooms()

            if not joined_rooms:
                await evt.respond("i'm not in any rooms right now", edits=mymsg)
                return

            room_list = []
            for room_id in joined_rooms:
                room_info = f"`{room_id}`"
                
                # Try to get room name
                try:
                    name_content = await self.client.get_state_event(
                        room_id, EventType.ROOM_NAME, ""
                    )
                    if name_content:
                        if isinstance(name_content, RoomNameStateEventContent):
                            name = name_content.name
                        elif hasattr(name_content, "get"):
                            name = name_content.get("name")
                        else:
                            name = getattr(name_content, "name", None)
                        if name:
                            room_info += f" - {name}"
                except Exception:
                    # Room name not set or not accessible
                    pass

                # Try to get canonical alias
                try:
                    alias_content = await self.client.get_state_event(
                        room_id, EventType.ROOM_CANONICAL_ALIAS, ""
                    )
                    if alias_content:
                        if isinstance(alias_content, CanonicalAliasStateEventContent):
                            alias = alias_content.canonical_alias
                        elif hasattr(alias_content, "get"):
                            alias = alias_content.get("canonical_alias")
                        else:
                            alias = getattr(alias_content, "canonical_alias", None)
                        if alias:
                            room_info += f" ({alias})"
                except Exception:
                    # Canonical alias not set or not accessible
                    pass

                room_list.append(f"- {room_info}")

            response = f"i'm in {len(joined_rooms)} room(s):\n\n" + "\n".join(room_list)
            await evt.respond(response, edits=mymsg, markdown=True)
        except Exception as e:
            await evt.respond(
                f"i tried, but couldn't list rooms because: {e}", edits=mymsg
            )

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
