import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from py_yt import VideosSearch

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def safe_text(text: str) -> str:
    return text.encode("ascii", "ignore").decode()


def fit_text(text, font, max_width):
    while font.getlength(text) > max_width and len(text) > 0:
        text = text[:-1]
    return text


async def get_thumb(videoid: str) -> str:
    path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(path):
        return path

    # FETCH DATA
    try:
        data = (await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next())["result"][0]
        title = re.sub(r"\W+", " ", data["title"]).strip().title()
        thumb_url = data["thumbnails"][0]["url"]
    except:
        title = "Unknown Song"
        thumb_url = "https://i.imgur.com/4L0rZ7P.jpg"

    title = safe_text(title)

    # DOWNLOAD
    temp = f"{CACHE_DIR}/{videoid}.jpg"
    async with aiohttp.ClientSession() as session:
        async with session.get(thumb_url) as r:
            if r.status == 200:
                async with aiofiles.open(temp, "wb") as f:
                    await f.write(await r.read())

    # BACKGROUND
    base = Image.open(temp).resize((1280, 720)).convert("RGB")
    bg = base.filter(ImageFilter.GaussianBlur(25))
    bg = ImageEnhance.Brightness(bg).enhance(0.35)

    draw = ImageDraw.Draw(bg)

    # PANEL
    PANEL_W, PANEL_H = 860, 580
    PANEL_X = (1280 - PANEL_W)//2
    PANEL_Y = 70

    panel = Image.new("RGBA", (PANEL_W, PANEL_H), (20, 20, 20, 235))
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, PANEL_W, PANEL_H), 45, fill=255)
    bg.paste(panel, (PANEL_X, PANEL_Y), mask)

    # THUMB TOP
    TH_W, TH_H = 760, 360
    TH_X = PANEL_X + (PANEL_W - TH_W)//2
    TH_Y = PANEL_Y + 30

    thumb = base.resize((TH_W, TH_H))
    tmask = Image.new("L", (TH_W, TH_H), 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, TH_W, TH_H), 35, fill=255)
    bg.paste(thumb, (TH_X, TH_Y), tmask)

    # GOLD BORDER
    draw.rounded_rectangle(
        (TH_X, TH_Y, TH_X + TH_W, TH_Y + TH_H),
        radius=35,
        outline="#d4af37",
        width=5
    )

    # FONTS (BIG TITLE 🔥)
    try:
        font_big = ImageFont.truetype("ShashankMusic/assets/assets/font2.ttf", 90)
        font_small = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 30)
        font_time = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 24)
        control_font = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 50)
    except:
        font_big = font_small = font_time = control_font = ImageFont.load_default()

    # NOW PLAYING
    np = "Now Playing"
    np_w = font_small.getlength(np)
    draw.text(
        (PANEL_X + (PANEL_W - np_w)//2, TH_Y + TH_H + 20),
        np,
        fill="#aaaaaa",
        font=font_small
    )

    # 🔥 BIG TITLE (AADAT STYLE)
    text = title.upper()
    text = fit_text(text, font_big, 720)

    tw = font_big.getlength(text)

    # Shadow
    draw.text(
        (PANEL_X + (PANEL_W - tw)//2 + 3, TH_Y + TH_H + 75),
        text,
        fill="#000000",
        font=font_big
    )

    # Main text
    draw.text(
        (PANEL_X + (PANEL_W - tw)//2, TH_Y + TH_H + 70),
        text,
        fill="white",
        font=font_big
    )

    # PROGRESS BAR
    BAR_Y = TH_Y + TH_H + 170
    BAR_X = PANEL_X + 90
    BAR_W = PANEL_W - 180

    progress = BAR_W // 3

    draw.line((BAR_X, BAR_Y, BAR_X + BAR_W, BAR_Y), fill="#666", width=6)
    draw.line((BAR_X, BAR_Y, BAR_X + progress, BAR_Y), fill="#d4af37", width=6)

    draw.ellipse(
        (BAR_X + progress - 9, BAR_Y - 9, BAR_X + progress + 9, BAR_Y + 9),
        fill="white"
    )

    # TIME
    draw.text((BAR_X, BAR_Y + 15), "1:24", fill="#cccccc", font=font_time)
    draw.text((BAR_X + BAR_W - 60, BAR_Y + 15), "3:45", fill="#cccccc", font=font_time)

    # CONTROLS
    controls = "<<   ||   >>"
    cw = control_font.getlength(controls)

    draw.text(
        (PANEL_X + (PANEL_W - cw)//2, BAR_Y + 70),
        controls,
        fill="white",
        font=control_font
    )

    # SAVE
    bg.save(path)

    try:
        os.remove(temp)
    except:
        pass

    return path
