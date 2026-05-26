# BanInBlacklistedChannels 2.0
## A simple bot to insta-ban spammers in Discord. Written in Python.

This code is used to run `BanInBlacklistedChannels#5518` in the [MeowHouse](https://dsc.gg/meowsmp) server. 

When it detects a user chatting in blacklisted channel(s) configured in the code, it will log the message content in the console, then ban the user.

<img width="326" height="57" alt="image" src="https://github.com/user-attachments/assets/89bc4b31-d378-48ff-bb14-97d5e404dc3e" />

## Why is this bot ?
Users whose accounts have been hacked usually try to spam the same messages across every channels they can chat. By exploiting this vulnerability, we can write a simple Python bot to watch a channel and catch spammers:
<img width="1028" height="686" alt="image" src="https://github.com/user-attachments/assets/ed4c9888-1b8c-43c4-b91b-df71139b54ea" />

## Getting started  
### Get Python 
Make sure you have the latest Python version installed on your computer. If not, install it.  
I recommend you to have Python 3.13+ installed.  
Once ready, open a terminal at the same directory as the bot files and install the required packages in `requirements.txt` using `pip`: `pip install -r requirements.txt`.
### Configuring
Open `bot.py` and start configuring:  
```py
# ==== CONFIG ====
botToken = ""
ChID = [123456789, 987654321]
reportChID = [12345654321, 65432123456]
actionReason = "gửi tin nhắn vào kênh lọc spam"
isLogOnlyMode = 0
# =================
```
`botToken` is where you fill in the bot token. Get it on the [Discord Developer Portal](https://discord.com/developers/applications/) and **keep this token secret**  
`chID` is which channel(s) you want BIBC to monitor.  
`reportChID` is where BIBC should send the report messages to.  
`actionReason` specify the reason to ban the user. This reason will show in the Audit Log.
`isLogOnlyMode` set this to `1` if you want to use `LogOnly` mode. Set this back to `0` to use `Enforced` mode.  
> [!NOTE]
> `LogOnly` (PolicyMode 1) will NOT ban the user who sent messages to `ChID`. It only logs the event to reportChID. Ideal to test the configuration.

### Run the bot.  
Execute `python3 bot.py` to run the bot.  
<img width="636" height="139" alt="{52933AA3-A8D9-4040-9B65-79437ACA10B6}" src="https://github.com/user-attachments/assets/25e4d74c-6bb3-47ac-ac6a-ca1f0af572b4" />  


### Slash Commands (NEW)
<img width="330" height="294" alt="{0A5C9D30-448B-4745-89A8-CCC9EF30D921}" src="https://github.com/user-attachments/assets/1e267a3f-7bb6-49a1-a821-e179446a3776" />  

## BIBC in action !
<img width="437" height="336" alt="{E6B6634F-3706-4C72-B841-D1B24480015F}" src="https://github.com/user-attachments/assets/2aceccea-a9b4-41ea-8182-d6688ec87d16" />  

*BIBC Event Log in `reportChID`*  




<img width="1267" height="170" alt="{D8436FF8-18DA-4CCA-B46E-5A57A54CA0D0}" src="https://github.com/user-attachments/assets/bb6f1d4c-f533-456d-9dea-80d273aedcbe" />  

*BIBC Event Log in console*  




<img width="765" height="132" alt="{384F2207-6474-432C-ADE7-7CCC61DE4CA0}" src="https://github.com/user-attachments/assets/ff775ed7-bcb3-4f05-8a97-35b9042214f6" />  

*BIBC Action in Server Audit Log*


## License
Copyright (c) 2026 MeowIce

Permission is granted to use, modify, and distribute this software for non-commercial purposes only.

Selling this software or any derivative works is prohibited without explicit written permission.

Removing or altering author credits is prohibited.
