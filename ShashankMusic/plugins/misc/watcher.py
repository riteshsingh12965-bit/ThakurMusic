# -----------------------------------------------
# 🔸 ShashankMusic Project
# 🔹 Developed & Maintained by: Shashank Shukla (https://github.com/itzshukla)
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by ItzShukla
# -----------------------------------------------

from pyrogram import filters
from pyrogram.types import Message
from ShashankMusic import app
from ShashankMusic.core.call import Shashank
from ShashankMusic.utils.database import get_assistant

welcome = 20
close = 30


@app.on_message(filters.video_chat_started, group=welcome)
@app.on_message(filters.video_chat_ended, group=close)
async def welcome(_, message: Message):
    await Shashank.stop_stream_force(message.chat.id)


@app.on_message(filters.left_chat_member, group=69)
async def bot_kick(_, msg: Message):
    if msg.left_chat_member.id == app.id:
        ub = await get_assistant(msg.chat.id)
        try:
            await ub.leave_chat(msg.chat.id)
        except:
            pass