r"""Generate the non-villager vending machines: Wandering Trader, Shulker and the four Loot Machines.

Each lives in its own feature behaviour pack, so a world gets it only when that
pack is active:

    vending_wandering_bp   vm:machine_wandering_trader  (+ vm:trader_wandering_trader)
    vending_shulker_bp     vm:machine_shulker           (+ vm:trader_shulker, vm:shulker_core)
    vending_loot_bp        vm:machine_loot_overworld|nether|trial|end (+ vm:trader_loot_<stage>)

The four Loot Machines (the Peaceful catalogue, tools/peaceful_catalog.json) sell the mob loot
a Peaceful world cannot produce; their trade tables are read from that catalogue.

The block, the trader entity and the client entity are NOT built from scratch.
They are copied from the farmer machine with the name swapped, so the
two-half block, the upgrade permutations, the invisible trader and the
vm:apply_upgrade event stay byte-for-byte the shape that is already verified
in game. The core script needs nothing: it handles any vm:machine_* block.
Use --blocks-only to refresh the shared machine states/permutations without
rewriting trade tables, recipes, items or localization resources.

Trade tables are written by gen_trade_tables.py (TABLES below).
Wandering upgraded prices/counts come from the newest installed vanilla table.
Basic sales cost more emeralds; basic buybacks pay fewer emeralds, minimum one,
without inflating unstackable bucket/bottle inputs. The custom shulker balance
remains explicit. All native candidates (every trade of every pick-N group) become singleton
selection groups, with the same deterministic rules as the villager tables.

The RP entries (terrain atlas, blocks.json, item atlas, lang) are MERGED, so
this is safe to re-run. language names are maintained in localization/catalog.json;
run this tool again after it.

Run:  python mods\vending\tools\gen_extra_machines.py
"""

import copy
import json
from trade_sources import load_trade_source, fixture_items
from gen_trade_tables import _tier_trades, deterministic_variants
import os
from gen_machine_blocks import write_machine_loot
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

# One Loot Machine per catalogue stage. `goods` is the glass display item, `recipe_goods` the recipe's
# T slot (a display good can be a SOLD item, a recipe ingredient must not be), `core` the stage proof (W).
LOOT_STAGES = {
    "overworld": {"catalog_stage": "overworld", "goods": "minecraft:bone",
                  "recipe_goods": "minecraft:carved_pumpkin", "core": "minecraft:bone_block"},
    "nether": {"catalog_stage": "nether", "goods": "minecraft:blaze_rod",
               "recipe_goods": "minecraft:magma", "core": "minecraft:nether_wart_block"},  # magma = magma block
    "trial": {"catalog_stage": "trial", "goods": "minecraft:breeze_rod",
              "recipe_goods": "minecraft:copper_grate", "core": "minecraft:trial_key"},
    "end": {"catalog_stage": "end_boss", "goods": "minecraft:nether_star",
            "recipe_goods": "minecraft:end_crystal", "core": "minecraft:shulker_shell"},
}
for _stage, _spec in LOOT_STAGES.items():
    MACHINES["loot_" + _stage] = dict(_spec, pack="vending_loot_bp", name=_stage.capitalize() + " Loot")

MAX_USES = 9999999
CATALOG = os.path.join(MOD, "tools", "peaceful_catalog.json")

def base_price(quantity):
    """Dearer emerald cost, with upgraded price exactly matching vanilla."""
    return min(64, max(quantity + 1, round(quantity / 0.7)))


def trade(wants, gives, count, exp):
    return {"num_to_select": 1, "trades": [{
        "wants": [{"item": item, "quantity": qty} for item, qty in wants],
        "gives": [{"item": gives, "quantity": count}],
        "trader_exp": exp,
        "max_uses": MAX_USES,
        "reward_exp": True,
    }]}


def wandering_table(upgraded, root=None, stripped=None):
    source = load_trade_source("wandering_trader", root).data
    groups, seen = [], []
    for tier in source["tiers"]:
        for original in _tier_trades(tier):
            for option in deterministic_variants(original, stripped):
                if option in seen:  # a repeated trade is a roll weight; sell it once
                    continue
                seen.append(option)
                offer = copy.deepcopy(option)
                offer["wants"] = fixture_items(offer["wants"])
                offer["gives"] = fixture_items(offer["gives"])
                if not upgraded:
                    if any(line["item"] == "minecraft:emerald" for line in offer["wants"]):
                        for line in offer["wants"]:
                            if line["item"] == "minecraft:emerald":
                                line["quantity"] = base_price(line.get("quantity", 1))
                    else:
                        # A bucket/bottle cannot occupy a trade slot as a stack
                        # of two. Keep native input quantities; reduce payout.
                        for line in offer["gives"]:
                            if line["item"] == "minecraft:emerald":
                                line["quantity"] = max(1, round(line.get("quantity", 1) * 0.7))
                offer.update(trader_exp=0, max_uses=MAX_USES, reward_exp=True)
                groups.append({"num_to_select": 1, "trades": [offer]})
    return {"tiers": [{"total_exp_required": 0, "groups": groups}]}


def shulker_table(upgraded, root=None):
    shell, box = (8, 16) if upgraded else (12, 24)
    return {"tiers": [
        {"total_exp_required": 0, "groups": [
            trade([("minecraft:emerald", shell)], "minecraft:shulker_shell", 1, 2)]},
        # Five shells buy the level that unlocks the box.
        {"total_exp_required": 10, "groups": [
            trade([("minecraft:emerald", box), ("minecraft:chest", 1)],
                  "minecraft:undyed_shulker_box", 1, 2)]},
    ]}


# Items sold side by side (owner, 2026-11-21): a family sorts at its cheapest member's price.
LOOT_FAMILIES = {"prismarine_shard": "prismarine", "prismarine_crystals": "prismarine",
                 "trial_key": "trial_key", "ominous_trial_key": "trial_key",
                 "ochre_froglight": "froglight", "pearlescent_froglight": "froglight",
                 "verdant_froglight": "froglight"}


def loot_offer_order(entry, included=None):
    """Owner (2026-11-21): ordinary loot first, cheapest first, then mob heads, then music discs last;
    a family (LOOT_FAMILIES) stays together at its cheapest member's price, members cheapest first."""
    def short(e):
        return e["item"].split(":", 1)[1]

    def price(e):
        return sum(line["quantity"] for line in e["wants"])

    item = short(entry)
    if item.startswith("music_disc_"):
        group = 2
    elif item.endswith("_head") or item.endswith("_skull"):
        group = 1
    else:
        group = 0
    family = LOOT_FAMILIES.get(item, item)
    members = [e for e in (included or [entry]) if LOOT_FAMILIES.get(short(e), short(e)) == family] or [entry]
    return (group, min(price(e) for e in members), family, price(entry), item)


def loot_table(machine, upgraded):
    """One tier, one singleton group per catalogue item of the machine's stage, paid in emeralds."""
    stage = MACHINES[machine]["catalog_stage"]
    with open(CATALOG, encoding="utf-8") as fh:
        included = json.load(fh)["included"]
    key = "upgraded_wants" if upgraded else "wants"
    groups = []
    for entry in sorted((e for e in included if e["stage"] == stage), key=lambda e: loot_offer_order(e, included)):
        offer = {"wants": [dict(line) for line in entry[key]],
                 "gives": [{"item": entry["item"], "quantity": entry["quantity"]}],
                 "trader_exp": 0, "max_uses": MAX_USES, "reward_exp": True}
        groups.append({"num_to_select": 1, "trades": [offer]})
    return {"tiers": [{"total_exp_required": 0, "groups": groups}]}


TABLES = {"wandering_trader": wandering_table, "shulker": shulker_table}
for _machine in MACHINES:
    if _machine.startswith("loot_"):
        TABLES[_machine] = (lambda machine: lambda upgraded, root=None: loot_table(machine, upgraded))(_machine)


def machine_recipe(machine, spec):
    return {"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": "vm:machine_%s_recipe" % machine},
        "tags": ["crafting_table"],
        "pattern": ["GTG", "IWI", "EEE"],
        "key": {"I": {"item": "minecraft:iron_block"},
                "G": {"item": "minecraft:gold_block"},
                "T": {"item": spec.get("recipe_goods", spec["goods"])},
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
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")
    print("wrote", path)


def from_template(src, dest, machine):
    with open(src, encoding="utf-8-sig") as fh:
        text = fh.read()
    assert TEMPLATE in text, src
    write_json(dest, json.loads(text.replace(TEMPLATE, machine)))
    if os.path.basename(os.path.dirname(src)) == "blocks":
        write_machine_loot(os.path.dirname(os.path.dirname(dest)), machine)
        source_policy = os.path.join(os.path.dirname(os.path.dirname(src)), "block_materials.json")
        target_policy = os.path.join(os.path.dirname(os.path.dirname(dest)), "block_materials.json")
        template_policy = read_json(source_policy)["blocks"]["vm:machine_" + TEMPLATE]
        # Loot records contain profession-specific routes just like the block.
        template_policy = json.loads(json.dumps(template_policy).replace(TEMPLATE, machine))
        policy = read_json(target_policy) if os.path.exists(target_policy) else {"schema_version": 1, "blocks": {}}
        entry = policy["blocks"].setdefault("vm:machine_" + machine, template_policy)
        entry.setdefault("property_checks", {})["minecraft:instrument_sound"] = template_policy["property_checks"]["minecraft:instrument_sound"]
        write_json(target_policy, policy)


def build_bp(machine, spec):
    bp = os.path.join(BP_ROOT, spec["pack"])
    from_template(os.path.join(TEMPLATE_BP, "blocks", "machine_%s.json" % TEMPLATE),
                  os.path.join(bp, "blocks", "machine_%s.json" % machine), machine)
    from_template(os.path.join(TEMPLATE_BP, "entities", "trader_%s.json" % TEMPLATE),
                  os.path.join(bp, "entities", "trader_%s.json" % machine), machine)
    write_json(os.path.join(bp, "recipes", "machine_%s.json" % machine),
               machine_recipe(machine, spec), indent=4)
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
        blocks["vm:machine_%s" % machine] = {"sound": "iron", "textures": "vm_machine_body"}
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
    print("wandering trader: %d trades" % len(wandering_table(True)["tiers"][0]["groups"]))


if __name__ == "__main__":
    main()
