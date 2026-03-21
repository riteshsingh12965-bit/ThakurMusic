import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def clean_title(title):
    title = re.sub(r"\W+", " ", str(title))
    return title.strip().title()


async def get_thumb(videoid: str, title="Unknown Track"):
    try:
        videoid = str(videoid).split("v=")[-1].strip()
        path = f"{CACHE_DIR}/{videoid}_final.png"

        if os.path.exists(path):
            return path

        # 🔥 YOUTUBE THUMB
        thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
        thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return None
                async with aiofiles.open(thumb_path, "wb") as f:
                    await f.write(await resp.read())

        base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")

        # 🔥 STRONG BLUR BG (MATCH STYLE)
        bg = base.filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.55)

        draw = ImageDraw.Draw(bg)

        # 🔥 GLASS CARD (CENTER)
        card_w, card_h = 720, 400
        card_x = (1280 - card_w) // 2
        card_y = 160

        card = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 170))

        mask = Image.new("L", (card_w, card_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 45, fill=255)

        bg.paste(card, (card_x, card_y), mask)

        # 🔥 THUMB INSIDE CARD
        thumb = base.resize((520, 240))
        tmask = Image.new("L", thumb.size, 0)
        ImageDraw.Draw(tmask).rounded_rectangle((0, 0, 520, 240), 25, fill=255)

        thumb_x = card_x + (card_w - 520) // 2
        thumb_y = card_y + 30

        bg.paste(thumb, (thumb_x, thumb_y), tmask)

        # 🔥 FONT (CLEAN)
        try:
            title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 42)
            small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 24)
        except:
            title_font = small_font = ImageFont.load_default()

        title = clean_title(title)

        # 🔥 TEXT (MATCH POSITION)
        draw.text((card_x + 120, card_y + 290), title[:30], fill="black", font=title_font)
        draw.text((card_x + 120, card_y + 335), "YouTube Music", fill="black", font=small_font)

        # 🔥 PROGRESS BAR (EXACT STYLE)
        bar_x = card_x + 100
        bar_y = card_y + 370

        draw.line((bar_x, bar_y, bar_x + 420, bar_y), fill=(200, 200, 200), width=6)
        draw.line((bar_x, bar_y, bar_x + 200, bar_y), fill=(255, 0, 0), width=6)

        draw.ellipse((bar_x + 195, bar_y - 7, bar_x + 210, bar_y + 7), fill=(255, 0, 0))

        draw.text((bar_x, bar_y + 15), "00:00", fill="black", font=small_font)
        draw.text((bar_x + 360, bar_y + 15), "3:00", fill="black", font=small_font)

        # 🔥 PLAYER ICONS
        draw.text((card_x + 230, card_y + 410), "⏮  ▶  ⏸  ⏭", fill="black", font=small_font)

        # SAVE
        bg.save(path)

        try:
            os.remove(thumb_path)
        except:
            pass

        return path

    except Exception as e:
        print("THUMB ERROR:", e)
        return None
