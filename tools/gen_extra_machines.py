r"""Generate the two non-villager vending machines: Wandering Trader and Shulker.

Each lives in its own feature behaviour pack, so a world gets it only when that
pack is active:

    vending_wandering_bp   vm:machine_wandering_trader  (+ vm:trader_wandering_trader)
    vending_shulker_bp     vm:machine_shulker           (+ vm:trader_shulker, vm:shulker_core)

The block, the trader entity and the client entity are NOT built from scratch.
They are copied from the farmer machine with the name swapped, so the
two-half block, the upgrade permutations, the invisible trader and the
vm:apply_upgrade event stay byte-for-byte the shape that is already verified
in game. The core script needs nothing: it handles any vm:machine_* block.
Use --blocks-only to refresh the shared machine states/permutations without
rewriting trade tables, recipes, items or localization resources.

Pricing follows one rule. The UPGRADED table is the real trader's price;
the base table is dearer, so an un-upgraded machine is worse than finding the
trader. For the wandering trader, base prices are chosen so that the cured
trim used by gen_trade_tables.py (round(q * 0.7), floor 1) lands exactly on the
vanilla price -- asserted below. The shulker tables are written out by hand
because 24 * 0.7 does not round to 16.

The RP entries (terrain atlas, blocks.json, item atlas, lang) are MERGED, so
this is safe to re-run. language names are maintained in localization/catalog.json;
run this tool again after it.

Run:  python mods\vending\tools\gen_extra_machines.py
"""

import json
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root

BP_ROOT = MOD
RP = os.path.join(MOD, "vending_rp")
TEMPLATE_BP = os.path.join(BP_ROOT, "vending_villagers_bp")
TEMPLATE = "farmer"

MACHINES = {
    "wandering_trader": {"pack": "vending_wandering_bp", "name": "Wandering Trader",
                         "goods": "minecraft:lead", "core": "minecraft:bundle"},
    "shulker": {"pack": "vending_shulker_bp", "name": "Shulker",
                "goods": "minecraft:chest", "core": "vm:shulker_core"},
}

MAX_USES = 9999999

# vanilla emerald price -> base price whose 30% trim rounds back to vanilla.
BASE_PRICE = {1: 2, 2: 3, 3: 4, 4: 6, 5: 7, 6: 9}

# Every wandering trader ware as (item, count given, vanilla emerald price).
# Vanilla picks some of these at random and rolls random variants; the machine
# offers all of them, each variant as its own trade, in modern item IDs.
FLOWERS = ["dandelion", "poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip",
           "orange_tulip", "white_tulip", "pink_tulip", "oxeye_daisy", "cornflower",
           "lily_of_the_valley", "sunflower", "lilac", "rose_bush", "peony"]
SEEDS = ["wheat_seeds", "pumpkin_seeds", "melon_seeds", "beetroot_seeds"]
SAPLINGS = ["oak_sapling", "spruce_sapling", "birch_sapling", "jungle_sapling",
            "acacia_sapling", "dark_oak_sapling"]
DYES = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
        "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]
CORALS = ["tube", "brain", "bubble", "fire", "horn"]

WANDERING_WARES = (
    [("sea_pickle", 1, 2), ("slime_ball", 1, 4), ("glowstone", 1, 2), ("nautilus_shell", 1, 5),
     ("fern", 1, 1), ("sugar_cane", 1, 1), ("pumpkin", 1, 1), ("kelp", 1, 3), ("cactus", 1, 3)]
    + [(f, 1, 1) for f in FLOWERS]
    + [(s, 1, 1) for s in SEEDS]
    + [(s, 1, 5) for s in SAPLINGS]
    + [(d + "_dye", 3, 1) for d in DYES]
    + [(c + "_coral_block", 3, 1) for c in CORALS]
    + [("vine", 1, 1), ("brown_mushroom", 1, 1), ("red_mushroom", 1, 1), ("waterlily", 2, 1),
       ("red_sand", 4, 1), ("red_sandstone", 4, 1)]
    + [("tropical_fish_bucket", 1, 5), ("pufferfish_bucket", 1, 5), ("packed_ice", 1, 3),
       ("blue_ice", 1, 6), ("gunpowder", 1, 1), ("podzol", 3, 3)]
)


def trade(wants, gives, count, exp):
    return {"num_to_select": 1, "trades": [{
        "wants": [{"item": item, "quantity": qty} for item, qty in wants],
        "gives": [{"item": gives, "quantity": count}],
        "trader_exp": exp,
        "max_uses": MAX_USES,
        "reward_exp": True,
    }]}


def wandering_table(upgraded):
    groups = []
    for item, count, vanilla in WANDERING_WARES:
        price = vanilla if upgraded else BASE_PRICE[vanilla]
        assert max(1, round(BASE_PRICE[vanilla] * 0.7)) == vanilla, item
        groups.append(trade([("minecraft:emerald", price)], "minecraft:" + item, count, 0))
    return {"tiers": [{"total_exp_required": 0, "groups": groups}]}


def shulker_table(upgraded):
    shell, box = (8, 16) if upgraded else (12, 24)
    return {"tiers": [
        {"total_exp_required": 0, "groups": [
            trade([("minecraft:emerald", shell)], "minecraft:shulker_shell", 1, 2)]},
        # Five shells buy the level that unlocks the box.
        {"total_exp_required": 10, "groups": [
            trade([("minecraft:emerald", box), ("minecraft:chest", 1)],
                  "minecraft:undyed_shulker_box", 1, 2)]},
    ]}


TABLES = {"wandering_trader": wandering_table, "shulker": shulker_table}


def machine_recipe(machine, spec):
    return {"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": "vm:machine_%s_recipe" % machine},
        "tags": ["crafting_table"],
        "pattern": ["GTG", "IWI", "EEE"],
        "key": {"I": {"item": "minecraft:iron_block"},
                "G": {"item": "minecraft:gold_block"},
                "T": {"item": spec["goods"]},
                "E": {"item": "minecraft:emerald_block"},
                "W": {"item": spec["core"]}},
        "unlock": [{"item": spec["core"]}],
        "result": {"item": "vm:machine_%s" % machine, "count": 1},
    }}


SHULKER_CORE_ITEM = {"format_version": "1.21.120", "minecraft:item": {
    "description": {"identifier": "vm:shulker_core", "menu_category": {"category": "items"}},
    "components": {
        "minecraft:display_name": {"value": "item.vm:shulker_core"},
        "minecraft:icon": {"textures": {"default": "vm_shulker_core"}},
        "minecraft:max_stack_size": 64,
    },
}}

SHULKER_CORE_RECIPE = {"format_version": "1.20.10", "minecraft:recipe_shaped": {
    "description": {"identifier": "vm:shulker_core_recipe"},
    "tags": ["crafting_table"],
    "pattern": ["SSS", "SSS", "SSS"],
    "key": {"S": {"item": "minecraft:shulker_shell"}},
    "unlock": [{"item": "minecraft:shulker_shell"}],
    "result": {"item": "vm:shulker_core", "count": 1},
}}


def read_json(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def write_json(path, data, indent=2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")
    print("wrote", path)


def from_template(src, dest, machine):
    with open(src, encoding="utf-8-sig") as fh:
        text = fh.read()
    assert TEMPLATE in text, src
    write_json(dest, json.loads(text.replace(TEMPLATE, machine)))


def build_bp(machine, spec):
    bp = os.path.join(BP_ROOT, spec["pack"])
    from_template(os.path.join(TEMPLATE_BP, "blocks", "machine_%s.json" % TEMPLATE),
                  os.path.join(bp, "blocks", "machine_%s.json" % machine), machine)
    from_template(os.path.join(TEMPLATE_BP, "entities", "trader_%s.json" % TEMPLATE),
                  os.path.join(bp, "entities", "trader_%s.json" % machine), machine)
    write_json(os.path.join(bp, "recipes", "machine_%s.json" % machine),
               machine_recipe(machine, spec), indent=4)
    for suffix, upgraded in (("", False), ("_cured", True)):
        write_json(os.path.join(bp, "trading", "vm", "%s%s.json" % (machine, suffix)),
                   TABLES[machine](upgraded))
    if machine == "shulker":
        write_json(os.path.join(bp, "items", "shulker_core.json"), SHULKER_CORE_ITEM, indent=4)
        write_json(os.path.join(bp, "recipes", "shulker_core.json"), SHULKER_CORE_RECIPE, indent=4)


def build_rp():
    for machine in MACHINES:
        from_template(os.path.join(RP, "entity", "trader_%s.entity.json" % TEMPLATE),
                      os.path.join(RP, "entity", "trader_%s.entity.json" % machine), machine)

    path = os.path.join(RP, "textures", "terrain_texture.json")
    terrain = read_json(path)
    for machine in MACHINES:
        for short in ("vm_machine_head_%s" % machine, "vm_machine_head_%s_upgraded" % machine):
            assert os.path.isfile(os.path.join(RP, "textures", "blocks", short + ".png")), short
            terrain["texture_data"][short] = {"textures": "textures/blocks/" + short}
    write_json(path, terrain)

    path = os.path.join(RP, "blocks.json")
    blocks = read_json(path)
    for machine in MACHINES:
        blocks["vm:machine_%s" % machine] = {"sound": "stone", "textures": "vm_machine_body"}
    write_json(path, blocks)

    path = os.path.join(RP, "textures", "item_texture.json")
    items = read_json(path)
    assert os.path.isfile(os.path.join(RP, "textures", "items", "vm_shulker_core.png"))
    items["texture_data"]["vm_shulker_core"] = {"textures": "textures/items/vm_shulker_core"}
    write_json(path, items)

    # Block keys take the .name suffix, item keys do not (see bedrock-items).
    wanted = {}
    for machine, spec in MACHINES.items():
        wanted["tile.vm:machine_%s.name" % machine] = spec["name"] + " Machine"
        wanted["entity.vm:trader_%s.name" % machine] = spec["name"] + " Machine"
    wanted["item.vm:shulker_core"] = "Shulker Core"
    path = os.path.join(RP, "texts", "en_US.lang")
    from localization_support import merge_localized_names
    merge_localized_names(wanted)
    print("wrote", path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks-only", action="store_true")
    args = parser.parse_args()
    if args.blocks_only:
        for machine, spec in MACHINES.items():
            from_template(os.path.join(TEMPLATE_BP, "blocks", "machine_%s.json" % TEMPLATE),
                          os.path.join(MOD, spec["pack"], "blocks", "machine_%s.json" % machine), machine)
        return
    for machine, spec in MACHINES.items():
        build_bp(machine, spec)
    build_rp()
    print("wandering trader: %d trades" % len(WANDERING_WARES))


if __name__ == "__main__":
    main()
