r"""Build the vending machine block and item textures.

Two techniques, used deliberately:

  * The machine CHASSIS is plotted from an ASCII grid, in a palette sampled out of
    vanilla sprites by luminance. Nothing in vanilla looks like a vending machine,
    so there is nothing to crop -- but sampling from observer_side.png,
    gold_ingot.png and emerald.png keeps it sitting beside vanilla blocks rather
    than on top of them.
  * The GOODS in the display window are a real vanilla item sprite, blitted 1:1
    with no scaling: a steak, a book, a sword, red wool. That is what tells you at
    a glance what a machine sells.

The design language is the recipe. A machine is crafted from iron, an emerald
block and its workstation; the Upgrade Kit from gold, emeralds, a golden apple and
a potion of weakness. So the chassis is dark steel with gold trim and emerald
buttons, and the wrench is gold with emerald texels.

Outputs:

  * vm_machine_body.png          -- shared LOWER half: the machine front. Display
                                    underside, gold trim, two emerald buttons, a
                                    gold coin slot and a recessed dispensing tray.
                                    Identical on all 13, which is what makes them
                                    a product line rather than 13 odd blocks.
  * vm_machine_top.png           -- the upper half's TOP face: an emerald status
                                    light, so the machine reads as powered.
  * vm_machine_head_<prof>.png   -- upper half SIDES: the glass display case, with
                                    that profession's signature trade good in it.
  * vm_upgrade_kit.png           -- the item: a golden open-end wrench with three
                                    emerald texels down it.
  * vm_shulker_core.png          -- the item: two shulker-shell caps closed on a
                                    lime-yellow glow, i.e. a shulker, compacted.

Two earlier passes are recorded here so they are not retried:

  1. A one-texel iron_block border around the raw workstation sprite. iron_block
     has no dark texels at all, so the border read as a white picture frame at two
     texels and vanished entirely at one.
  2. The workstation sprite itself as the panel. Several are simply not
     identifiable cropped small -- a cauldron side and a stonecutter side are both
     just grey -- which is why the window now shows the GOODS instead.

The wrench keeps its own palette, drawn wholly from gold_ingot.png. It shares
character names with the chassis grids but not their colours: folding the two
palettes together once turned the wrench steel-grey, because the chassis needs
'm' to mean mid steel and the wrench needs it to mean mid gold.

Run:  python mods\vending\tools\make_machine_textures.py [--force] [--only NAME ...] [--contact-sheet PATH]
"""

import argparse
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: python -m pip install Pillow")

VANILLA_ROOT = r"E:\AI\ref\bedrock\current\resource_packs\vanilla\textures"
BLOCKS_SRC = os.path.join(VANILLA_ROOT, "blocks")
ITEMS_SRC = os.path.join(VANILLA_ROOT, "items")

BLOCKS_DEST = os.path.join(MOD, "vending_rp", "textures", "blocks")
ITEMS_DEST = os.path.join(MOD, "vending_rp", "textures", "items")

SIZE = 16
WINDOW = 14              # the display glass, inset one texel on every side

# profession -> (vanilla folder, sprite) for the good on show. Chosen to be
# instantly readable at 14x14 AND characteristic of what that machine sells --
# both matter, which is why the fisherman shows a fish and not a fishing rod.
PROFESSION_GOODS = {
    "farmer": (ITEMS_SRC, "wheat"),
    "fisherman": (ITEMS_SRC, "fish_raw"),
    "shepherd": (BLOCKS_SRC, "wool_colored_red"),
    "fletcher": (ITEMS_SRC, "arrow"),
    "librarian": (ITEMS_SRC, "book_enchanted"),
    "cartographer": (ITEMS_SRC, "compass_item"),
    "cleric": (ITEMS_SRC, "ender_pearl"),
    "armorer": (ITEMS_SRC, "iron_chestplate"),
    "weapon_smith": (ITEMS_SRC, "iron_sword"),
    "tool_smith": (ITEMS_SRC, "iron_pickaxe"),
    "butcher": (ITEMS_SRC, "beef_cooked"),
    "leather_worker": (ITEMS_SRC, "leather"),
    "stone_mason": (ITEMS_SRC, "brick"),
    "wandering_trader": (ITEMS_SRC, "lead"),
    # No vanilla sprite reads as a shulker box: its only block face is a flat
    # purple square. The good is drawn instead -- see shulker_box_sprite().
    "shulker": (None, "shulker_box"),
}

CHASSIS_SOURCES = {"steel": (BLOCKS_SRC, "observer_side"),
                   "gold": (ITEMS_SRC, "gold_ingot"),
                   "emerald": (ITEMS_SRC, "emerald")}

# Chassis grids, one character per texel.
#   h  highlight edge (top/left)   s  shadow edge (bottom/right)
#   k  recess, near-black          d  dark steel      m  mid steel
#   G  gold trim                   e  emerald         E  emerald highlight
#   .  leave whatever is underneath (the display glass and its goods)
TOP_EDGE = "h" * 15 + "G"
BOTTOM_EDGE = "G" + "s" * 14 + "k"


def _row(middle):
    """One chassis row: highlight column, 13 texels of content, shadow columns."""
    if len(middle) != SIZE - 3:
        raise ValueError("chassis row must be %d chars, got %r" % (SIZE - 3, middle))
    return "h" + middle + "ks"


BODY = [TOP_EDGE] + [_row(m) for m in [
    "mmmmmmmmmmmmm",
    "kkkkkkkkkkkkk",     # underside of the display case above
    "kkkkkkkkkkkkk",
    "GGGGGGGGGGGGG",
    "mmmmmmmmmmmmm",
    "mmeemmmmmeemm",     # selection buttons
    "mmeemmmmmeemm",
    "mmmmmGGGmmmmm",     # coin slot
    "mmmmmmmmmmmmm",
    "GGGGGGGGGGGGG",
    "mmmmmmmmmmmmm",
    "dkkkkkkkkkkkd",     # dispensing tray
    "dkkkkkkkkkkkd",
    "mmmmmmmmmmmmm",
]] + [BOTTOM_EDGE]

TOP = [TOP_EDGE] + [_row(m) for m in [
    "mmmmmmmmmmmmm",
    "GGGGGGGGGGGGG",
    "mmmmmmmmmmmmm",
    "mmmmmmmmmmmmm",
    "mmmmmmmmmmmmm",
    "mmmmmeeemmmmm",
    "mmmmmeEEemmmm",
    "mmmmmeEEemmmm",
    "mmmmmeeeemmmm",
    "mmmmmmmmmmmmm",
    "mmmmmmmmmmmmm",
    "mmmmmmmmmmmmm",
    "GGGGGGGGGGGGG",
    "mmmmmmmmmmmmm",
]] + [BOTTOM_EDGE]

HEAD = [TOP_EDGE] + [_row("." * (SIZE - 3)) for _ in range(SIZE - 2)] + [BOTTOM_EDGE]

# An open-end wrench: jaw open at the top left, handle running to the bottom right.
# The jaw is left OPEN on purpose -- a closed ring reads as a key, not a spanner.
# The three emerald texels are the "glow", and they use the MID emerald: the
# brightest texel in emerald.png is near-white and reads as a specular highlight.
WRENCH = [".mm..mm.........",
          ".ml..lm.........",
          ".ml..lm.........",
          "..mlglm.........",
          "...mlm..........",
          "....mgm.........",
          ".....mlm........",
          "......mgm.......",
          ".......mlm......",
          "........mlm.....",
          ".........mlm....",
          "..........mlm...",
          "...........mlm..",
          "...........mld..",
          "............md..",
          "................"]


# A 12x13 isometric cube, the way vanilla draws a block in an inventory slot:
#   T  top face    L  left face (mid)    R  right face (dark)
# Every texel is sampled from shulker_top_purple.png and only shaded, so the box
# stays in vanilla's purple. SEAM is the lid line, parallel to the top edges.
SHULKER_CUBE = ["....TTTT....",
                "..TTTTTTTT..",
                "TTTTTTTTTTTT",
                "LLTTTTTTTTRR",
                "LLLLTTTTRRRR",
                "LLLLLLRRRRRR",
                "LLLLLLRRRRRR",
                "LLLLLLRRRRRR",
                "LLLLLLRRRRRR",
                "LLLLLLRRRRRR",
                "LLLLLLRRRRRR",
                "..LLLLRRRR..",
                "....LLRR...."]
SHULKER_SEAM = {(0, 6), (1, 6), (2, 7), (3, 7), (4, 8), (5, 8),
                (6, 8), (7, 8), (8, 7), (9, 7), (10, 6), (11, 6)}
SHULKER_FACE = {"T": 1.25, "L": 0.8, "R": 0.6}

# The Shulker Core: two shell caps closed on each other, with the shulker's
# lime-yellow head glowing through the gap. SHELL_CAP rows of the shell sprite
# form each cap, which drops the drips so the silhouette stays compact.
SHELL_CAP = 6
CORE_GLOW = (196, 204, 96, 255)
CORE_GLOW_HI = (246, 240, 150, 255)


def shulker_box_sprite():
    top = load(BLOCKS_SRC, "shulker_top_purple").load()
    image = Image.new("RGBA", (len(SHULKER_CUBE[0]), len(SHULKER_CUBE)), (0, 0, 0, 0))
    px = image.load()
    for y, row in enumerate(SHULKER_CUBE):
        for x, char in enumerate(row):
            if char == ".":
                continue
            c = top[(x * SIZE) // image.width, (y * SIZE) // image.height]
            f = SHULKER_FACE[char] * (0.55 if (x, y) in SHULKER_SEAM else 1.0)
            px[x, y] = tuple(min(255, int(v * f)) for v in c[:3]) + (255,)
    return image


def shulker_core_sprite():
    shell = load(ITEMS_SRC, "shulker_shell")
    art = shell.crop(shell.getbbox())
    cap = art.crop((0, 0, art.width, min(art.height, SHELL_CAP)))
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    x0 = (SIZE - cap.width) // 2
    image.paste(cap, (x0, 1), cap)
    flipped = cap.transpose(Image.FLIP_TOP_BOTTOM)
    image.paste(flipped, (x0, SIZE - 1 - cap.height), flipped)

    px = image.load()
    darkest = _ramp(shell)[0]
    cx = x0 + cap.width // 2
    for y in range(1 + cap.height, SIZE - 1 - cap.height):
        for x in range(x0 + 1, x0 + cap.width - 1):
            px[x, y] = darkest
        for x in range(cx - 2, cx + 3):
            px[x, y] = CORE_GLOW
        for x in range(cx - 1, cx + 2):
            px[x, y] = CORE_GLOW_HI
    return image


DRAWN_GOODS = {"shulker_box": shulker_box_sprite}


def goods_sprite(root, name):
    return DRAWN_GOODS[name]() if root is None else load(root, name)


def load(root, name):
    """Open a vanilla sprite as RGBA. Tries .png then .tga -- grindstone_side is a TGA."""
    for ext in (".png", ".tga"):
        path = os.path.join(root, name + ext)
        if os.path.exists(path):
            image = Image.open(path).convert("RGBA")
            if image.size != (SIZE, SIZE):
                # Animated sprites are a vertical strip of frames; take the first.
                image = image.crop((0, 0, SIZE, SIZE))
            return image
    sys.exit("vanilla sprite not found: {} in {}".format(name, root))


def _ramp(image):
    """The sprite's own opaque texels, sorted dark to light."""
    texels = [t for t in list(image.getdata()) if t[3] > 200]
    texels.sort(key=lambda c: c[0] * 299 + c[1] * 587 + c[2] * 114)
    return texels


def chassis_palette():
    """Map the chassis grid characters to real vanilla colours.

    Picking by position in each sprite's own luminance ramp, rather than by a
    hardcoded RGB, means these stay in palette if the vanilla reference is
    refreshed under us.
    """
    ramps = {key: _ramp(load(root, sprite))
             for key, (root, sprite) in CHASSIS_SOURCES.items()}
    steel, gold, emerald = ramps["steel"], ramps["gold"], ramps["emerald"]
    return {
        "k": steel[0],
        "s": steel[len(steel) // 12],
        "d": steel[len(steel) // 5],
        "m": steel[len(steel) // 2],
        "h": steel[-1],
        "G": gold[-1 - len(gold) // 8],
        "e": emerald[len(emerald) // 2],
        "E": emerald[-1 - len(emerald) // 4],
    }


def wrench_palette():
    """The wrench's own ramp -- all gold, so it cannot go steel-grey."""
    gold = _ramp(load(ITEMS_SRC, "gold_ingot"))
    emerald = _ramp(load(ITEMS_SRC, "emerald"))
    return {
        "d": gold[len(gold) // 8],
        "m": gold[len(gold) // 2],
        "l": gold[-1 - len(gold) // 8],
        "g": emerald[len(emerald) // 2],
    }


def paint(image, grid, palette):
    """Stamp a grid over an image. '.' and unknown characters leave it alone."""
    px = image.load()
    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            if char in palette:
                px[x, y] = palette[char]
    return image


def plot(grid, palette):
    return paint(Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0)), grid, palette)


def display_case(goods, palette):
    """The glass window with one trade good centred in it.

    The goods sprite is placed by its own alpha bounding box, so a small icon sits
    centred rather than wherever vanilla happened to draw it. Anything wider or
    taller than the window is centre-cropped -- never scaled; a resampled item
    sprite reads as mush at the size Minecraft draws a block.
    """
    case = Image.new("RGBA", (SIZE, SIZE), palette["k"])
    px = case.load()
    for y in range(1, SIZE - 1):
        for x in range(1, SIZE - 1):
            px[x, y] = palette["s"] if y < 4 else palette["k"]   # light falling in

    box = goods.getbbox()
    art = goods.crop(box) if box else goods
    if art.width > WINDOW or art.height > WINDOW:
        left = max(0, (art.width - WINDOW) // 2)
        top = max(0, (art.height - WINDOW) // 2)
        art = art.crop((left, top,
                        left + min(WINDOW, art.width), top + min(WINDOW, art.height)))
    case.paste(art, (1 + (WINDOW - art.width) // 2, 1 + (WINDOW - art.height) // 2), art)
    return paint(case, HEAD, palette)


def write(image, path, force):
    if os.path.exists(path) and not force:
        sys.exit("{} already exists; pass --force to replace it".format(path))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="overwrite outputs that already exist")
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="write only these outputs: body, top, kit or a profession")
    ap.add_argument("--contact-sheet", metavar="PATH",
                    help="also write an upscaled contact sheet for eyeballing the result")
    args = ap.parse_args()

    if not os.path.isdir(BLOCKS_SRC):
        sys.exit("vanilla reference not found at {} -- run "
                 r"E:\AI\ref\bedrock\refresh_bedrock_ref.ps1".format(BLOCKS_SRC))

    for name, grid in (("HEAD", HEAD), ("BODY", BODY), ("TOP", TOP), ("WRENCH", WRENCH)):
        if len(grid) != SIZE or any(len(row) != SIZE for row in grid):
            sys.exit("{} grid is not {}x{}".format(name, SIZE, SIZE))

    missing = ["%s/%s" % (os.path.basename(root), sprite)
               for root, sprite in PROFESSION_GOODS.values()
               if root is not None and not any(os.path.exists(os.path.join(root, sprite + ext))
                          for ext in (".png", ".tga"))]
    if missing:
        sys.exit("vanilla sprites missing, nothing written: {}".format(", ".join(missing)))

    palette = chassis_palette()
    written = []

    def wanted(name):
        return not args.only or name in args.only

    if wanted("body"):
        body = plot(BODY, palette)
        write(body, os.path.join(BLOCKS_DEST, "vm_machine_body.png"), args.force)
        written.append(("body", body))

    if wanted("top"):
        top = plot(TOP, palette)
        write(top, os.path.join(BLOCKS_DEST, "vm_machine_top.png"), args.force)
        written.append(("top", top))

    for profession in sorted(PROFESSION_GOODS):
        if not wanted(profession):
            continue
        root, sprite = PROFESSION_GOODS[profession]
        head = display_case(goods_sprite(root, sprite), palette)
        write(head, os.path.join(BLOCKS_DEST, "vm_machine_head_%s.png" % profession), args.force)
        written.append((profession, head))

    if wanted("kit"):
        kit = plot(WRENCH, wrench_palette())
        write(kit, os.path.join(ITEMS_DEST, "vm_upgrade_kit.png"), args.force)
        written.append(("kit", kit))

    if wanted("core"):
        core = shulker_core_sprite()
        write(core, os.path.join(ITEMS_DEST, "vm_shulker_core.png"), args.force)
        written.append(("core", core))

    if args.contact_sheet:
        scale, cols = 16, 4
        rows = (len(written) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * SIZE * scale, rows * SIZE * scale), (24, 24, 28, 255))
        for i, (_, image) in enumerate(written):
            big = image.resize((SIZE * scale, SIZE * scale), Image.NEAREST)
            sheet.paste(big, ((i % cols) * SIZE * scale, (i // cols) * SIZE * scale), big)
        os.makedirs(os.path.dirname(args.contact_sheet) or ".", exist_ok=True)
        sheet.save(args.contact_sheet)
        print("wrote contact sheet", args.contact_sheet,
              "order:", ", ".join(name for name, _ in written))


if __name__ == "__main__":
    main()
