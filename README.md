# join bot
[![Chat on Matrix](https://img.shields.io/badge/chat_on_matrix-%23dev:mssj.me-green)](https://matrix.to/#/#dev:mssj.me)

a really stupid simple maubot module that allows for only a designated list of users to get your maubot instance to join
another room.

the reason this exists is really because [this reature request](https://github.com/maubot/maubot/issues/110) exists but
is not implemented.

to use this, add this plugin as an instance under the bot user you'd like to restrict joining on, add user IDs to the
admins list in the config, and disable autojoin on the bot instance. now, only people in the admin list are able to
invite your bot to rooms.

## Uses

invite or kick your bot like normal. if you're on the approved list of users, everything will "just work". if not, the
bot will reject invitations sent to it.

optionally, use the explicit commands. these are ideally done from some sort of "control room" for the bot.

you can use the `!join #someroom:example.com` command and your bot will go try to join that room, even if you are not a
member of it yourself. if the room in question has restricted access (invite-only, space-membership is required, etc)
try to have the bot meet that criteria first, otherwise the bot will return the error. this command supports both aliases
and room IDs.

use the `!part` command similarly to the `!join` command to get your bot to leave a room by alias or ID! amazing! if the
bot recognizes that the room you're trying to get it to leave is the same as the room that you've issued that command,
it will refuse. this is because if the bot rejoins that room later, it may attempt to reprocess commands sent before as
it syncs the room events, and get caught in a perpetual loop of joining and then immediately leaving. using a dedicated
room to execute `!join` and `!part` commands is strongly recommended.
