r"""Build pack_icon.png for the vending machine packs.

The icon is the real machine, not an illustration of one: the shipped
vm_machine_body / vm_machine_head_<prof> / vm_machine_top textures are projected
onto a two-block-tall isometric box, one texel at a time. Each texel becomes a
parallelogram with integer corners (2:1 pixel-art projection), so the result is
as crisp as the game's own blocks -- no resampling anywhere.

The librarian head is shown because the enchanted book is the most recognisable
trade good. A vanilla emerald sits beside the machine for "trading".

Run:  python mods\vending\tools\make_pack_icon.py [--head PROFESSION] [--preview PATH]
"""

import argparse
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow is required: python -m pip install Pillow")

RP = os.path.join(MOD, "vending_rp")
BP = os.path.join(MOD, "vending_bp")
BLOCKS = os.path.join(RP, "textures", "blocks")
EMERALD = r"E:\AI\ref\bedrock\current\resource_packs\vanilla\textures\items\emerald.png"

ICON = 256
A, B, H = 4, 2, 5          # per texel: X/Z step (A right, B down), Y step (H up)
ORIGIN = (116, 176)        # screen position of the block's back-bottom corner
SHADE = {"left": 0.82, "right": 0.62, "top": 1.0}

# Background: a stepped radial glow in 8 px cells, so it stays pixel-art too.
BG_STEPS = [(38, 64, 58), (31, 53, 48), (25, 43, 39), (20, 34, 31)]
CELL = 8


def project(x, y, z):
    return (ORIGIN[0] + A * (x - z), ORIGIN[1] + B * (x + z) - H * y)


def shade(color, factor):
    r, g, b, a = color
    return (int(r * factor), int(g * factor), int(b * factor), a)


def draw_face(draw, texture, corner, du, dv, factor):
    """Paint a 16x16 texture onto the face spanned from `corner` by the texel
    steps du (along u) and dv (along v), both 3D vectors."""
    px = texture.load()
    for v in range(16):
        for u in range(16):
            color = px[u, v]
            if color[3] < 128:
                continue
            pts = []
            for cu, cv in ((u, v), (u + 1, v), (u + 1, v + 1), (u, v + 1)):
                p = [corner[i] + cu * du[i] + cv * dv[i] for i in range(3)]
                pts.append(project(*p))
            draw.polygon(pts, fill=shade(color, factor))


def background():
    img = Image.new("RGBA", (ICON, ICON))
    draw = ImageDraw.Draw(img)
    cx, cy = ICON * 0.45, ICON * 0.5
    reach = ICON * 0.72
    for gy in range(0, ICON, CELL):
        for gx in range(0, ICON, CELL):
            d = ((gx + CELL / 2 - cx) ** 2 + (gy + CELL / 2 - cy) ** 2) ** 0.5 / reach
            step = BG_STEPS[min(len(BG_STEPS) - 1, int(d * len(BG_STEPS)))]
            draw.rectangle((gx, gy, gx + CELL - 1, gy + CELL - 1), fill=step + (255,))
    return img


def build(head_name):
    load = lambda name: Image.open(os.path.join(BLOCKS, name + ".png")).convert("RGBA")
    body, top = load("vm_machine_body"), load("vm_machine_top")
    head = load("vm_machine_head_" + head_name)

    img = background()
    draw = ImageDraw.Draw(img)

    # Ground shadow: the footprint diamond, darkened, nudged down a touch.
    foot = [project(0, 0, 0), project(16, 0, 0), project(16, 0, 16), project(0, 0, 16)]
    draw.polygon([(x, y + 4) for x, y in foot], fill=(10, 18, 16, 255))

    for base, tex in ((0, body), (16, head)):
        # Left face (z = 16): u runs along +x, v runs down from the half's top.
        draw_face(draw, tex, (0, base + 16, 16), (1, 0, 0), (0, -1, 0), SHADE["left"])
        # Right face (x = 16): u runs along -z.
        draw_face(draw, tex, (16, base + 16, 16), (0, 0, -1), (0, -1, 0), SHADE["right"])
    # Top face (y = 32).
    draw_face(draw, top, (0, 32, 0), (1, 0, 0), (0, 0, 1), SHADE["top"])

    emerald = Image.open(EMERALD).convert("RGBA").crop((0, 0, 16, 16))
    emerald = emerald.resize((48, 48), Image.NEAREST)
    img.alpha_composite(emerald, (192, 188))
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--head", default="librarian", help="which machine head to show")
    ap.add_argument("--preview", metavar="PATH",
                    help="write only this preview file, not the packs' pack_icon.png")
    args = ap.parse_args()

    img = build(args.head)
    targets = [args.preview] if args.preview else [
        os.path.join(BP, "pack_icon.png"), os.path.join(RP, "pack_icon.png")]
    for path in targets:
        img.save(path)
        print("wrote", path)


if __name__ == "__main__":
    main()
