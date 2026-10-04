"""Generate the 13 villager machine crafting recipes, each carrying its own `unlock`.

For each profession this writes one shaped recipe,
vending_villagers_bp/recipes/machine_<prof>.json:

    G T G      G  gold block        T  the profession's signature goods
    I W I      I  iron block        W  the profession's workstation
    E E E      E  emerald block

It reproduces the files in the pack byte for byte -- check with
`--out temp/recipes_check` and a diff before overwriting anything. An earlier
version of this tool emitted an older III/IWE/III layout and had drifted from
the real files; the layout above is the one in play.

The workstation is also the unlock. A crafting recipe with no `unlock` is silent:
there is no error, creative cannot disprove it (Bedrock's creative crafting
table has only a recipe book), and the recipe simply never shows up in the
survival recipe book.

Item identifier quirks, both checked against vanilla_item_ids.txt:
  * fletcher's workstation is "fletching_table".
  * stone mason's is "stonecutter_block" -- plain "stonecutter" is the legacy
    block ID and is not what the recipe names.

The wandering trader and shulker machines are not villagers and live in their
own packs; their recipes come from gen_extra_machines.py.

Run:  python mods/vending/tools/gen_machine_recipes.py [--force] [--out DIR]
"""

import argparse
import json
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
import sys
from machine_catalog import VILLAGER_MACHINES

# profession -> (goods T, workstation W), both without the minecraft: namespace.
RECIPES = {profession: (spec[0], spec[3])
           for profession, spec in VILLAGER_MACHINES.items()}

# recipes track their own version, a long-stable track separate from items and
# blocks.
RECIPE_FORMAT_VERSION = "1.20.10"

# Goods whose aux value selects a variant. Without "data" the ingredient is a
# wildcard (aux 32767): for arrow that means "any tipped arrow", so the recipe
# book shows a Tipped Arrow and the content log spams
# "Potion with aux value 32766 does not exist". Pin the plain variant.
GOODS_DATA = {
    "arrow": 0,
    "empty_map": 0,  # plain Empty Map, rather than the locator-map aux variant
}

RECIPE_DIR = os.path.join(MOD, "vending_villagers_bp", "recipes")


def goods_key(goods):
    key = {"item": "minecraft:%s" % goods}
    if goods in GOODS_DATA:
        key["data"] = GOODS_DATA[goods]
    return key


def build_recipe(prof, goods, workstation):
    workstation = "minecraft:%s" % workstation
    return {
        "format_version": RECIPE_FORMAT_VERSION,
        "minecraft:recipe_shaped": {
            "description": {"identifier": "vm:machine_%s_recipe" % prof},
            "tags": ["crafting_table"],
            "pattern": ["GTG", "IWI", "EEE"],
            "key": {
                "I": {"item": "minecraft:iron_block"},
                "G": {"item": "minecraft:gold_block"},
                "T": goods_key(goods),
                "E": {"item": "minecraft:emerald_block"},
                "W": {"item": workstation},
            },
            "unlock": [{"item": workstation}],
            "result": {"item": "vm:machine_%s" % prof, "count": 1},
        },
    }


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument("--force", action="store_true",
                    help="overwrite machine_*.json recipes if they exist")
    ap.add_argument("--out", default=RECIPE_DIR,
                    help="output directory (default: %(default)s)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    for prof, (goods, workstation) in RECIPES.items():
        path = os.path.join(args.out, "machine_%s.json" % prof)
        if os.path.exists(path) and not args.force:
            sys.exit("%s already exists; pass --force to overwrite it" % path)
        write_json(path, build_recipe(prof, goods, workstation))

    print("recipes: %d written to %s" % (len(RECIPES), args.out))
    for prof, (goods, workstation) in RECIPES.items():
        print("  %-16s T=minecraft:%-16s W=unlock=minecraft:%s" % (prof, goods, workstation))


if __name__ == "__main__":
    main()
