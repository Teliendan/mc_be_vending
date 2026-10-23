r"""Generate the 13 vending-machine block definitions, one custom block per profession.

Each machine is ONE custom block, vm:machine_<prof>, that occupies two stacked
positions through a block state, vm:half: 0 (the solid, selectable, breakable
base) and 1 (the upper half). The upper half keeps full collision and normally
drops its selection box so clicks reach the invisible trader. The core script
temporarily exposes a full selection box while crouching to allow native block
placement; the two halves share a geometry so they read as one
two-block-tall machine.

The base components (worn by every half, so the base is always mineable and
selectable) wear the shared body texture. Permutations override the
upper half: normally selection_box off, always unmineable, and that profession's panel
texture plus the shared top texture, which lands on "up" -- an absolute face name
-- so the emerald status light shows on the machine's crown no matter which way
it faces.

The textures are shortnames from RP/textures/terrain_texture.json, never file
paths, and each must have a PNG behind it in mods/vending/vending_rp/
textures/blocks/. A shortname with no PNG renders as the purple-black missing
block, and verify_addon.py will not tell you, so this tool checks every PNG is on
disk before it writes a single file -- the same discipline gen_machine_models.py
uses for its vanilla sprite names.

Run:  python mods\vending\tools\gen_machine_blocks.py [--force]
"""

import argparse
import json
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
import sys

BLOCKS_DIR = os.path.join(MOD, "vending_villagers_bp", "blocks")

# The 16 PNGs every machine block references: the shared body and top, plus one
# panel per profession. Iterate the profession list to build the per-profession
# shortnames so the check below names a real file.
PROFESSIONS = [
    "farmer",
    "fisherman",
    "shepherd",
    "fletcher",
    "librarian",
    "cartographer",
    "cleric",
    "armorer",
    "weapon_smith",
    "tool_smith",
    "butcher",
    "leather_worker",
    "stone_mason",
]

TEXTURE_ROOT = os.path.join(MOD, "vending_rp",
                            "textures", "blocks")


def _sprite_png(shortname):
    return os.path.join(TEXTURE_ROOT, shortname + ".png")


def verify_textures():
    """Fail before writing if any PNG the machines reference is missing.

    A missing PNG is silent until the block reads as the purple-black missing
    texture in-game; catch it here where the file name is in hand.
    """
    names = ["vm_machine_body", "vm_machine_top"]
    names += ["vm_machine_head_{}".format(p) for p in PROFESSIONS]
    names += [n + "_upgraded" for n in names]  # the Upgrade Kit swaps every texture
    missing = [n for n in names if not os.path.exists(_sprite_png(n))]
    if missing:
        lines = ["texture verification FAILED -- these PNGs are not on disk:"]
        lines += ["  {}".format(n) for n in missing]
        lines.append("Rebuild them with tools\\make_machine_textures.py, or point the "
                     "atlas at a file that exists; verify_addon.py will not catch a "
                     "missing PNG.")
        sys.exit("\n".join(lines))


def build(profession):
    """Return the vm:machine_<prof> block definition for one profession.

    Base components describe the solid, mineable lower half; the permutation
    rewrites the upper half so the crosshair reaches the trader inside.

    The block's in-world texture is the shared body (material_instances), but the
    icon it shows in the menu, inventory and hand comes from item_visual, which
    is independent -- here it wears that profession's head panel so a stack of
    machines reads as the profession rather than a plain body cube.
    """
    return {
        "format_version": "1.26.50",
        "minecraft:block": {
            "description": {
                "identifier": "vm:machine_{}".format(profession),
                "menu_category": {"category": "items"},
                "states": {"vm:half": [0, 1], "vm:upgraded": [False, True],
                           "vm:build_mode": [False, True]},
            },
            "components": {
                "vm:machine": {},
                "minecraft:tags": ["minecraft:is_pickaxe_item_destructible"],
                "minecraft:flammable": False,
                "minecraft:liquid_detection": {"detection_rules": [{
                    "liquid_type": "water", "can_contain_liquid": False, "on_liquid_touches": "blocking"}]},
                "minecraft:destructible_by_mining": {"seconds_to_destroy": 8},
                "minecraft:destructible_by_explosion": {"explosion_resistance": 1200},
                "minecraft:movable": {"movement_type": "immovable"},
                "minecraft:loot": "loot_tables/blocks/machine_{}.json".format(profession),
                "minecraft:map_color": "#8f8f8f",
                "minecraft:geometry": "minecraft:geometry.full_block",
                "minecraft:redstone_conductivity": {"redstone_conductor": True},
                "minecraft:instrument_sound": {"up": "note.iron_xylophone"},
                "minecraft:material_instances": {
                    "*": {"texture": "vm_machine_body", "render_method": "opaque"},
                },
                "minecraft:item_visual": {
                    "geometry": {"identifier": "minecraft:geometry.full_block"},
                    "material_instances": {
                        "*": {"texture": "vm_machine_head_{}".format(profession),
                              "render_method": "opaque"},
                    },
                },
            },
            "permutations": [
                {
                    "condition": "q.block_state('vm:half') == 1",
                    "components": {
                        "minecraft:selection_box": False,
                        "minecraft:destructible_by_mining": False,
                        "minecraft:loot": "loot_tables/blocks/machine_upper_empty.json",
                    },
                },
                {
                    "condition": "q.block_state('vm:half') == 1 && q.block_state('vm:build_mode')",
                    "components": {"minecraft:selection_box": {
                        "origin": [-8, 0, -8], "size": [16, 16, 16],
                    }},
                },
                {
                    "condition": "q.block_state('vm:half') == 0 && q.block_state('vm:upgraded')",
                    "components": {
                        "minecraft:material_instances": {
                            "*": {"texture": "vm_machine_body_upgraded", "render_method": "opaque"},
                        },
                    },
                },
                {
                    "condition": "q.block_state('vm:half') == 1 && !q.block_state('vm:upgraded')",
                    "components": {
                        "minecraft:material_instances": {
                            "*": {"texture": "vm_machine_head_{}".format(profession),
                                  "render_method": "opaque"},
                            "up": {"texture": "vm_machine_top", "render_method": "opaque"},
                        },
                    },
                },
                {
                    "condition": "q.block_state('vm:half') == 1 && q.block_state('vm:upgraded')",
                    "components": {
                        "minecraft:material_instances": {
                            "*": {"texture": "vm_machine_head_{}_upgraded".format(profession),
                                  "render_method": "opaque"},
                            "up": {"texture": "vm_machine_top_upgraded", "render_method": "opaque"},
                        },
                    },
                },
            ],
        },
    }


def write_machine_loot(pack_root, profession):
    """Only the base owns one item; native explosion decay retains its context."""
    loot_dir = os.path.join(pack_root, "loot_tables", "blocks")
    os.makedirs(loot_dir, exist_ok=True)
    tables = {
        "machine_" + profession: {"pools": [{"rolls": 1, "entries": [{
            "type": "item", "name": "vm:machine_" + profession,
            "functions": [{"function": "explosion_decay"}],
        }]}]},
        "machine_upper_empty": {"pools": [{"rolls": 1, "entries": [{"type": "empty"}]}]},
    }
    for name, table in tables.items():
        with open(os.path.join(loot_dir, name + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(table, fh, indent=2)
            fh.write("\n")


def material_policy(profession):
    return {
        "profile": "metal_machine",
        "property_checks": {"minecraft:instrument_sound": {
            "counterpart": "minecraft:iron_block", "expected": {"up": "note.iron_xylophone"},
            "source": "Block of Iron: a note block placed ON this block plays iron xylophone. Vanilla data-driven blocks (vanilla_1.26.50 concrete) key it as \"up\"."}, "RP:sound": {
            "counterpart": "minecraft:iron_block", "expected": "iron",
            "source": "reference/vanilla/current/resource_packs/vanilla_1.21.60/blocks.json"}},
        "harvest": "One native base-owned machine item; explicit empty upper loot. Upper-only loss uses support-collapse context; Creative cleanup drops nothing. Owner 2026-10-10: collect with any tool or hand; no required tool.",
        "loot_checks": {
            "loot_tables/blocks/machine_" + profession + ".json": {
                "counterpart": "minecraft:iron_block", "explosion_decay": True,
                "source": "references/harvest-explosion-loot.md; docs/VANILLA_PARITY.md: native decay and one base-owned item."},
            "loot_tables/blocks/machine_upper_empty.json": {
                "counterpart": "minecraft:wooden_door", "explosion_decay": False,
                "source": "Paired-block one-item ownership; docs/VANILLA_PARITY.md.",
                "reason": "Manually paired machines: only the base owns loot; upper-only loss destroys a surviving base natively."},
        },
        "reason": "Preserve deliberate protected trader lifecycle: mining 8, resistance 1200, upper half cannot be mined independently.",
        "overrides": {"minecraft:destructible_by_mining": {"seconds_to_destroy": 8},
                      "minecraft:destructible_by_explosion": {"explosion_resistance": 1200}},
        "permutations": {"q.block_state('vm:half') == 1": {
            "reason": "Only the base owns loot; the upper half is not independently mineable.",
            "overrides": {"minecraft:destructible_by_mining": False}}},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="overwrite blocks that already exist")
    args = ap.parse_args()

    verify_textures()
    os.makedirs(BLOCKS_DIR, exist_ok=True)
    for profession in PROFESSIONS:
        path = os.path.join(BLOCKS_DIR, "machine_{}.json".format(profession))
        if os.path.exists(path) and not args.force:
            sys.exit("{} already exists; pass --force to replace it".format(path))
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(build(profession), fh, indent=2)
            fh.write("\n")
        write_machine_loot(os.path.dirname(BLOCKS_DIR), profession)
    print("wrote {} block definitions to {}".format(len(PROFESSIONS), BLOCKS_DIR))
    policy_path = os.path.join(os.path.dirname(BLOCKS_DIR), "block_materials.json")
    if os.path.exists(policy_path):
        with open(policy_path, encoding="utf-8", newline="\n") as fh:
            policy = json.load(fh)
    else:
        policy = {"schema_version": 1, "blocks": {}}
    for profession in PROFESSIONS:
        entry = policy["blocks"].setdefault("vm:machine_" + profession, material_policy(profession))
        entry.setdefault("property_checks", {})["minecraft:instrument_sound"] = material_policy(profession)["property_checks"]["minecraft:instrument_sound"]
    with open(policy_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(policy, fh, indent=2)
        fh.write("\n")
    for profession in PROFESSIONS:
        print("  machine_{}".format(profession))


if __name__ == "__main__":
    main()
