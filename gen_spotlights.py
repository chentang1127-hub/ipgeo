"""Generate 3 spotlight card images for RapidAPI Hub."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(__file__)
W, H = 500, 280
BG = (15, 18, 25)  # dark theme

sprites = [
    {
        "name": "spotlight-security",
        "color": (59, 130, 246),  # blue
        "icon": "🛡️",
        "title": "Security on every plan",
        "desc": "VPN, proxy, Tor, hosting detection — even on free",
    },
    {
        "name": "spotlight-free",
        "color": (34, 197, 94),  # green
        "icon": "🎁",
        "title": "10K free lookups/month",
        "desc": "Enough for PoC. No credit card tricks.",
    },
    {
        "name": "spotlight-maxmind",
        "color": (168, 85, 247),  # purple
        "icon": "🌐",
        "title": "MaxMind data engine",
        "desc": "Trusted by Cloudflare, npm, and Cisco",
    },
]

for s in sprites:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # accent bar on top
    draw.rectangle([0, 0, W, 5], fill=s["color"])

    # icon circle
    cx, cy, r = 60, 80, 30
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=s["color"], outline=None)

    # emoji — render as text since PIL has limited emoji support
    # use a simple geometric shape instead
    # Shield shape
    if "shield" in s["name"]:
        pts = [(cx - 16, cy - 18), (cx + 16, cy - 18), (cx + 18, cy - 5),
               (cx + 10, cy + 15), (cx, cy + 22), (cx - 10, cy + 15),
               (cx - 18, cy - 5)]
        draw.polygon(pts, fill=(255, 255, 255))
        # checkmark
        draw.line([(cx - 6, cy), (cx, cy + 8), (cx + 8, cy - 5)],
                  fill=s["color"], width=3)
    elif "free" in s["name"]:
        # Star
        pts = []
        import math
        for i in range(5):
            outer_angle = (2 * math.pi * i / 5) - math.pi / 2
            inner_angle = (2 * math.pi * i / 5 + math.pi / 5) - math.pi / 2
            pts.append((cx + int(20 * math.cos(outer_angle)),
                        cy + int(20 * math.sin(outer_angle))))
            pts.append((cx + int(8 * math.cos(inner_angle)),
                        cy + int(8 * math.sin(inner_angle))))
        draw.polygon(pts, fill=(255, 255, 255))
    else:
        # Globe ring
        draw.ellipse([cx - 20, cy - 18, cx + 20, cy + 18], outline=(255, 255, 255), width=3)
        draw.ellipse([cx - 8, cy - 18, cx + 8, cy + 18], outline=(255, 255, 255), width=2)
        draw.line([(cx - 20, cy), (cx + 20, cy)], fill=(255, 255, 255), width=2)

    # Title text (bold, large)
    draw.text((110, 55), s["title"], fill=(255, 255, 255))

    # Description text
    draw.text((110, 110), s["desc"], fill=(180, 185, 200))

    # Subtle tagline
    draw.text((110, 160), "ipgeo · rapidapi", fill=(100, 105, 120))

    path = os.path.join(OUT, s["name"] + ".png")
    img.save(path, "PNG")
    print(f"Saved: {path}")


print("Done! 3 spotlight images generated.")
