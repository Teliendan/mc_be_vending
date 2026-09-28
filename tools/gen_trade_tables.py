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
blocks (including "choice" arrays) are preserved verbatim; only trader_exp is
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

VANILLA_ROOT = r"E:\AI\ref\bedrock\current\behavior_packs\vanilla\trading\economy_trades"

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

# The number of trades vanilla ships per profession across all five tiers. Tier
# N now holds exactly vanilla tier N's trades, so this is also the per-profession
# total the new layout must preserve -- a guard that no trade was dropped.
EXPECTED_TRADE_COUNTS = {
    "farmer": 15,
    "fisherman": 17,
    "shepherd": 86,
    "fletcher": 26,
    "librarian": 14,
    "cartographer": 27,
    "cleric": 11,
    "armorer": 18,
    "weapon_smith": 9,
    "tool_smith": 16,
    "butcher": 14,
    "leather_worker": 12,
    "stone_mason": 9,
}


def _input_path(profession):
    return os.path.join(VANILLA_ROOT, profession + "_trades.json")


def _load(profession):
    path = _input_path(profession)
    if not os.path.exists(path):
        sys.exit("missing input file for profession {}: {}".format(profession, path))
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


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
            want["quantity"] = max(1, round(want["quantity"] * 0.7))
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
        out["wants"] = _discounted_wants(trade["wants"]) if cured else copy.deepcopy(trade["wants"])
    if "gives" in trade:
        out["gives"] = copy.deepcopy(trade["gives"])
    if "price_multiplier" in trade:
        out["price_multiplier"] = trade["price_multiplier"]
    if "functions" in trade:
        out["functions"] = copy.deepcopy(trade["functions"])
    out["trader_exp"] = trade["trader_exp"]
    out["max_uses"] = MAX_USES
    out["reward_exp"] = True
    return out


def build_table(data, cured):
    """Return the five-tier table for a profession, cured or not.

    Each tier carries vanilla's own total_exp_required and holds one group per
    vanilla tier-N trade, so the engine accumulates and levels on its own.
    """
    tiers = []
    for index, xp in enumerate(TIER_XP):
        trades = _tier_trades(data["tiers"][index])
        groups = [{"num_to_select": 1, "trades": [_emit_trade(trade, cured)]} for trade in trades]
        tiers.append({"total_exp_required": xp, "groups": groups})
    return {"tiers": tiers}


def _write_table(profession, force):
    for suffix in ("", "_cured"):
        path = os.path.join(OUTPUT_DIR, "{}{}.json".format(profession, suffix))
        if os.path.exists(path) and not force:
            sys.exit("{} already exists; pass --force to replace it".format(path))
        table = build_table(_load(profession), cured=(suffix == "_cured"))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(table, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    # The old layout wrote one file per tier; remove those so the directory only
    # holds the new per-profession files.
    for tier in range(5):
        old = os.path.join(OUTPUT_DIR, "{}_t{}.json".format(profession, tier))
        if os.path.exists(old):
            os.remove(old)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="overwrite outputs that already exist")
    args = ap.parse_args()

    if not os.path.isdir(VANILLA_ROOT):
        sys.exit("vanilla reference dir not found at {}".format(VANILLA_ROOT))
    for profession in PROFESSIONS:
        if not os.path.exists(_input_path(profession)):
            sys.exit("missing input file for profession {}".format(profession))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for profession in PROFESSIONS:
        _write_table(profession, args.force)

    total = 0
    for profession in PROFESSIONS:
        data = _load(profession)
        count = sum(len(_tier_trades(data["tiers"][i])) for i in range(5))
        print("{}: {}".format(profession, count))
        total += count
    print("TOTAL: {}".format(total))

    for profession, expected in EXPECTED_TRADE_COUNTS.items():
        actual = sum(len(_tier_trades(_load(profession)["tiers"][i])) for i in range(5))
        assert actual == expected, (
            "{}: got {} trades across tiers, expected {}".format(
                profession, actual, expected)
        )
    assert total == sum(EXPECTED_TRADE_COUNTS.values()), (
        "grand total {} != {}".format(total, sum(EXPECTED_TRADE_COUNTS.values()))
    )


if __name__ == "__main__":
    main()
