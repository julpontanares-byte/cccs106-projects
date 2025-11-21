"""create_icon.py

Simple helper to create a placeholder PNG icon for packaging.
Usage:
    pip install pillow
    python create_icon.py
This will write `icon.png` into the same folder.
"""

try:
    from PIL import Image, ImageDraw
except Exception:
    print("Pillow is required to run this script. Install it with: pip install pillow")
    raise


def make_icon(path="icon.png", size=256):
    # Create an RGBA image with a light-blue background
    img = Image.new("RGBA", (size, size), (240, 248, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw a sun (yellow circle)
    sun_bbox = (int(size * 0.08), int(size * 0.08), int(size * 0.48), int(size * 0.48))
    draw.ellipse(sun_bbox, fill=(255, 204, 0, 255))

    # Draw a simple cloud (three overlapping ellipses + rectangle)
    c1 = (int(size * 0.44), int(size * 0.46), int(size * 0.82), int(size * 0.72))
    c2 = (int(size * 0.34), int(size * 0.56), int(size * 0.72), int(size * 0.86))
    c3 = (int(size * 0.50), int(size * 0.60), int(size * 0.90), int(size * 0.88))
    draw.ellipse(c1, fill=(245, 245, 245, 255))
    draw.ellipse(c2, fill=(245, 245, 245, 255))
    draw.ellipse(c3, fill=(245, 245, 245, 255))
    # cloud base rectangle to smooth bottom
    draw.rectangle((int(size*0.34), int(size*0.72), int(size*0.90), int(size*0.88)), fill=(245,245,245,255))

    # Optional: draw a small raindrop for detail
    drop_x = int(size * 0.70)
    drop_y = int(size * 0.78)
    draw.ellipse((drop_x, drop_y, drop_x + int(size*0.06), drop_y + int(size*0.08)), fill=(135,206,235,255))

    img.save(path)
    print(f"Saved placeholder icon: {path}")


if __name__ == "__main__":
    make_icon()
