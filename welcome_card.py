"""
Generate a welcome card image with the new member's avatar centered.
"""

import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
BACKGROUND_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banner.jpg")

# Card dimensions
CARD_WIDTH = 550
CARD_HEIGHT = 300

# Avatar circle settings
AVATAR_SIZE = 110
AVATAR_BORDER = 4
AVATAR_CENTER_X = CARD_WIDTH // 2
AVATAR_CENTER_Y = 100

# Font paths (Windows)
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"


def make_circle_avatar(avatar_image: Image.Image, size: int) -> Image.Image:
    """Crop an avatar image into a circle with antialiasing."""
    # Resize at 4x for smooth edges, then downscale
    big_size = size * 4
    avatar = avatar_image.resize((big_size, big_size), Image.LANCZOS).convert("RGBA")

    mask = Image.new("L", (big_size, big_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, big_size - 1, big_size - 1], fill=255)

    avatar.putalpha(mask)
    return avatar.resize((size, size), Image.LANCZOS)


def create_welcome_card(
    username: str,
    avatar_bytes: bytes,
    member_count: int,
) -> io.BytesIO:
    """
    Create a welcome card image.

    Args:
        username: The display name of the new member.
        avatar_bytes: Raw bytes of the member's avatar image.
        member_count: The server's total member count.

    Returns:
        A BytesIO buffer containing the PNG image.
    """
    # Load background
    card = Image.open(BACKGROUND_PATH).convert("RGBA")
    card = card.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)

    # Load and process avatar
    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    circle_avatar = make_circle_avatar(avatar_img, AVATAR_SIZE)

    # Draw avatar border (a slightly larger circle behind the avatar)
    border_layer = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_layer)
    border_radius = AVATAR_SIZE // 2 + AVATAR_BORDER
    border_draw.ellipse(
        [
            AVATAR_CENTER_X - border_radius,
            AVATAR_CENTER_Y - border_radius,
            AVATAR_CENTER_X + border_radius,
            AVATAR_CENTER_Y + border_radius,
        ],
        fill=(40, 40, 40, 200),
        outline=(80, 80, 80, 150),
        width=2,
    )
    card = Image.alpha_composite(card, border_layer)

    # Paste circular avatar centered
    avatar_x = AVATAR_CENTER_X - AVATAR_SIZE // 2
    avatar_y = AVATAR_CENTER_Y - AVATAR_SIZE // 2
    card.paste(circle_avatar, (avatar_x, avatar_y), circle_avatar)

    # Draw text
    text_layer = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    # Main text: "username just joined the server!"
    try:
        font_main = ImageFont.truetype(FONT_BOLD, 20)
        font_sub = ImageFont.truetype(FONT_REGULAR, 14)
    except OSError:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    main_text = f"{username} just joined the server!"
    bbox = text_draw.textbbox((0, 0), main_text, font=font_main)
    text_w = bbox[2] - bbox[0]
    text_x = (CARD_WIDTH - text_w) // 2
    text_y = AVATAR_CENTER_Y + AVATAR_SIZE // 2 + 20

    # Text shadow
    text_draw.text((text_x + 1, text_y + 1), main_text, font=font_main, fill=(0, 0, 0, 150))
    # Main text
    text_draw.text((text_x, text_y), main_text, font=font_main, fill=(255, 255, 255, 255))

    # Sub text: "Member #XXXXX"
    sub_text = f"Member #{member_count}"
    bbox_sub = text_draw.textbbox((0, 0), sub_text, font=font_sub)
    sub_w = bbox_sub[2] - bbox_sub[0]
    sub_x = (CARD_WIDTH - sub_w) // 2
    sub_y = text_y + 30

    text_draw.text((sub_x + 1, sub_y + 1), sub_text, font=font_sub, fill=(0, 0, 0, 120))
    text_draw.text((sub_x, sub_y), sub_text, font=font_sub, fill=(200, 200, 200, 230))

    card = Image.alpha_composite(card, text_layer)

    # Convert to RGB and save to buffer
    final = card.convert("RGB")
    buffer = io.BytesIO()
    final.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    # Test with a placeholder avatar
    test_avatar = Image.new("RGB", (128, 128), (100, 50, 150))
    buf = io.BytesIO()
    test_avatar.save(buf, format="PNG")

    result = create_welcome_card("m1zz17", buf.getvalue(), 101589)
    with open("assets/test_welcome.png", "wb") as f:
        f.write(result.read())
    print("Test card saved to assets/test_welcome.png")
