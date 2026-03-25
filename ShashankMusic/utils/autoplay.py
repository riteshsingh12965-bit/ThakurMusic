import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from youtubesearchpython import VideosSearch

# =========================
# AUTOPLAY MEMORY
# =========================
AUTO_PLAY_CHATS = set()
LAST_PLAYED = {}

def is_autoplay_enabled(chat_id: int) -> bool:
    return chat_id in AUTO_PLAY_CHATS

def enable_autoplay(chat_id: int):
    AUTO_PLAY_CHATS.add(chat_id)

def disable_autoplay(chat_id: int):
    AUTO_PLAY_CHATS.discard(chat_id)

def save_last_played(chat_id: int, title: str):
    LAST_PLAYED[chat_id] = title

def get_last_played(chat_id: int):
    return LAST_PLAYED.get(chat_id)

# =========================
# COMMAND: /autoplay on/off
# =========================
@Client.on_message(filters.command("autoplay") & filters.group)
async def autoplay_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Usage:\n\n`/autoplay on`\n`/autoplay off`"
        )

    mode = message.command[1].lower()
    chat_id = message.chat.id

    if mode == "on":
        enable_autoplay(chat_id)
        return await message.reply_text("✅ **AutoPlay Enabled**")

    elif mode == "off":
        disable_autoplay(chat_id)
        return await message.reply_text("❌ **AutoPlay Disabled**")

    else:
        return await message.reply_text(
            "❌ Usage:\n\n`/autoplay on`\n`/autoplay off`"
        )

# =========================
# YOUTUBE SEARCH
# =========================
async def get_related_song(query: str):
    try:
        search = VideosSearch(query, limit=5)
        results = search.result().get("result", [])

        if not results:
            return None

        for video in results:
            title = video.get("title")
            url = video.get("link")
            duration = video.get("duration", "Unknown")

            if title and url:
                return {
                    "title": title,
                    "url": url,
                    "duration": duration
                }

        return None
    except Exception as e:
        print(f"[AUTOPLAY SEARCH ERROR] {e}")
        return None

# =========================
# MAIN AUTOPLAY HANDLER
# =========================
async def run_autoplay(client, chat_id: int, play_func):
    """
    play_func should be:
    await play_func(chat_id, url, title)

    Example:
    await run_autoplay(app, chat_id, my_play_function)
    """
    try:
        if not is_autoplay_enabled(chat_id):
            return False

        last_song = get_last_played(chat_id)
        if not last_song:
            return False

        recommended = await get_related_song(last_song + " official audio")
        if not recommended:
            return False

        title = recommended["title"]
        url = recommended["url"]

        save_last_played(chat_id, title)

        await play_func(chat_id, url, title)

        try:
            await client.send_message(
                chat_id,
                f"🎵 **AutoPlay Started**\n\n"
                f"▶️ **Now Playing:** {title}"
            )
        except:
            pass

        return True

    except Exception as e:
        print(f"[AUTOPLAY RUN ERROR] {e}")
        return False
