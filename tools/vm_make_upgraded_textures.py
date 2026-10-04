"""Generate the *_upgraded textures for the vending machine.

Upgraded = the original texture with 3-pixel corner marks: the two existing
1-pixel gold corners (top-right, bottom-left) grow into 3-pixel L's, and the
other two corners (top-left, bottom-right) get matching emerald L's.
The original PNGs are only read, never written.
"""
from pathlib import Path
from PIL import Image
from make_machine_textures import GOLD_RAMP, EMERALD_RAMP, rgba

BLOCKS = Path(__file__).resolve().parent.parent / "vending_rp/textures/blocks"

# corner pixel, then its two neighbours along the edges
CORNERS = {
    "gold": [((15, 0), (14, 0), (15, 1)), ((0, 15), (1, 15), (0, 14))],
    "emerald": [((0, 0), (1, 0), (0, 1)), ((15, 15), (14, 15), (15, 14))],
}
COLOURS = {"gold": tuple(rgba(GOLD_RAMP[i]) for i in (3, 2, 1)),
           "emerald": tuple(rgba(EMERALD_RAMP[i]) for i in (3, 2, 1))}


def upgrade(src: Path) -> Path:
    im = Image.open(src).convert("RGBA")
    assert im.size == (16, 16), f"{src.name} is {im.size}, expected 16x16"
    px = im.load()
    for kind, corners in CORNERS.items():
        hi, mid, lo = COLOURS[kind]
        for corner, arm1, arm2 in corners:
            px[corner] = hi
            px[arm1] = mid
            px[arm2] = lo
    dst = src.with_name(src.stem + "_upgraded.png")
    im.save(dst)
    return dst


if __name__ == "__main__":
    sources = sorted(p for p in BLOCKS.glob("vm_machine_*.png") if not p.stem.endswith("_upgraded"))
    for src in sources:
        print(upgrade(src).name)
