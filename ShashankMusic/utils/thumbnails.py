import os
import re
import random

import aiofiles
import aiohttp

from PIL import Image, ImageEnhance, ImageOps

from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from ShashankMusic import app   # ✅ FIXED (BrandrdX → Shashank)
from config import YOUTUBE_IMG_URL


# ✅ Resize function safe
def changeImageSize(maxWidth, maxHeight, image):
    if image.size[0] == 0 or image.size[1] == 0:
        return image
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


# ✅ Title cleaner
def clear(text):
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 60:
            title += " " + word
    return title.strip()


# ✅ Main thumbnail function
async def get_thumb(videoid):
    os.makedirs("cache", exist_ok=True)

    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"

    try:
        results = VideosSearch(url, limit=1)
        data = await results.next()

        if not data["result"]:
            return YOUTUBE_IMG_URL

        result = data["result"][0]

        title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
        duration = result.get("duration", "Unknown")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        # ✅ Download thumbnail
        temp_path = f"cache/thumb_{videoid}.png"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL

                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(await resp.read())

        # ✅ Image processing
        colors = ["white", "red", "orange", "yellow", "green", "cyan", "blue", "violet", "pink"]
        border = random.choice(colors)

        youtube = Image.open(temp_path)
        image1 = changeImageSize(1280, 720, youtube)

        bg = ImageEnhance.Brightness(image1).enhance(1.1)
        bg = ImageEnhance.Contrast(bg).enhance(1.1)

        final = ImageOps.expand(bg, border=7, fill=border)
        final = changeImageSize(1280, 720, final)

        # ✅ Save final
        final_path = f"cache/{videoid}.png"
        final.save(final_path)

        # ✅ Cleanup
        try:
            os.remove(temp_path)
        except:
            pass

        return final_path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return YOUTUBE_IMG_URL
