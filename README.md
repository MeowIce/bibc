# BanInBlacklistedChannel
## A simple bot to insta-ban spammers in Discord. Written in Python.

This code is used to run `BanInBlacklistedChannel#5518` in the [MeowHouse](https://dsc.gg/meowsmp) server. 

When it detects a user chatting in blacklisted channel(s) configured in the code, it will log the message content in the console, then ban the user.

<img width="326" height="57" alt="image" src="https://github.com/user-attachments/assets/89bc4b31-d378-48ff-bb14-97d5e404dc3e" />

## Why is this bot ?
Users whose accounts have been hacked usually try to spam the same messages across every channels they can chat. By exploiting this vulnerability, we can write a simple Python bot to watch a channel and catch spammers:
<img width="1028" height="686" alt="image" src="https://github.com/user-attachments/assets/ed4c9888-1b8c-43c4-b91b-df71139b54ea" />

## Getting started
1. Make sure you have the latest Python version.
2. Install required packages in `requirements.txt` using `pip`: `pip install -r requirements.txt`.
3. Open `bot.py` and fill in your bot token, and the ID of the channel(s) you want the bot to watch.
4. Execute `python3 bot.py` to run the bot.
5. Now wait for spammer to trigger the trap.

## BIBC in action !
The below image shows a user who got his account hacked and started sending scam messsages. Once he sends a message the watched channel, the bot immediately ban him:
<img width="1018" height="742" alt="image" src="https://github.com/user-attachments/assets/3fc23f2b-9884-400d-aa51-eaf0ef7f3864" />
*Thanks Auttaja for logging the events*

## License
You can redistribute the codes, modify it to whatever you like, but not selling or making any profits out of it.
