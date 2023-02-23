# join bot

a really stupid simple maubot module that allows for only a designated list of users to get your maubot instance to join
another room.

the reason this exists is really because [this reature request](https://github.com/maubot/maubot/issues/110) exists but
is not implemented.

to use this, add this plugin as an instance under the bot user you'd like to restrict joining on. invite the bot to at
least one room while "autojoin" is enabled.

one you are in a room with your bot, you may disable "autojoin" in maubot to prevent it from joining any more rooms
automatically. use the `!join #someroom:example.com` command and your bot will go try to join that room.

if the room in question has restricted access (invite-only, space-membership is required, etc) you should try to meet
that criteria first, otherwise the bot will return the error.

also now including a `!part` command that will get your bot to leave a room by alias or ID! amazing!
