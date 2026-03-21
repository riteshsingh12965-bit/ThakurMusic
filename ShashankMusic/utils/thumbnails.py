import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def clean_title(title):
    title = re.sub(r"\W+", " ", str(title))
    return title.title()


async def get_thumb(videoid: str, title="Music Playing"):
    try:
        videoid = str(videoid).split("v=")[-1].strip()
        path = f"{CACHE_DIR}/{videoid}_final.png"

        if os.path.exists(path):
            return path

        thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
        thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

        # download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return None
                async with aiofiles.open(thumb_path, "wb") as f:
                    await f.write(await resp.read())

        # base image
        base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")

        # blur background
        bg = base.filter(ImageFilter.GaussianBlur(25))
        bg = ImageEnhance.Brightness(bg).enhance(0.6)

        draw = ImageDraw.Draw(bg)

        # GLASS PANEL
        panel = Image.new("RGBA", (700, 400), (255, 255, 255, 140))
        mask = Image.new("L", (700, 400), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 700, 400), 40, fill=255)
        bg.paste(panel, (290, 160), mask)

        # THUMB IMAGE
        thumb = base.resize((500, 220))
        tmask = Image.new("L", thumb.size, 0)
        ImageDraw.Draw(tmask).rounded_rectangle((0, 0, 500, 220), 25, fill=255)
        bg.paste(thumb, (390, 190), tmask)

        # FONT
        try:
            title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 40)
            small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 24)
        except:
            title_font = small_font = ImageFont.load_default()

        title = clean_title(title)

        # TEXT
        draw.text((500, 430), title[:30], fill="black", font=title_font)
        draw.text((500, 480), "YouTube Music", fill="black", font=small_font)

        # PROGRESS BAR
        draw.line((480, 530, 850, 530), fill="gray", width=6)
        draw.line((480, 530, 650, 530), fill="red", width=6)
        draw.ellipse((645, 523, 660, 538), fill="red")

        draw.text((480, 550), "00:00", fill="black", font=small_font)
        draw.text((820, 550), "3:00", fill="black", font=small_font)

        # ICONS
        draw.text((560, 590), "⏮  ⏸  ▶  ⏭", fill="black", font=small_font)

        # SAVE
        bg.save(path)

        try:
            os.remove(thumb_path)
        except:
            pass

        return path

    except Exception as e:
        print(e)
        return None
