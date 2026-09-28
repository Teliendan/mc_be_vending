r"""Replace the librarian's random book with a catalogue of every enchantment.

The vanilla librarian gets its enchantment trade from an "enchant_book_for_trading"
function, which stamps a RANDOM enchantment (and random level) onto the book each
time. A vending machine that sells a fixed catalogue cannot accept randomness: the
player must be able to buy a specific enchantment, at a specific level, for a fixed
price. This tool removes every vanilla random-book trade and appends, per tier, one
deterministic book trade for each non-curse enchantment.

The five tiers are engine-owned now, and the engine carries a lower-tier offer up into
the higher ones on its own. So each book goes to exactly one tier -- the one its
enchantment belongs to -- rather than being repeated at every tier as before. A Novice
enchantment is offered only at tier 0; a Master one only at tier 4, where the engine has
already accumulated the lower offers on top.

Every emitted book grant XP the same way the tier's other trades do (reward_exp on,
trader_exp matching the tier), because a book that pays no XP is a dead end at the top
tier. Enchantment data comes from mods/vending/tools/enchantments.json, the single source of truth.

Run:  python mods\vending\tools\gen_book_trades.py [--force]
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT, "tools")
ENCHANTS_PATH = os.path.join(TOOLS_DIR, "enchantments.json")

OUTPUT_DIR = os.path.join(
    ROOT, "vending_villagers_bp", "trading", "vm"
)

# The single profession this tool rewrites; every other table is left untouched.
PROFESSION = "librarian"

# gen_trade_tables lives in the same tools/ directory; put it on the path so this
# script stays import-safe regardless of the caller's working directory.
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)


def _load_enchants():
    if not os.path.exists(ENCHANTS_PATH):
        sys.exit("missing enchantment source: {}".format(ENCHANTS_PATH))
    with open(ENCHANTS_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    # Each entry is a dict {max_level, treasure, curse, tier}; accept that directly.
    return dict(data.get("enchants", {}))


def _load_table(name):
    path = os.path.join(OUTPUT_DIR, name + ".json")
    if not os.path.exists(path):
        sys.exit("missing base table: {}".format(path))
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _is_random_book_trade(trade):
    """True when the trade's book is stamped by the vanilla random enchanter."""
    for entry in trade.get("gives") or []:
        for fn in entry.get("functions") or []:
            if fn.get("function") == "enchant_book_for_trading":
                return True
    return False


def _price_for(spec):
    """Emerald price for a book: grows with the enchantment's max level.

    price = round(2 + 3*level + 2.5 + 5*level), doubled for treasure enchantments,
    clamped to at most 64. The +2.5 and the treasure double keep treasures and
    higher levels visibly dearer; it never floors below 1.
    """
    level = spec["max_level"]
    price = round(2 + 3 * level + 2.5 + 5 * level)
    if spec["treasure"]:
        price *= 2
    return min(price, 64)


def _book_group(ident, spec, tier_exp, cured):
    """Build one deterministic book trade group for a single enchantment.

    The book is the whole point of the tier, so it costs emeralds only -- the player
    still supplies the blank book to enchant. trader_exp is the tier's own, so the
    trade feeds the XP bar like the trades around it; reward_exp is forced on so it is
    never a dead end at the top tier.
    """
    level = spec["max_level"]
    group = {
        "num_to_select": 1,
        "trades": [
            {
                "wants": [
                    {
                        "item": "minecraft:emerald",
                        "quantity": _price_for(spec),
                        "price_multiplier": 1.0,
                    },
                    {"item": "minecraft:book", "quantity": 1},
                ],
                "gives": [
                    {
                        "item": "minecraft:enchanted_book",
                        "quantity": 1,
                        "functions": [
                            {
                                "function": "specific_enchants",
                                "enchants": {
                                    "id": ident,
                                    "level": [level, level],
                                },
                            }
                        ],
                    }
                ],
                "trader_exp": tier_exp,
                "max_uses": 9999999,
                "reward_exp": True,
            }
        ],
    }
    if cured:
        # The cured trader undercuts on everything: trim the emerald the same 30%
        # the base trade tables do. book(1) floors back to 1, so nothing shrinks
        # below a single item.
        for want in group["trades"][0]["wants"]:
            if "quantity" in want:
                want["quantity"] = max(1, round(want["quantity"] * 0.7))
    return group


def _patch(table,enchants, cured):
    """Strip the random-book trade from each tier, append one book per enchantment.

    Books land at the tier their enchantment belongs to, not at every tier: the
    engine accumulates the lower offers itself. Each book's trader_exp is the tier's
    own richest trade, so it grants XP like its neighbours; the Master tier's only
    vanilla trade pays nothing, so there it falls back to the richest tier overall.
    """
    exp_by_tier = []
    for tier in table["tiers"]:
        tier["groups"] = [
            g for g in tier["groups"] if not _is_random_book_trade(g["trades"][0])
        ]
        exp_by_tier.append(max((g["trades"][0]["trader_exp"] for g in tier["groups"]), default=0))
    fallback = max(exp_by_tier)

    added = 0
    for index, tier in enumerate(table["tiers"]):
        tier_exp = exp_by_tier[index] or fallback
        for ident, spec in enchants.items():
            if spec["curse"] or spec["tier"] != index:
                continue
            tier["groups"].append(_book_group(ident, spec, tier_exp, cured))
            added += 1
    return added


def _count_books(table):
    """Number of book trades per tier, for the run summary."""
    out = []
    for tier in table["tiers"]:
        count = 0
        for group in tier["groups"]:
            for trade in group["trades"]:
                if any(w.get("item") == "minecraft:enchanted_book" for w in trade.get("gives") or []):
                    count += 1
        out.append(count)
    return out


def _remove_tier_files():
    # gen_book_trades used to write one file per tier; drop any leftovers so the
    # directory only holds the two per-profession tables.
    for tier in range(5):
        old = os.path.join(OUTPUT_DIR, "{}_t{}.json".format(PROFESSION, tier))
        if os.path.exists(old):
            os.remove(old)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--force",
        action="store_true",
        help="overwrite the table if it already exists",
    )
    args = ap.parse_args()

    enchants = _load_enchants()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    grand = 0
    for suffix in ("", "_cured"):
        path = os.path.join(OUTPUT_DIR, "{}{}.json".format(PROFESSION, suffix))
        if os.path.exists(path) and not args.force:
            sys.exit("{} already exists; pass --force to replace it".format(path))
        table = _load_table(PROFESSION + suffix)
        added = _patch(table,enchants, cured=(suffix == "_cured"))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(table, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print("{}{}: {} book trades, per tier {}".format(PROFESSION, suffix, added, _count_books(table)))
        grand += added

    _remove_tier_files()
    print("TOTAL: {} book trades across 5 tiers".format(grand))


if __name__ == "__main__":
    main()
