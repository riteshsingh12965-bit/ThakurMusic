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

import random
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from ShashankMusic import app
from ShashankMusic.core.call import Shashank
from ShashankMusic.utils import bot_sys_stats
from ShashankMusic.utils.decorators.language import language
from ShashankMusic.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL

SHASHANK_PIC = [
    "https://files.catbox.moe/9aif4j.jpg",
    "https://files.catbox.moe/edkdm2.jpg",
    "https://files.catbox.moe/jwwnbc.jpg",
    "https://files.catbox.moe/jwwnbc.jpg",
    "https://files.catbox.moe/3y5e6c.jpg",
    "https://files.catbox.moe/5wfpxe.jpg",
    "https://files.catbox.moe/5wfpxe.jpg",
    "https://files.catbox.moe/qhxsg2.jpg",
    "https://files.catbox.moe/5wfpxe.jpg",
    "https://files.catbox.moe/9aif4j.jpg",
    "https://files.catbox.moe/5wfpxe.jpg",
    "https://files.catbox.moe/jwwnbc.jpg"
]

@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    response = await message.reply_photo(
        photo=random.choice(SHASHANK_PIC),
        has_spoiler=True,
        caption=_["ping_1"].format(app.mention),
    )
    pytgping = await Shashank.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    await response.edit_text(
        _["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )
