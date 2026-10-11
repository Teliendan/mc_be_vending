r"""Build pack_icon.png for the vending machine packs.

The icon is the real machine, not an illustration of one: the shipped
vm_machine_body / vm_machine_head_<prof> / vm_machine_top textures are projected
onto a two-block-tall isometric box, one texel at a time. Each texel becomes a
parallelogram with integer corners (2:1 pixel-art projection), so the result is
as crisp as the game's own blocks -- no resampling anywhere.

Each feature pack shows its own machine. Core and Resources share a group
of all three machine families. A vanilla emerald
sits beside the single machines for "trading".

Run:  python mods\vending\tools\make_pack_icon.py [--review PATH]
Preview: add --preview PATH --pack PACK [--head PROFESSION]
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
PACK_DESIGNS = {
    "vending_bp": ("Core", None, False, "green"),
    "vending_rp": ("Resources", None, False, "green"),
    "vending_villagers_bp": ("Villagers", "librarian", False, "green"),
    "vending_wandering_bp": ("Wandering Trader", "wandering_trader", False, "blue"),
    "vending_shulker_bp": ("Shulker", "shulker", False, "purple"),
}
BLOCKS = os.path.join(RP, "textures", "blocks")
EMERALD = r"C:\mcmods\reference\vanilla\current\resource_packs\vanilla\textures\items\emerald.png"

ICON = 256
A, B, H = 4, 2, 5          # per texel: X/Z step (A right, B down), Y step (H up)
ORIGIN = (116, 176)        # screen position of the block's back-bottom corner
SHADE = {"left": 0.82, "right": 0.62, "top": 1.0}

# Background: a stepped radial glow in 8 px cells, so it stays pixel-art too.
BG_PALETTES = {
    "green": [(38, 64, 58), (31, 53, 48), (25, 43, 39), (20, 34, 31)],
    "blue": [(36, 60, 83), (29, 49, 69), (23, 40, 56), (18, 31, 44)],
    "purple": [(65, 45, 75), (54, 36, 63), (44, 29, 51), (34, 23, 40)],
}
CELL = 8


def project(x, y, z, origin=ORIGIN, steps=(A, B, H)):
    a, b, h = steps
    return (origin[0] + a * (x - z), origin[1] + b * (x + z) - h * y)


def shade(color, factor):
    r, g, b, a = color
    return (int(r * factor), int(g * factor), int(b * factor), a)


def draw_face(draw, texture, corner, du, dv, factor, origin, steps):
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
                pts.append(project(*p, origin=origin, steps=steps))
            draw.polygon(pts, fill=shade(color, factor))


def background(palette):
    img = Image.new("RGBA", (ICON, ICON))
    draw = ImageDraw.Draw(img)
    cx, cy = ICON * 0.45, ICON * 0.5
    reach = ICON * 0.72
    for gy in range(0, ICON, CELL):
        for gx in range(0, ICON, CELL):
            d = ((gx + CELL / 2 - cx) ** 2 + (gy + CELL / 2 - cy) ** 2) ** 0.5 / reach
            ramp = BG_PALETTES[palette]
            step = ramp[min(len(ramp) - 1, int(d * len(ramp)))]
            draw.rectangle((gx, gy, gx + CELL - 1, gy + CELL - 1), fill=step + (255,))
    return img


def draw_machine(img, head_name, upgraded=False, origin=ORIGIN, steps=(A, B, H)):
    """Project the shipped faces directly; integer steps retain crisp texels."""
    assert all(isinstance(n, int) and n > 0 for n in steps)
    suffix = "_upgraded" if upgraded else ""
    load = lambda name: Image.open(os.path.join(BLOCKS, name + ".png")).convert("RGBA")
    body, top = load("vm_machine_body" + suffix), load("vm_machine_top" + suffix)
    head = load("vm_machine_head_" + head_name + suffix)
    for texture in (body, top, head):
        assert texture.size == (16, 16), "machine face textures must be 16x16"
        assert texture.getchannel("A").getextrema() == (255, 255), "machine faces must be opaque"

    draw = ImageDraw.Draw(img)
    bounds = [project(x, y, z, origin, steps)
              for x in (0, 16) for y in (0, 32) for z in (0, 16)]
    assert all(0 <= x < ICON and 0 <= y < ICON - 4 for x, y in bounds), "machine is clipped"

    # Ground shadow: the footprint diamond, darkened, nudged down a touch.
    foot = [project(x, 0, z, origin, steps) for x, z in ((0, 0), (16, 0), (16, 16), (0, 16))]
    draw.polygon([(x, y + 4) for x, y in foot], fill=(10, 18, 16, 255))

    for base, tex in ((0, body), (16, head)):
        # Left face (z = 16): u runs along +x, v runs down from the half's top.
        draw_face(draw, tex, (0, base + 16, 16), (1, 0, 0), (0, -1, 0), SHADE["left"], origin, steps)
        # Right face (x = 16): u runs along -z.
        draw_face(draw, tex, (16, base + 16, 16), (0, 0, -1), (0, -1, 0), SHADE["right"], origin, steps)
    # Top face (y = 32).
    draw_face(draw, top, (0, 32, 0), (1, 0, 0), (0, 0, 1), SHADE["top"], origin, steps)


def build(pack, head_override=None):
    _, head, upgraded, palette = PACK_DESIGNS[pack]
    img = background(palette)
    if head_override:
        head = head_override
    if head is None:
        # Back row: feature families. Foreground: the classic villager machine.
        draw_machine(img, "wandering_trader", origin=(52, 158), steps=(2, 1, 3))
        draw_machine(img, "shulker", origin=(204, 158), steps=(2, 1, 3))
        draw_machine(img, "librarian", origin=(128, 202), steps=(3, 1, 4))
        return img
    draw_machine(img, head, upgraded)

    emerald = Image.open(EMERALD).convert("RGBA").crop((0, 0, 16, 16))
    emerald = emerald.resize((48, 48), Image.NEAREST)
    img.alpha_composite(emerald, (192, 188))
    return img


def review(images, path):
    """Pack-list sizes beside the full-size icons, with labels outside the art."""
    sheet = Image.new("RGB", (ICON * len(images), ICON + 116), (28, 30, 34))
    draw = ImageDraw.Draw(sheet)
    for i, (pack, img) in enumerate(images.items()):
        x = i * ICON
        draw.text((x + 8, 8), PACK_DESIGNS[pack][0], fill=(230, 232, 235))
        sheet.paste(img, (x, 28))
        for size, dx in ((64, 24), (32, 120)):
            sheet.paste(img.resize((size, size), Image.Resampling.NEAREST), (x + dx, 296))
    sheet.save(path)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--head", help="override the machine in a single preview")
    ap.add_argument("--pack", choices=PACK_DESIGNS, default="vending_bp", help="which pack to preview")
    ap.add_argument("--preview", metavar="PATH",
                    help="write only this preview file, not the packs' pack_icon.png")
    ap.add_argument("--review", metavar="PATH", help="write a review sheet at full, 64 and 32 pixel sizes")
    args = ap.parse_args()
    if args.head and not args.preview:
        ap.error("--head requires --preview; shipped icons use the pack-specific designs")
    images = {pack: build(pack) for pack in PACK_DESIGNS}
    assert images["vending_bp"].tobytes() == images["vending_rp"].tobytes(), "Core and Resources must share the group icon"
    assert len({img.tobytes() for img in images.values()}) == 4, "feature icons must differ from each other and the group"
    targets = [(args.preview, build(args.pack, args.head))] if args.preview else [
        (os.path.join(MOD, pack, "pack_icon.png"), img) for pack, img in images.items()]
    for path, img in targets:
        img.save(path)
        print("wrote", path)
    if args.review:
        review(images, args.review)


if __name__ == "__main__":
    main()
