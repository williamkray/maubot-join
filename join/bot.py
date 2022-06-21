from typing import Awaitable, Type, Optional, Tuple
import json
import time

from mautrix.client import Client
from mautrix.types import (Event, StateEvent, EventID, UserID, FileInfo, EventType,
                            RoomID, RoomAlias, ReactionEvent, RedactionEvent)
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command, event


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("admins")


class Join(Plugin):

    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()
        

    @command.new("join", help="tell me a room to join and i'll do my scientific best")
    @command.argument("room", required=True)
    async def join_that_room(self, evt: MessageEvent, room: str) -> None:
        if evt.sender in self.config["admins"]:
            try:
                await evt.respond(f"trying, give me a minute...")
                await self.client.join_room(room, max_retries=2)
                await evt.respond(f"i'm in!")
            except Exception as e:
                await evt.respond(f"i tried, but couldn't join because \"{e}\"")
        else:
            await evt.reply("you're not the boss of me!")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
