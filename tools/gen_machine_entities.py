r"""Generate the 13 vending-machine trader entities for the vending_bp behaviour pack.

Each machine is one custom block with a hidden trader standing inside its upper half. The
trader is a separate entity -- the block owns collision and breaking, the trader owns the
trade table -- so the two must not share an identifier: the block is `vm:machine_<prof>`,
this tool emits `vm:trader_<prof>`.

The trader is the proven-minimum entity the spike (vending_spike_bp/entities/swap_trader.json)
ran: a `minecraft:economy_trade_table` on the base components plus one `component_group` that
swaps the table for the cured variant, driven by a single event. The engine levels the trader
natively from the five tiers in that table -- like a villager -- so the script never touches a
tier. The base components keep it put: a small collision box, no physics so it hangs motionless,
immovable by knockback and piston, and a damage sensor that swallows every hit.

Each table holds exactly one group (`vm:upgraded`) and each event adds only that one group, so
a trader can never carry two trade tables at once and a second Upgrade Kit simply finds none to
add. This is the same single-table shape the spike used; the trade-table files themselves are
produced by gen_trade_tables.py.

Run:  python mods\vending\tools\gen_machine_entities.py [--force]
"""

import argparse
import json
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_trade_tables import PROFESSIONS  # noqa: E402

OUTPUT_DIR = os.path.join(MOD, "vending_villagers_bp", "entities")

# The single component group: applying an Upgrade Kit swaps the trader's table for the cured
# one. There is no `locked` group -- crafting the machine *is* the unlock, so a freshly placed
# trader always trades at full price until a kit is applied.
UPGRADED_GROUP = "vm:upgraded"
UPGRADE_EVENT = "vm:apply_upgrade"


def trade_table_component(profession, table):
    return {
        "display_name": "entity.vm:trader_{}.name".format(profession),
        "table": "trading/vm/{}.json".format(table),
        "new_screen": True,
        "persist_trades": False,
    }


def build_entity(profession):
    description = {
        "identifier": "vm:trader_{}".format(profession),
        "is_spawnable": True,
        "is_summonable": True,
        "is_experimental": False,
    }

    # Small collision box, no physics (it hangs motionless inside the block), immovable by
    # attacks and pistons, immune to damage. No type_family: it would draw mob aggro.
    components = {
        "minecraft:collision_box": {"width": 0.9, "height": 0.9},
        "minecraft:pushable": {
            "is_pushable": False,
            "is_pushable_by_piston": False,
        },
        "minecraft:knockback_resistance": {
            "value": 100,
            "max": 100,
        },
        "minecraft:damage_sensor": {
            "triggers": {
                "cause": "all",
                "deals_damage": False,
            }
        },
        "minecraft:persistent": {},
        "minecraft:economy_trade_table": trade_table_component(profession, profession),
    }

    # Upgrading swaps in the cured table on the same entity; persist_trades false keeps the
    # re-price deterministic because every table group holds one trade with num_to_select 1.
    component_groups = {
        UPGRADED_GROUP: {
            "minecraft:economy_trade_table": trade_table_component(profession, profession + "_cured")
        }
    }

    # One event, adding only its own group: a second kit finds nothing left to add and the
    # script reports "already upgraded" instead of applying twice.
    events = {
        UPGRADE_EVENT: {
            "add": {"component_groups": [UPGRADED_GROUP]}
        }
    }

    return {
        "format_version": "1.13.0",
        "minecraft:entity": {
            "description": description,
            "components": components,
            "component_groups": component_groups,
            "events": events,
        },
    }


def _write(profession, force):
    path = os.path.join(OUTPUT_DIR, "trader_{}.json".format(profession))
    if os.path.exists(path) and not force:
        sys.exit("{} already exists; pass --force to replace it".format(path))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(build_entity(profession), fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def _remove_stale(force):
    # The old pack emitted machine_<prof>.json; the block now owns that name, so the entity
    # files must go. One by one, never a recursive delete.
    removed = 0
    for profession in PROFESSIONS:
        path = os.path.join(OUTPUT_DIR, "machine_{}.json".format(profession))
        if os.path.exists(path):
            if force:
                os.remove(path)
                removed += 1
            else:
                sys.exit("{} still exists; pass --force to remove it".format(path))
    return removed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="overwrite trader_*.json and remove stale machine_*.json")
    args = ap.parse_args()

    if not PROFESSIONS:
        sys.exit("PROFESSIONS not importable from gen_trade_tables.py")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for profession in PROFESSIONS:
        _write(profession, args.force)

    removed = _remove_stale(args.force)

    print("wrote {} trader entities to {}".format(len(PROFESSIONS), OUTPUT_DIR))
    for profession in PROFESSIONS:
        print("  trader_{}".format(profession))
    if removed:
        print("  removed {} stale machine_*.json".format(removed))


if __name__ == "__main__":
    main()
