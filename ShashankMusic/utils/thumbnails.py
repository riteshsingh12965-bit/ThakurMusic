import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "font.ttf"))


# =========================
# SAFE TEXT
# =========================
def safe_text(text, default="Unknown Song"):
    if text is None:
        return default
    text = str(text).strip()
    return text if text else default


def trim(text, font, max_w):
    text = safe_text(text)
    try:
        while font.getbbox(text)[2] > max_w and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


# =========================
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "0")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"

    # If cached final thumb exists
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    # -------------------------
    # Download thumbnail
    # -------------------------
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_file, "wb") as f:
                        await f.write(await r.read())
                else:
                    thumb_file = None
    except:
        thumb_file = None

    # -------------------------
    # Load original image
    # -------------------------
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumb")
    except:
        original = Image.new("RGB", (1280, 720), (35, 35, 35))

    # =========================
    # BACKGROUND
    # =========================
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(22))
    bg = bg.convert("RGBA")

    dark_overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 145))
    bg = Image.alpha_composite(bg, dark_overlay)

    # warm glow
    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((180, 120, 1100, 690), fill=(255, 160, 90, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # CENTER PLAYER CARD
    # =========================
    card_x, card_y = 290, 80
    card_w, card_h = 700, 560

    # shadow
    shadow = Image.new("RGBA", (card_w + 40, card_h + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 40, card_h + 40), 65, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    bg.paste(shadow, (card_x - 20, card_y - 10), shadow)

    # card
    card = Image.new("RGBA", (card_w, card_h), (18, 18, 20, 240))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 55, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # =========================
    # TOP PREVIEW IMAGE
    # =========================
    preview = original.convert("RGBA").resize((610, 265))
    preview_mask = Image.new("L", (610, 265), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 610, 265), 35, fill=255)
    preview.putalpha(preview_mask)

    # border
    border = Image.new("RGBA", (618, 273), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 618, 273), 38, outline=(225, 185, 120), width=4)

    bg.paste(border, (331, 97), border)
    bg.paste(preview, (335, 101), preview)

    # =========================
    # FONTS
    # =========================
    try:
        small_font = ImageFont.truetype(FONT, 24)
        med_font = ImageFont.truetype(FONT, 32)
        title_font = ImageFont.truetype(FONT, 44)
        time_font = ImageFont.truetype(FONT, 26)
        button_font = ImageFont.truetype(FONT, 44)
        badge_font = ImageFont.truetype(FONT, 26)
    except:
        small_font = ImageFont.load_default()
        med_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
        button_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # =========================
    # TEXT
    # =========================
    title = trim(title, title_font, 520)

    # now playing
    draw.text((640, 395), "Now Playing", fill=(210, 210, 210), font=med_font, anchor="mm")

    # title
    draw.text((640, 455), title, fill="white", font=title_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 380
    bar_x2 = 910
    bar_y = 530

    # base
    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 8), 10, fill=(110, 110, 110))

    # progress fill
    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 8), 10, fill=(225, 185, 120))

    # knob
    draw.ellipse((prog_x - 10, bar_y - 8, prog_x + 10, bar_y + 12), fill="white")

    # time
    draw.text((380, 565), "1:24", fill=(170, 170, 170), font=time_font)
    draw.text((875, 565), duration, fill=(170, 170, 170), font=time_font)

    # =========================
    # PLAYER BUTTONS
    # =========================
    # Use text buttons instead of emoji (emoji square issue fix)
    draw.text((520, 625), "<<", fill="white", font=button_font, anchor="mm")

    draw.rounded_rectangle((610, 575, 720, 675), 28, fill=(55, 55, 60))
    draw.text((665, 625), "II", fill="white", font=button_font, anchor="mm")

    draw.text((785, 625), ">>", fill="white", font=button_font, anchor="mm")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=95)

    # cleanup
    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
