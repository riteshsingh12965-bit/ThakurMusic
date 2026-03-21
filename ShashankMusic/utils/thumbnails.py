import os
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from youtubesearchpython import VideosSearch  # ✅ FIXED
from config import YOUTUBE_IMG_URL
from ShrutiMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def trim(text, font, max_w):
    try:
        while font.getbbox(text)[2] > max_w:
            text = text[:-1]
        return text + "..."
    except:
        return text


async def gen_thumb(videoid: str, player_username=None):
    if player_username is None:
        player_username = getattr(app, "username", "MusicBot")

    path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(path):
        return path

    # 🔍 YT FETCH (same)
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        res = await results.next()
        data = res["result"][0]

        title = data.get("title", "Unknown")
        thumb_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration", "Live")
        views = data.get("viewCount", {}).get("short", "0")

    except:
        title, thumb_url, duration, views = "Unknown", YOUTUBE_IMG_URL, "Live", "0"

    thumb_path = f"{CACHE_DIR}/{videoid}.png"

    # ⬇ DOWNLOAD
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
                else:
                    raise Exception
    except:
        thumb_path = None

    # 🖤 BASE BG
    bg = Image.new("RGB", (1280, 720), (10, 10, 10))

    # 🔥 IMPROVED GLOW BG (SOFT + DEPTH)
    glow = Image.new("RGB", (1280, 720), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((150, 0, 1150, 720), fill=(255, 110, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    bg = Image.blend(bg, glow, 0.5)

    draw = ImageDraw.Draw(bg)

    # 🖼 THUMB (ENHANCED)
    try:
        thumb = Image.open(thumb_path).resize((420, 420)).convert("RGBA")

        # contrast + brightness boost
        thumb = ImageEnhance.Contrast(thumb).enhance(1.1)
        thumb = ImageEnhance.Brightness(thumb).enhance(1.05)

    except:
        thumb = Image.new("RGBA", (420, 420), (40, 40, 40, 255))

    mask = Image.new("L", (420, 420), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 420, 420), 40, fill=255)
    thumb.putalpha(mask)

    # 🔥 SOFTER SHADOW
    shadow = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, 460, 460), 50, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(70))
    bg.paste(shadow, (100, 130), shadow)

    # 🔥 CLEAN BORDER GLOW
    border = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 460, 460), 50, outline=(255, 130, 60), width=4)

    bg.paste(border.filter(ImageFilter.GaussianBlur(40)), (100, 130), border)
    bg.paste(border, (100, 130), border)
    bg.paste(thumb, (120, 150), thumb)

    # 🅵🅾🅽🆃 (same)
    try:
        title_font = ImageFont.truetype("ShrutiMusic/assets/font.ttf", 44)
        meta_font = ImageFont.truetype("ShrutiMusic/assets/font.ttf", 30)
        small_font = ImageFont.truetype("ShrutiMusic/assets/font.ttf", 26)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    # 🔴 BADGE
    draw.rounded_rectangle((600, 140, 830, 195), 25, fill=(255, 120, 40))
    draw.text((635, 152), "NOW PLAYING", fill="white", font=small_font)

    # 🎵 TITLE (SOFTER GLOW)
    title = trim(title, title_font, 550)
    draw.text((601, 241), title, fill=(255,140,70), font=title_font)
    draw.text((600, 240), title, fill="white", font=title_font)

    draw.line((600, 300, 1000, 300), fill=(255, 120, 40), width=3)

    # 📊 META (same)
    draw.text((600, 330), f"Duration: {duration}", fill="white", font=meta_font)
    draw.text((600, 370), f"Views: {views}", fill=(255, 150, 100), font=meta_font)
    draw.text((600, 410), f"Player: @{player_username}", fill=(255, 150, 100), font=meta_font)

    # 🎚 BAR (SMOOTHER)
    bar_x, bar_y = 600, 480
    bar_w = 500

    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+10), 6, fill=(60,60,60))
    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w//2, bar_y+10), 6, fill=(255,120,40))
    draw.ellipse((bar_x+bar_w//2-8, bar_y-5, bar_x+bar_w//2+8, bar_y+15), fill="white")

    draw.text((600, 510), "00:00", fill="white", font=small_font)
    draw.text((1080, 510), duration, fill="white", font=small_font)

    # 🔥 REFLECTION (SOFTER)
    reflection = bg.crop((0, 350, 1280, 720)).transpose(Image.FLIP_TOP_BOTTOM)
    reflection = reflection.filter(ImageFilter.GaussianBlur(40))

    fade = Image.new("L", reflection.size, 90)
    reflection.putalpha(fade)

    bg.paste(reflection, (0, 520), reflection)

    # 🔥 BRANDING (same)
    draw.text((820, 660), "Powered by Mr Thakur", fill=(255, 120, 40), font=small_font)

    try:
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path
