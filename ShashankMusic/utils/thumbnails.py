import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from py_yt import VideosSearch
from ShashankMusic import app
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    return image.resize((int(widthRatio * image.size[0]), int(heightRatio * image.size[1])))


def truncate(text):
    text = unidecode(text)
    words = text.split()
    t1, t2 = "", ""
    for w in words:
        if len(t1 + w) < 30:
            t1 += " " + w
        elif len(t2 + w) < 30:
            t2 += " " + w
    return [t1.strip(), t2.strip()]


def crop_center_circle(img, size, border):
    img = img.resize((size - 2*border, size - 2*border))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, img.size[0], img.size[1]), fill=255)

    final = Image.new("RGBA", (size, size))
    final.paste(img, (border, border), mask)
    return final


async def get_thumb(videoid):

    final_path = f"{CACHE_DIR}/{videoid}_v4.png"
    if os.path.exists(final_path):
        return final_path

    # 🎯 DATA FETCH
    try:
        data = (await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next())["result"][0]

        title = unidecode(data.get("title", "Song"))
        title = re.sub(r"\W+", " ", title).title()

        duration = data.get("duration", "3:00")
        views = data.get("viewCount", {}).get("short", "0")
        channel = data.get("channel", {}).get("name", "Channel")

        thumbnail = data["thumbnails"][0]["url"].split("?")[0]

    except:
        title, duration, views, channel = "Shashank Music", "3:00", "0", "Channel"
        thumbnail = YOUTUBE_IMG_URL

    # 🎯 DOWNLOAD THUMB
    thumb_path = f"{CACHE_DIR}/{videoid}.png"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except:
        return YOUTUBE_IMG_URL

    try:
        youtube = Image.open(thumb_path)
    except:
        return YOUTUBE_IMG_URL

    # 🎯 BACKGROUND
    image = changeImageSize(1280, 720, youtube)
    bg = image.filter(ImageFilter.BoxBlur(20))
    bg = ImageEnhance.Brightness(bg).enhance(0.6)

    draw = ImageDraw.Draw(bg)

    # 🎯 FONT SAFE
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font3.ttf", 45)
        small_font = ImageFont.truetype("ShashankMusic/assets/font2.ttf", 30)
    except:
        title_font = small_font = ImageFont.load_default()

    # 🎯 CIRCLE THUMB
    circle = crop_center_circle(youtube, 400, 20)
    bg.paste(circle, (120, 160), circle)

    x = 565
    t1, t2 = truncate(title)

    draw.text((x, 180), t1, fill="white", font=title_font)
    draw.text((x, 230), t2, fill="white", font=title_font)

    draw.text((x, 320), f"{channel} | {views}", fill="white", font=small_font)

    # 🎯 PROGRESS BAR
    total = 580
    done = int(total * 0.6)

    draw.line((x, 380, x + done, 380), fill="red", width=9)
    draw.line((x + done, 380, x + total, 380), fill="white", width=8)

    draw.ellipse((x + done - 10, 370, x + done + 10, 390), fill="red")

    draw.text((x, 400), "00:00", fill="white", font=small_font)
    draw.text((1080, 400), duration, fill="white", font=small_font)

    # 🎯 ICONS SAFE
    try:
        icons = Image.open("ShashankMusic/assets/play_icons.png").resize((580, 62))
        bg.paste(icons, (x, 450), icons)
    except:
        pass

    # CLEANUP
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(final_path)
    return final_path
