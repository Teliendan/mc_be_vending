r"""Generate engine-native five-tier Bedrock trade tables for the vending machine mod.

Minecraft Bedrock only offers a limited sample of a villager's trade groups per
level-up, which makes many vanilla trades effectively unobtainable in a single
villager. The old tool fought that by flattening every profession into one flat,
level-off table and accumulating all of vanilla's trades into it. That killed
levelling; this tool turns it back on.

Each emitted file now has the five tiers vanilla already ships for the
profession, `total_exp_required` included, so the engine does its own
level-up bookkeeping exactly as it does for a villager. Tier N holds the
trades from vanilla tier N *only* -- the engine accumulates offers across the
levels itself, and a cumulative tier would duplicate every trade.

Each emitted file is one profession plus one cured variant (`_cured`). The cured
table is identical but every wants quantity is trimmed by 30% -- the flat
discount a cured trader offers. Vanilla wants/gives/price_multiplier/functions
blocks are preserved verbatim, except that "choice" lines are split into one
trade per option so the machine sells every variant; only trader_exp is
kept, max_uses is made permanent, and reward_exp is forced on so every trade
still feeds the XP bar.

Run:  python mods\vending\tools\gen_trade_tables.py [--force]
"""

import argparse
import copy
import json
import os
MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
import sys

from trade_sources import load_trade_source, fixture_items

VANILLA_ROOT = None

OUTPUT_DIR = os.path.join(MOD, "vending_villagers_bp", "trading", "vm")

# The 13 profession trade tables this tool consumes. Iterate this list to drive
# everything; adding a new source (e.g. the wandering trader) is one line, not a
# refactor, and keeps output order deterministic.
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

# Vanilla's own tier thresholds. The engine owns levelling now, so these become
# the five levels a machine's trader passes through.
TIER_XP = [0, 10, 60, 160, 310]

# The maximum uses we stamp on every emitted trade so it never burns out.
MAX_USES = 9999999

def _load(profession):
    return load_trade_source(profession, VANILLA_ROOT)[0]


def _tier_trades(tier):
    """Every trade in one vanilla tier, in order.

    Vanilla stores trades normally under tiers[i].groups[j].trades, but a few
    professions (stone_mason, and possibly others) put them directly under
    tiers[i].trades. Handle both.
    """
    out = []
    for group in tier.get("groups") or []:
        for trade in group.get("trades") or []:
            out.append(trade)
    for trade in tier.get("trades") or []:
        out.append(trade)
    return out


def _discounted_wants(wants):
    """Trim every wants quantity by 30% for the cured variant.

    A wants line is what the trader takes from the player, so fewer of anything
    is a discount no matter whether the player is buying or selling. Floor at 1.
    """
    out = []
    for want in wants:
        want = copy.deepcopy(want)
        if "quantity" in want:
            quantity = want["quantity"]
            if isinstance(quantity, dict):
                want["quantity"] = {key: max(1, round(value * 0.7)) for key, value in quantity.items()}
            else:
                want["quantity"] = max(1, round(quantity * 0.7))
        out.append(want)
    return out


def _emit_trade(trade, cured):
    """Build the emitted trade dict from a vanilla trade object.

    Carry wants/gives/price_multiplier/functions exactly as vanilla wrote them
    (deep-copied so choices are preserved untouched); keep vanilla's trader_exp
    so levelling stays engine-native, and force the two knobs that make a trade
    permanently renewable.
    """
    out = {}
    if "wants" in trade:
        out["wants"] = _discounted_wants(fixture_items(trade["wants"])) if cured else fixture_items(trade["wants"])
    if "gives" in trade:
        out["gives"] = fixture_items(trade["gives"])
    if "price_multiplier" in trade:
        out["price_multiplier"] = trade["price_multiplier"]
    if "functions" in trade:
        out["functions"] = copy.deepcopy(trade["functions"])
    out["trader_exp"] = trade.get("trader_exp", 1)
    out["max_uses"] = MAX_USES
    out["reward_exp"] = True
    return out


def _expand_choices(trade):
    """Split a vanilla trade with a "choice" line into one trade per option.

    Vanilla rolls one option per villager (the stone mason's polished stone
    variants, 16 terracotta colours, 16 glazed terracottas...). A vending machine
    should sell every variant, so each option becomes its own trade.
    """
    for key in ("wants", "gives"):
        for i, line in enumerate(trade.get(key) or []):
            if "choice" in line:
                out = []
                for option in line["choice"]:
                    variant = copy.deepcopy(trade)
                    variant[key][i] = copy.deepcopy(option)
                    out.extend(_expand_choices(variant))
                return out
    return [trade]


def build_table(data, cured):
    """Return the five-tier table for a profession, cured or not.

    Each tier carries vanilla's own total_exp_required and holds one group per
    vanilla tier-N trade (choices split into one trade per option), so the
    engine accumulates and levels on its own.
    """
    tiers = []
    for index, xp in enumerate(TIER_XP):
        trades = [t for trade in _tier_trades(data["tiers"][index]) for t in _expand_choices(trade)]
        groups = [{"num_to_select": 1, "trades": [_emit_trade(trade, cured)]} for trade in trades]
        tiers.append({"total_exp_required": xp, "groups": groups})
    return {"tiers": tiers}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="overwrite generated tables")
    ap.add_argument("--vanilla-root", help="installed behavior_packs root or explicit readable economy_trades directory")
    ap.add_argument("--profession", action="append", choices=PROFESSIONS,
                    help="regenerate only this profession; repeat to select several")
    args = ap.parse_args()
    professions = list(dict.fromkeys(args.profession or PROFESSIONS))
    # Read/build/check every selected output before writing the first file.
    sources = {p: load_trade_source(p, args.vanilla_root) for p in professions}
    outputs = [(os.path.join(OUTPUT_DIR, p + suffix + ".json"), build_table(sources[p][0], suffix == "_cured"))
               for p in professions for suffix in ("", "_cured")]
    for path, table in outputs:
        if os.path.exists(path) and not args.force:
            sys.exit(f"{path} already exists; pass --force to replace it")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for path, table in outputs:
        with open(path, "w", encoding="utf-8", newline="\n") as output:
            json.dump(table, output, ensure_ascii=False, indent=2)
            output.write("\n")
    for profession, (_, source) in sources.items():
        print(f"{profession}: {source}")


if __name__ == "__main__":
    main()
