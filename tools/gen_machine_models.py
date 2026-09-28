r"""Generate the vending_rp side of the 13 villager machines.

The visible machine is a custom BLOCK (see gen_machine_blocks.py) with a hidden trader
standing inside it, whose client entity is empty, so this tool writes:

  * RP/models/entity/vm_invisible.geo.json        -- one [0,0,0] cube that renders nothing. A bone
    list with NO cube at all fails the validator, so the zero cube is mandatory, not cosmetic.
  * RP/entity/trader_<prof>.entity.json x13       -- vm:trader_<prof>, points at the empty geo.
  * RP/blocks.json                                -- 13 entries: sound "stone" + the body texture.
  * RP/textures/terrain_texture.json              -- body, top and the 13 head panels (new file).
  * merge into RP/textures/item_texture.json      -- the upgrade_kit icon (new shortname).
  * RP/texts/en_US.lang                           -- tile.<block>.name, entity.<trader>.name,
    item.<kit>. The old item/entity vm:machine_* keys are gone.

It also deletes the dead artefacts: the 13 old machine_<prof>.entity.json and the old
vm_machine.geo.json geometry.

Every PNG this pack ships already exists on disk (see "Textures are already built" in the plan).
This tool only writes atlas ENTRIES that name them, so it verifies each PNG exists BEFORE writing;
a shortname with no PNG behind it is silent until you see the purple-black texture in-game, and
verify_addon.py names the missing file so the entry is fixed, never the art.

The profession list is imported from gen_trade_tables so the wandering-trader line stays a one-liner
in exactly one place.

It rewrites the shared RP files (blocks.json, atlases, en_US.lang) with the villager entries
only, so run gen_extra_machines.py afterwards to add the feature-pack machines back.

Run:  python mods\vending\tools\gen_machine_models.py [--force]
"""

import argparse
import json
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
import sys

from gen_trade_tables import PROFESSIONS

ENTITY_FORMAT_VERSION = "1.10.0"
BLOCKS_FORMAT_VERSION = "1.21.40"

RP_ROOT = os.path.join(MOD, "vending_rp")
MODEL_DIR = os.path.join(RP_ROOT, "models", "entity")
ENTITY_DIR = os.path.join(RP_ROOT, "entity")
TEXTURES_DIR = os.path.join(RP_ROOT, "textures")
LANG_FILE = os.path.join(RP_ROOT, "texts", "en_US.lang")

OLD_GEO = os.path.join(MODEL_DIR, "vm_machine.geo.json")
GEO_DEST = os.path.join(MODEL_DIR, "vm_invisible.geo.json")

# The trader's empty model: one [0,0,0] cube. A bone with NO cube fails the
# validator, so the zero cube is mandatory, not cosmetic. (It used to be copied
# from the spike pack; it is embedded now that the spike is gone.)
INVISIBLE_GEO = {
    "format_version": "1.12.0",
    "minecraft:geometry": [{
        "description": {"identifier": "geometry.vm_invisible", "texture_width": 16, "texture_height": 16},
        "bones": [{"name": "root", "pivot": [0, 0, 0],
                   "cubes": [{"origin": [0, 0, 0], "size": [0, 0, 0], "uv": [0, 0]}]}],
    }],
}


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4)
        fh.write("\n")


def verify_textures():
    """Fail loudly before anything is written: a shortname with no PNG behind it is silent."""
    locations = {
        "vm_machine_body.png": os.path.join(TEXTURES_DIR, "blocks"),
        "vm_machine_top.png": os.path.join(TEXTURES_DIR, "blocks"),
        "vm_upgrade_kit.png": os.path.join(TEXTURES_DIR, "items"),
    }
    for prof in PROFESSIONS:
        locations["vm_machine_head_%s.png" % prof] = os.path.join(TEXTURES_DIR, "blocks")
    gone = [name for name in locations if not os.path.exists(os.path.join(locations[name], name))]
    if gone:
        sys.exit("texture verification FAILED -- these PNGs are not on disk:\n  "
                 + "\n  ".join(os.path.join("textures", g) for g in gone)
                 + "\nThey already exist per 'Textures are already built'; fix the atlas entry, "
                 "never the art.")


def write_geo(force):
    if os.path.exists(GEO_DEST) and not force:
        sys.exit("{} already exists; pass --force to replace it".format(GEO_DEST))
    os.makedirs(os.path.dirname(GEO_DEST), exist_ok=True)
    write_json(GEO_DEST, INVISIBLE_GEO)
    return GEO_DEST


def write_traders(force):
    written = []
    for prof in PROFESSIONS:
        ident = "vm:trader_%s" % prof
        data = {
            "format_version": ENTITY_FORMAT_VERSION,
            "minecraft:client_entity": {
                "description": {
                    "identifier": ident,
                    "materials": {"default": "entity_alphatest"},
                    "textures": {"default": "textures/blocks/vm_machine_head_%s" % prof},
                    "geometry": {"default": "geometry.vm_invisible"},
                    "render_controllers": ["controller.render.default"],
                }
            },
        }
        dest = os.path.join(ENTITY_DIR, "trader_%s.entity.json" % prof)
        if os.path.exists(dest) and not force:
            sys.exit("{} already exists; pass --force to replace it".format(dest))
        write_json(dest, data)
        written.append(dest)
    return written


def write_blocks():
    path = os.path.join(RP_ROOT, "blocks.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    else:
        data = {}
    if not isinstance(data, dict):
        sys.exit("%s top-level JSON is not an object; refusing to write" % path)
    data["format_version"] = BLOCKS_FORMAT_VERSION
    for prof in PROFESSIONS:
        data["vm:machine_%s" % prof] = {"sound": "stone", "textures": "vm_machine_body"}
    write_json(path, data)
    return len(data)


def write_terrain():
    path = os.path.join(TEXTURES_DIR, "terrain_texture.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    else:
        data = {}
    if not isinstance(data, dict):
        sys.exit("%s top-level JSON is not an object; refusing to write" % path)
    data.setdefault("resource_pack_name", "vending_rp")
    data["texture_name"] = "atlas.terrain"
    data.setdefault("texture_data", {})
    for name in ("vm_machine_body", "vm_machine_top"):
        data["texture_data"][name] = {"textures": "textures/blocks/%s" % name}
    for prof in PROFESSIONS:
        short = "vm_machine_head_%s" % prof
        data["texture_data"][short] = {"textures": "textures/blocks/%s" % short}
    write_json(path, data)
    return len(data["texture_data"])


def merge_kit():
    path = os.path.join(TEXTURES_DIR, "item_texture.json")
    if not os.path.exists(path):
        sys.exit("item_texture.json missing at %s -- nothing to merge into" % path)
    with open(path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        sys.exit("%s top-level JSON is not an object; refusing to write" % path)
    data.setdefault("texture_data", {})
    data["texture_data"]["vm_upgrade_kit"] = {"textures": "textures/items/vm_upgrade_kit"}
    write_json(path, data)
    return "vm_upgrade_kit" in data["texture_data"]


def write_lang(force):
    lines = []
    for prof in PROFESSIONS:
        # Blocks: key "tile.<ns>:<id>.name" -- blocks DO take the .name suffix (items do not).
        # Entities: key "entity.<ns>:<id>.name" WITH the .name suffix.
        ident = "vm:machine_%s" % prof
        lines.append("tile.%s.name=%s Machine" % (ident, prof.title()))
        lines.append("entity.vm:trader_%s.name=%s Machine" % (prof, prof.title()))
    # Item: key "item.<ns>:<id>" WITHOUT the .name suffix -- see bedrock-items skill.
    lines.append("item.vm:upgrade_kit=Upgrade Kit")
    if os.path.exists(LANG_FILE) and not force:
        sys.exit("%s already exists; pass --force to overwrite it" % LANG_FILE)
    with open(LANG_FILE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return len(lines)


def delete_dead():
    removed = []
    for prof in PROFESSIONS:
        old = os.path.join(ENTITY_DIR, "machine_%s.entity.json" % prof)
        if os.path.exists(old):
            os.remove(old)
            removed.append(old)
    if os.path.exists(OLD_GEO):
        os.remove(OLD_GEO)
        removed.append(OLD_GEO)
    return removed


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument("--force", action="store_true",
                    help="overwrite the geo and client entities that already exist")
    args = ap.parse_args()

    verify_textures()
    geo = write_geo(args.force)
    traders = write_traders(args.force)
    nb = write_blocks()
    nt = write_terrain()
    has_kit = merge_kit()
    nl = write_lang(args.force)
    removed = delete_dead()

    print("geo:       wrote {} (geometry.vm_invisible)".format(geo))
    print("traders:   {} written to {}".format(len(traders), ENTITY_DIR))
    for prof in PROFESSIONS:
        print("  trader_{}".format(prof))
    print("blocks:    {} keys in {}".format(nb, os.path.join(RP_ROOT, "blocks.json")))
    print("terrain:   {} entries in {}".format(nt, os.path.join(TEXTURES_DIR, "terrain_texture.json")))
    print("kit icon:  %s into item_texture.json" % ("added" if has_kit else "already present"))
    print("lang:      {} keys in {}".format(nl, LANG_FILE))
    print("removed:   %d dead files" % len(removed))
    for path in removed:
        print("  {}".format(os.path.relpath(path)))


if __name__ == "__main__":
    main()
