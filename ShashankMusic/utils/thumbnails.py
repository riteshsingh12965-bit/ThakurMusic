import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from unidecode import unidecode
from py_yt import VideosSearch
from VaishuMusic import app
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


# =========================
# HELPERS
# =========================
def changeImageSize(maxWidth, maxHeight, image):
    return ImageOps.fit(image, (maxWidth, maxHeight), method=Image.LANCZOS)


def safe_text(text, default="Unknown Song"):
    if text is None:
        return default
    text = str(text).strip()
    return text if text else default


def trim_text(text, font, max_width):
    text = safe_text(text)
    try:
        while font.getbbox(text)[2] > max_width and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


def format_views(views):
    try:
        v = str(views).replace(",", "").replace("views", "").strip()
        if not v:
            return "0 views"
        return f"{v} views" if "views" not in str(views).lower() else str(views)
    except:
        return "0 views"


def crop_center_circle(img, output_size=260, border=12):
    img = ImageOps.fit(img, (output_size - border * 2, output_size - border * 2), method=Image.LANCZOS)

    mask = Image.new("L", (output_size - border * 2, output_size - border * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, output_size - border * 2, output_size - border * 2), fill=255)

    final_img = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))

    # white border ring
    ring = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((0, 0, output_size - 1, output_size - 1), fill=(255, 255, 255, 255))
    final_img.paste(ring, (0, 0), ring)

    final_img.paste(img, (border, border), mask)
    return final_img


# =========================
# ICON DRAW
# =========================
def draw_prev(draw, x, y, color="white"):
    draw.polygon([(x+26, y), (x, y+18), (x+26, y+36)], fill=color)
    draw.rectangle((x+31, y, x+37, y+36), fill=color)


def draw_play(draw, x, y, color=(25, 25, 25)):
    draw.polygon([(x, y), (x, y+34), (x+28, y+17)], fill=color)


def draw_next(draw, x, y, color="white"):
    draw.polygon([(x, y), (x+26, y+18), (x, y+36)], fill=color)
    draw.rectangle((x+31, y, x+37, y+36), fill=color)


def draw_shuffle(draw, x, y, color="white", width=4):
    draw.arc((x, y, x+32, y+22), start=200, end=340, fill=color, width=width)
    draw.arc((x, y+16, x+32, y+38), start=20, end=160, fill=color, width=width)
    draw.polygon([(x+30, y+3), (x+42, y+5), (x+34, y+15)], fill=color)
    draw.polygon([(x+5, y+26), (x-5, y+35), (x+8, y+37)], fill=color)


def draw_repeat(draw, x, y, color="white", width=4):
    draw.arc((x, y, x+36, y+28), start=210, end=20, fill=color, width=width)
    draw.arc((x+4, y+10, x+40, y+38), start=30, end=200, fill=color, width=width)
    draw.polygon([(x+31, y+2), (x+44, y+4), (x+35, y+14)], fill=color)
    draw.polygon([(x+8, y+24), (x-2, y+34), (x+10, y+36)], fill=color)


# =========================
# MAIN
# =========================
async def get_thumb(videoid):
    final_path = f"{CACHE_DIR}/{videoid}_v4.png"

    if os.path.isfile(final_path):
        return final_path

    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)

    title = "Unknown Song"
    duration = "0:00"
    thumbnail = None
    views = "0"
    channel = "YouTube"

    try:
        data = await results.next()
        result = data["result"][0]

        title = safe_text(result.get("title"), "Unknown Song")
        title = re.sub(r"\s+", " ", title).strip()

        duration = safe_text(result.get("duration"), "0:00")

        try:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        except:
            thumbnail = None

        try:
            views = result["viewCount"]["short"]
        except:
            views = "0"

        try:
            channel = result["channel"]["name"]
        except:
            channel = "YouTube"

    except:
        pass

    thumb_temp = f"{CACHE_DIR}/thumb_{videoid}.jpg"

    # -------------------------
    # DOWNLOAD THUMB
    # -------------------------
    try:
        if thumbnail:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(thumb_temp, mode="wb") as f:
                            await f.write(await resp.read())
    except:
        pass

    # -------------------------
    # LOAD IMAGE
    # -------------------------
    try:
        youtube = Image.open(thumb_temp).convert("RGB")
    except:
        youtube = Image.new("RGB", (1280, 720), (30, 30, 30))

    original = changeImageSize(1280, 720, youtube)

    # =========================
    # BACKGROUND = SAME SONG THUMB BLUR
    # =========================
    background = original.copy().filter(ImageFilter.GaussianBlur(28))
    background = ImageEnhance.Brightness(background).enhance(0.38)
    background = ImageEnhance.Color(background).enhance(1.0)
    background = background.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 105))
    background = Image.alpha_composite(background, dark)

    # soft center glow
    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((120, 100, 1160, 640), fill=(255, 255, 255, 16))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    background = Image.alpha_composite(background, glow)

    draw = ImageDraw.Draw(background)

    # =========================
    # GLASS CARD
    # =========================
    card_x, card_y = 70, 165
    card_w, card_h = 1080, 290

    shadow = Image.new("RGBA", (card_w + 80, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 80, card_h + 80), 34, fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    background.paste(shadow, (card_x - 40, card_y - 20), shadow)

    card_crop = background.crop((card_x, card_y, card_x + card_w, card_y + card_h)).filter(ImageFilter.GaussianBlur(6))
    glass = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 12))
    card_crop = Image.alpha_composite(card_crop.convert("RGBA"), glass)

    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 30, fill=255)
    background.paste(card_crop, (card_x, card_y), mask)

    border = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, card_w - 1, card_h - 1), 30, outline=(255, 255, 255, 55), width=2)
    background.paste(border, (card_x, card_y), border)

    # =========================
    # FONTS
    # =========================
    try:
        title_font = ImageFont.truetype("VaishuMusic/assets/font3.ttf", 28)
        meta_font = ImageFont.truetype("VaishuMusic/assets/font2.ttf", 18)
        time_font = ImageFont.truetype("VaishuMusic/assets/font2.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()
        time_font = ImageFont.load_default()

    # =========================
    # ROUND THUMB
    # =========================
    circle_thumbnail = crop_center_circle(youtube, output_size=230, border=10)

    # soft glow around album
    album_glow = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ag = ImageDraw.Draw(album_glow)
    ag.ellipse((25, 25, 275, 275), fill=(255, 255, 255, 35))
    album_glow = album_glow.filter(ImageFilter.GaussianBlur(20))

    thumb_x = 115
    thumb_y = 195
    background.paste(album_glow, (thumb_x - 35, thumb_y - 35), album_glow)
    background.paste(circle_thumbnail, (thumb_x, thumb_y), circle_thumbnail)

    # =========================
    # TEXT
    # =========================
    text_x = 530
    title = trim_text(title, title_font, 560)

    draw.text((text_x, 220), title, fill=(255, 255, 255), font=title_font)
    draw.text((text_x, 282), f"{channel} | {format_views(views)}", fill=(235, 235, 235), font=meta_font)

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = text_x
    bar_x2 = 1040
    bar_y = 335

    progress = 0.58
    duration_clean = duration if duration and duration != "Unknown Mins" else "0:00"

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 7), 8, fill=(255, 255, 255))
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 7), 8, fill=(255, 0, 0))
    draw.ellipse((prog_x - 9, bar_y - 8, prog_x + 9, bar_y + 10), fill=(255, 0, 0))

    draw.text((bar_x1, 365), "00:00", fill=(255, 255, 255), font=time_font)
    draw.text((1000, 365), duration_clean, fill=(255, 255, 255), font=time_font)

    # =========================
    # BUTTONS
    # =========================
    controls_y = 400

    draw_shuffle(draw, 540, controls_y, color="white")
    draw_prev(draw, 670, controls_y + 2, color="white")

    # center play button
    draw.ellipse((780, 385, 860, 465), fill=(255, 255, 255, 245))
    draw_play(draw, 810, 408, color=(25, 25, 25))

    draw_next(draw, 925, controls_y + 2, color="white")
    draw_repeat(draw, 1035, controls_y, color="white")

    # =========================
    # SAVE
    # =========================
    background = background.convert("RGB")
    background.save(final_path, quality=98)

    try:
        if os.path.exists(thumb_temp):
            os.remove(thumb_temp)
    except:
        pass

    return final_path
