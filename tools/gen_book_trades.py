r"""Replace the librarian's random book with one exact book per enchantment.

The vanilla librarian stamps a RANDOM enchantment onto its book trade
("enchant_book_for_trading"). A vending machine sells a fixed catalogue, so this
module removes every random-book trade and adds one deterministic book (max level,
fixed emerald price) per non-curse enchantment, on the tier its policy names. The
engine carries lower-tier offers up on its own, so each book appears on one tier.

Which enchantments exist comes from the game (trade_sources.game_enchantments), so a
new enchantment gets a book automatically. tools/enchantments.json adds the vanilla
max level, treasure/curse flags and the mod's tier. An enchantment the game has but
the policy lacks is sold at level 1 on the Master tier and reported as NEW.

Library only: gen_trade_tables.py calls it when it rebuilds the librarian tables.
"""
import json
from pathlib import Path

from trade_sources import game_enchantments

ENCHANTS_PATH = Path(__file__).with_name('enchantments.json')
DEFAULT_POLICY = {'max_level': 1, 'treasure': False, 'curse': False, 'tier': 4}


def _load_enchants():
    """The policy file only (no game data)."""
    return dict(json.loads(ENCHANTS_PATH.read_text(encoding='utf-8'))['enchants'])


def book_catalog(root=None):
    """(enchants, notes): every game enchantment with its policy, plus what needs a look."""
    policy = _load_enchants()
    game = game_enchantments(root)
    notes = []
    # Policy order first keeps the shipped table order stable; new ones follow.
    enchants = {ident: spec for ident, spec in policy.items() if ident in game}
    for ident in game:
        if ident not in policy:
            enchants[ident] = dict(DEFAULT_POLICY)
            notes.append(f'NEW enchantment {ident}: sold at level 1 on tier 4. Add its max_level/treasure/tier '
                         f'to tools/enchantments.json and run again.')
    for ident in policy:
        if ident not in game:
            notes.append(f'Enchantment {ident} is in tools/enchantments.json but not in the game; no book generated.')
    return enchants, notes


def _is_random_book_trade(trade):
    """True when the trade's book is stamped by the vanilla random enchanter."""
    for entry in trade.get("gives") or []:
        for fn in entry.get("functions") or []:
            if fn.get("function") == "enchant_book_for_trading":
                return True
    return False


def _price_for(spec):
    """Emerald price: round(4.5 + 8*level), doubled for treasure, at most 64."""
    level = spec["max_level"]
    price = round(2 + 3 * level + 2.5 + 5 * level)
    if spec["treasure"]:
        price *= 2
    return min(price, 64)


def _book_group(ident, spec, tier_exp, cured):
    """One deterministic book trade: emeralds + a book, XP like its tier's trades."""
    level = spec["max_level"]
    emeralds = _price_for(spec)
    if cured:
        emeralds = max(1, round(emeralds * 0.7))  # the same 30% cut as every cured table
    return {
        "num_to_select": 1,
        "trades": [{
            "wants": [
                {"item": "minecraft:emerald", "quantity": emeralds, "price_multiplier": 1.0},
                {"item": "minecraft:book", "quantity": 1},
            ],
            "gives": [{
                "item": "minecraft:enchanted_book",
                "quantity": 1,
                "functions": [{"function": "specific_enchants", "enchants": {"id": ident, "level": [level, level]}}],
            }],
            "trader_exp": tier_exp,
            "max_uses": 9999999,
            "reward_exp": True,
        }],
    }


def _patch(table, enchants, cured):
    """Strip random and previously generated books, then add one book per enchantment.

    Each book's trader_exp is its tier's richest remaining trade; the Master tier's
    only vanilla trade pays nothing, so there it falls back to the richest tier.
    Idempotent: running it twice gives the same table.
    """
    def owned_book(trade):
        for line in trade.get("gives", []):
            if line.get("item") != "minecraft:enchanted_book":
                continue
            for function in line.get("functions", []):
                if function.get("function") == "specific_enchants" and function.get("enchants", {}).get("id") in enchants:
                    return True
        return _is_random_book_trade(trade)

    exp_by_tier = []
    for tier in table["tiers"]:
        tier["groups"] = [g for g in tier["groups"] if not owned_book(g["trades"][0])]
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
