from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from .constants import (
    AVATAR_SIZE,
    AVATAR_FONT_RATIO,
    AVATAR_TEXT_COLOR,
    AVATAR_COLORS,
    HEX_CHUNK_SIZE,
    HEX_CHUNK_STARTS,
)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(
        int(value[i : i + HEX_CHUNK_SIZE], 16)
        for i in HEX_CHUNK_STARTS
    )


def load_avatar_font(size):
    font_path = (
        Path(settings.BASE_DIR)
        / "static"
        / "fonts"
        / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
    )
    font_size = int(size * AVATAR_FONT_RATIO)
    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), font_size)
        except OSError:
            pass
    return ImageFont.load_default()


def generate_avatar_image(letter, bg_color):
    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), color=hex_to_rgb(bg_color))
    draw = ImageDraw.Draw(image)
    font = load_avatar_font(AVATAR_SIZE)

    text_bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((AVATAR_SIZE - text_width) / 2, (AVATAR_SIZE - text_height) / 2)

    draw.text(position, letter, fill=AVATAR_TEXT_COLOR, font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    filename = f"avatar_{uuid4().hex}.png"
    return ContentFile(buffer.getvalue(), name=filename)