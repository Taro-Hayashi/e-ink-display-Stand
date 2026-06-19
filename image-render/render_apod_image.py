#!/usr/bin/env python3
import os
import textwrap
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

WIDTH = 122
HEIGHT = 250
IMAGE_HEIGHT = 188
HEADER_HEIGHT = 15
FOOTER_HEIGHT = HEIGHT - IMAGE_HEIGHT


def load_font(size, bold=False):
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ) if bold else (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
    )

    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def normalize_title(title):
    title = " ".join((title or "NASA APOD").split())
    return title[:80]


def format_date(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value).strftime("%Y.%m.%d")
    except ValueError:
        return value


def load_apod_photo(path):
    if not path or not os.path.exists(path):
        return None
    try:
        return Image.open(path).convert("L")
    except Exception as e:
        print(f"Warning: failed to load APOD image: {e}")
        return None


def prepare_photo(image):
    image = ImageOps.exif_transpose(image)
    image = ImageOps.fit(image, (WIDTH, IMAGE_HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.45)
    image = ImageEnhance.Sharpness(image).enhance(1.4)
    image = image.filter(ImageFilter.SHARPEN)
    return image.convert("1", dither=Image.Dither.FLOYDSTEINBERG).convert("L")


def draw_placeholder(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill="white", outline="black")
    for offset in range(-80, 140, 18):
        draw.line((x0 + offset, y1, x0 + offset + 100, y0), fill="black")
    draw.ellipse((34, 60, 88, 114), outline="black", width=2)
    draw.ellipse((50, 77, 63, 90), fill="black")
    draw.text((26, 126), "RUN FETCH", fill="black", font=load_font(11, bold=True))
    draw.text((37, 141), "APOD", fill="red", font=load_font(13, bold=True))


def draw_wrapped_title(draw, title, y, font):
    words = normalize_title(title).split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= WIDTH - 8:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    if not lines:
        lines = ["NASA APOD"]

    for text in lines[:3]:
        draw.text((4, y), text, fill="black", font=font)
        y += 12
    return y


def short_credit(value):
    value = " ".join((value or "").split())
    if not value:
        return ""
    return textwrap.shorten(value, width=28, placeholder="...")


def render_apod_image(payload):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    header_font = load_font(10, bold=True)
    title_font = load_font(10, bold=True)
    small_font = load_font(8)

    draw.rectangle((0, 0, WIDTH, HEADER_HEIGHT - 1), fill="white")
    draw.text((3, 2), "NASA", fill="red", font=header_font)
    draw.text((35, 2), "APOD", fill="black", font=header_font)
    date_text = format_date(payload.get("date"))
    if date_text:
        bbox = draw.textbbox((0, 0), date_text, font=small_font)
        draw.text((WIDTH - (bbox[2] - bbox[0]) - 3, 4), date_text, fill="black", font=small_font)

    photo = load_apod_photo(payload.get("image_path"))
    photo_box = (0, HEADER_HEIGHT, WIDTH, HEADER_HEIGHT + IMAGE_HEIGHT)
    if photo:
        prepared = prepare_photo(photo)
        image.paste(Image.merge("RGB", (prepared, prepared, prepared)), photo_box[:2])
    else:
        draw_placeholder(draw, photo_box)

    footer_y = HEADER_HEIGHT + IMAGE_HEIGHT
    draw.rectangle((0, footer_y, WIDTH, HEIGHT), fill="white")
    draw.line((0, footer_y, WIDTH, footer_y), fill="black")
    next_y = draw_wrapped_title(draw, payload.get("title"), footer_y + 3, title_font)

    credit = short_credit(payload.get("copyright"))
    if credit and next_y <= HEIGHT - 18:
        draw.text((4, HEIGHT - 10), f"Credit: {credit}", fill="black", font=small_font)

    return image


def pack_plane(image, color):
    pixels = image.load()
    data = bytearray()
    for y in range(HEIGHT):
        byte = 0xFF
        bit = 7
        for x in range(WIDTH):
            r, g, b = pixels[x, y]
            if color == "black":
                on = r < 128 and g < 128 and b < 128
            else:
                on = r > 160 and g < 100 and b < 100
            if on:
                byte &= ~(1 << bit)
            bit -= 1
            if bit < 0:
                data.append(byte)
                byte = 0xFF
                bit = 7
        if bit != 7:
            data.append(byte)
    return bytes(data)


def render_apod_planes(payload):
    image = render_apod_image(payload)
    return pack_plane(image, "black") + pack_plane(image, "red")


def save_preview(payload, path):
    render_apod_image(payload).save(path)
