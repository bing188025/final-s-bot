"""
Generate the welcome card background template image.
This creates a stadium-style background similar to the reference design.
Run this once to generate assets/background.png.
"""

from PIL import Image, ImageDraw, ImageFilter
import math


def create_stadium_background(width=550, height=300):
    """Create a stadium/field-style background with gradient and lighting."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)

    # Dark gradient background (top to bottom: dark green-brown to darker)
    for y in range(height):
        ratio = y / height
        r = int(30 + 20 * ratio)
        g = int(35 + 25 * (1 - ratio))
        b = int(15 + 10 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Add a green grass field at the bottom
    field_start = int(height * 0.55)
    for y in range(field_start, height):
        ratio = (y - field_start) / (height - field_start)
        r = int(30 + 40 * ratio)
        g = int(80 + 60 * (1 - ratio * 0.5))
        b = int(15 + 10 * ratio)
        alpha = int(200 + 55 * ratio)
        for x in range(width):
            existing = img.getpixel((x, y))
            blended_r = int(existing[0] * 0.3 + r * 0.7)
            blended_g = int(existing[1] * 0.3 + g * 0.7)
            blended_b = int(existing[2] * 0.3 + b * 0.7)
            img.putpixel((x, y), (blended_r, blended_g, blended_b, 255))

    # Add stadium light glow effects at the top
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Left and right stadium light pillars
    for cx, cy in [(width // 2, 20)]:
        for radius in range(120, 0, -1):
            alpha = int(15 * (1 - radius / 120))
            glow_draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=(255, 220, 150, alpha),
            )

    # Side glows (warm golden tones like stadium lights)
    for cx in [30, width - 30]:
        for radius in range(100, 0, -1):
            alpha = int(12 * (1 - radius / 100))
            glow_draw.ellipse(
                [cx - radius, 30 - radius, cx + radius, 30 + radius],
                fill=(255, 180, 80, alpha),
            )

    img = Image.alpha_composite(img, glow_layer)

    # Add subtle vignette (dark edges)
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette)
    cx, cy = width // 2, height // 2
    max_dist = math.sqrt(cx**2 + cy**2)
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            ratio = dist / max_dist
            alpha = int(min(120, 120 * (ratio**1.5)))
            vignette.putpixel((x, y), (0, 0, 0, alpha))

    img = Image.alpha_composite(img, vignette)

    # Add a subtle horizontal golden line across the middle area
    line_y = int(height * 0.52)
    line_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    line_draw = ImageDraw.Draw(line_layer)
    for x in range(20, width - 20):
        dist_from_center = abs(x - width // 2) / (width // 2)
        alpha = int(40 * (1 - dist_from_center))
        line_draw.point((x, line_y), fill=(200, 170, 80, alpha))
        line_draw.point((x, line_y + 1), fill=(200, 170, 80, alpha // 2))

    img = Image.alpha_composite(img, line_layer)

    # Add subtle top border glow (golden)
    for y in range(3):
        for x in range(width):
            alpha = int(80 * (1 - y / 3))
            existing = img.getpixel((x, y))
            img.putpixel(
                (x, y),
                (
                    min(255, existing[0] + 60),
                    min(255, existing[1] + 40),
                    existing[2],
                    255,
                ),
            )

    # Add bottom border glow
    for y in range(height - 3, height):
        for x in range(width):
            dist = height - y
            alpha = int(60 * (1 - dist / 3))
            existing = img.getpixel((x, y))
            img.putpixel(
                (x, y),
                (
                    min(255, existing[0] + 40),
                    min(255, existing[1] + 30),
                    existing[2],
                    255,
                ),
            )

    return img.convert("RGB")


if __name__ == "__main__":
    bg = create_stadium_background(550, 300)
    bg.save("assets/background.png", "PNG")
    print("Created assets/background.png")
