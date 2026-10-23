r"""Check and regenerate every vending trade table from the installed game.

    python mods\vending\tools\gen_trade_tables.py            # report what would change
    python mods\vending\tools\gen_trade_tables.py --write    # regenerate all tables

Run tools\refresh_vanilla_ref.ps1 first after a game update. The tool reads each
profession's newest vanilla trade file (trade_sources.load_trade_source, which also
handles binary files), builds all 13 villager tables, the wandering trader and the
shulker tables (basic + `_cured`), adds one exact enchanted book per game
enchantment to the librarian (gen_book_trades), and prints a human-readable diff
against the shipped tables. Nothing is written without --write; --report also saves
the diff as Markdown.

Rules kept from the design:
- Villager tables keep vanilla's five tiers and XP thresholds; the engine levels the
  machine. Every "choice" line becomes one trade per option, max_uses is permanent
  and reward_exp is on. The `_cured` (upgraded) table trims every wants quantity 30%.
- Wandering trader: one tier, every native offer; the upgraded table is vanilla, the
  basic one charges more emeralds and pays fewer on buybacks (gen_extra_machines).
- Shulker: the mod's own fixed balance (gen_extra_machines).
"""

import argparse
import copy
import json
import os
import sys
from collections import Counter

from trade_sources import load_trade_source, fixture_items, game_version
import gen_book_trades as books

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
OUTPUT_DIR = os.path.join(MOD, "vending_villagers_bp", "trading", "vm")

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

# Vanilla's own tier thresholds: the five levels a machine's trader passes through.
TIER_XP = [0, 10, 60, 160, 310]

# The maximum uses stamped on every emitted trade so it never burns out.
MAX_USES = 9999999


def _tier_trades(tier):
    """Every trade in one vanilla tier: under groups[].trades or directly under trades."""
    out = []
    for group in tier.get("groups") or []:
        for trade in group.get("trades") or []:
            out.append(trade)
    for trade in tier.get("trades") or []:
        out.append(trade)
    return out


def _discounted_wants(wants):
    """Trim every wants quantity by 30% (floor 1) for the cured/upgraded variant."""
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
    """Copy wants/gives/price_multiplier/functions; keep trader_exp; make it permanent."""
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
    """One trade per variant: the machine sells every variant vanilla would roll.

    A "choice" line becomes one trade per option; a line with random_aux_value
    becomes one trade per aux value (item "minecraft:bed:3" etc., as older vanilla
    data wrote them).
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
            for f, function in enumerate(line.get("functions") or []):
                if function.get("function") == "random_aux_value":
                    base = ":".join(line["item"].split(":")[:2])
                    out = []
                    for aux in range(function["values"]["min"], function["values"]["max"] + 1):
                        variant = copy.deepcopy(trade)
                        variant[key][i]["item"] = f"{base}:{aux}"
                        del variant[key][i]["functions"][f]
                        if not variant[key][i]["functions"]:
                            del variant[key][i]["functions"]
                        out.extend(_expand_choices(variant))
                    return out
    return [trade]


# Random item functions with no deterministic expansion, removed and counted (the
# report lists them). random_dye: trade tables have no fixed-colour function for
# leather, so the item is sold undyed (owner, 2026-10-23).
STRIPPED_RANDOM = {
    "random_dye": "sold undyed (trade tables have no fixed-colour function)",
}

# Item functions that roll at trade time. None may remain in a shipped table, except
# enchant_with_levels: the owner keeps vanilla's random enchanting on gear (2026-10-23).
ALLOWED_RANDOM = {"enchant_with_levels"}
RANDOM_FUNCTIONS = {"random_dye", "random_aux_value", "random_block_state",
                    "enchant_randomly", "enchant_random_gear", "enchant_book_for_trading", "set_stew_effect",
                    "set_ominous_bottle_amplifier", "trader_material_type"}


def random_parts(table):
    """Every leftover random element in a table: [(tier, item, what)]. Empty for a fixed catalogue."""
    out = []
    for index, tier in enumerate(table["tiers"]):
        for group in tier.get("groups") or []:
            if group.get("num_to_select") != 1 or len(group.get("trades") or []) != 1:
                out.append((index, "-", f"group picks {group.get('num_to_select')} of {len(group.get('trades') or [])}"))
        for trade in _tier_trades(tier):
            for line in trade.get("wants", []) + trade.get("gives", []):
                if "choice" in line:
                    out.append((index, "-", "choice"))
                    continue
                if isinstance(line.get("quantity", 1), dict):
                    out.append((index, line["item"], "quantity range"))
                for function in line.get("functions") or []:
                    if function.get("function") in RANDOM_FUNCTIONS:
                        out.append((index, line["item"], function["function"]))
    return out


def deterministic_variants(trade, stripped=None):
    """Every fixed variant of one vanilla trade: choices and aux values expanded, the
    STRIPPED_RANDOM functions removed (counted into `stripped`, a Counter)."""
    out = []
    for variant in _expand_choices(copy.deepcopy(trade)):
        for line in (variant.get("wants") or []) + (variant.get("gives") or []):
            if isinstance(line.get("quantity"), dict):
                raise ValueError(f"quantity range on {line['item']}: no fixed-price rule yet; decide one first")
            if "functions" not in line:
                continue
            for function in line["functions"]:
                if function.get("function") in STRIPPED_RANDOM and stripped is not None:
                    stripped[function["function"]] += 1
            line["functions"] = [f for f in line["functions"] if f.get("function") not in STRIPPED_RANDOM]
            if not line["functions"]:
                del line["functions"]
        out.append(variant)
    return out


def build_table(data, cured, stripped=None):
    """Five tiers with vanilla's XP thresholds; one singleton group per distinct tier-N trade.

    Every trade of every vanilla group is kept whatever its num_to_select: the machine
    sells all M offers a villager would pick N from."""
    tiers = []
    for index, xp in enumerate(TIER_XP):
        trades = []
        for trade in _tier_trades(data["tiers"][index]):
            for variant in deterministic_variants(trade, stripped):
                if variant not in trades:  # vanilla weights a roll by repeating a trade
                    trades.append(variant)
        groups = [{"num_to_select": 1, "trades": [_emit_trade(trade, cured)]} for trade in trades]
        tiers.append({"total_exp_required": xp, "groups": groups})
    return {"tiers": tiers}


def build_all(root=None):
    """Return ({path relative to the mod: table}, [source lines], [notes])."""
    import gen_extra_machines as extra  # imports this module; load it lazily

    tables, sources, notes = {}, [], []
    enchants, book_notes = books.book_catalog(root)
    notes += book_notes
    for profession in PROFESSIONS:
        source = load_trade_source(profession, root)
        sources.append(f"{profession}: {source.path}")
        if source.note:
            notes.append(f"{profession}: {source.note}")
        stripped = Counter()
        for suffix in ("", "_cured"):
            table = build_table(source.data, suffix == "_cured", None if suffix else stripped)
            if profession == "librarian":
                books._patch(table, enchants, suffix == "_cured")
            tables[f"vending_villagers_bp/trading/vm/{profession}{suffix}.json"] = table
        notes += _stripped_notes(profession, stripped)
    wandering = load_trade_source("wandering_trader", root)
    sources.append(f"wandering_trader: {wandering.path}")
    if wandering.note:
        notes.append(f"wandering_trader: {wandering.note}")
    stripped = Counter()
    for machine, pack in (("wandering_trader", "vending_wandering_bp"), ("shulker", "vending_shulker_bp")):
        for suffix, upgraded in (("", False), ("_cured", True)):
            build = extra.TABLES[machine]
            table = build(upgraded, root, stripped) if machine == "wandering_trader" and upgraded else build(upgraded, root)
            tables[f"{pack}/trading/vm/{machine}{suffix}.json"] = table
    notes += _stripped_notes("wandering_trader", stripped)
    leftovers = {rel: parts for rel, table in tables.items() if (parts := random_parts(table))}
    if leftovers:
        raise ValueError(f"random elements left in shipped tables: {leftovers}")
    return tables, sources, notes


def _stripped_notes(machine, stripped):
    return [f"{machine}: {count} offer(s) {STRIPPED_RANDOM[name]} [{name}]" for name, count in sorted(stripped.items())]


# --- human-readable diff ----------------------------------------------------

def _short(item_id):
    return item_id.removeprefix("minecraft:")


def _quantity(line):
    quantity = line.get("quantity", 1)
    if isinstance(quantity, dict):
        return f"{quantity.get('min')}-{quantity.get('max')}"
    return str(quantity)


def _extras(line):
    out = []
    for function in line.get("functions", []):
        name = function.get("function")
        if name == "specific_enchants":
            enchant = function["enchants"]
            out.append(f"{enchant['id']} {enchant['level'][0]}")
        elif name == "exploration_map":
            out.append(f"map to {function.get('destination')}")
        elif name == "set_potion":
            out.append(function.get("id"))
        else:
            out.append(name)
    return f" [{', '.join(out)}]" if out else ""


def _side(lines, with_quantity=True):
    return " + ".join((f"{_quantity(line)} " if with_quantity else "") + _short(line["item"]) + _extras(line)
                      for line in lines)


def offers(table):
    """[(tier, key without quantities, full label)] for every trade in a table."""
    out = []
    for index, tier in enumerate(table["tiers"]):
        for trade in _tier_trades(tier):
            key = _side(trade.get("wants", []), False) + " -> " + _side(trade.get("gives", []), False)
            label = _side(trade.get("wants", [])) + " -> " + _side(trade.get("gives", []))
            out.append((index, key, label))
    return out


def diff_table(old, new):
    """[(sign, tier, key, text)] describing how `new` differs from `old`; empty when equal."""
    if old == new:
        return []
    before, after = Counter(offers(old)), Counter(offers(new))
    removed, added = list((before - after).elements()), list((after - before).elements())
    lines = []
    for tier, key, label in sorted(removed):
        match = next((a for a in added if a[0] == tier and a[1] == key), None)
        if match:
            added.remove(match)
            lines.append(("~", tier, key, f"  ~ T{tier + 1} {label}  =>  {match[2]}"))
        else:
            lines.append(("-", tier, key, f"  - T{tier + 1} {label}"))
    lines += [("+", tier, key, f"  + T{tier + 1} {label}") for tier, key, label in sorted(added)]
    if not lines:
        lines.append(("=", 0, "", "  (same offers; order, XP, multipliers or filters changed)"))
    return lines


def report(tables, sources, notes, root=None):
    out = [f"# Vending trade check against {game_version(root)}", ""]
    out += ["Flags:" if notes else "Flags: none"] + [f"- {note}" for note in notes] + [""]
    out += ["Sources:"] + [f"- {line}" for line in sources] + [""]
    changed = 0
    shown = {}
    for rel, table in tables.items():
        path = os.path.join(MOD, rel)
        old = {"tiers": []}
        if os.path.exists(path):
            with open(path, encoding="utf-8-sig") as shipped:
                old = json.load(shipped)
        lines = diff_table(old, table)
        if not lines:
            continue
        changed += 1
        name = os.path.basename(rel)
        counts = f"{len(offers(old))} -> {len(offers(table))} offers"
        shape = [line[:3] for line in lines]
        basic = name.replace("_cured", "")
        if name != basic and shape == shown.get(basic):
            out += [f"## {name}: {counts}; same changes as {basic}, at the upgraded prices", ""]
            continue
        shown[name] = shape
        out.append(f"## {name}: {counts}  (- removed, + added, ~ changed; Tn = machine level)")
        out += [line[3] for line in lines] + [""]
    out.append(f"{changed} of {len(tables)} tables change." if changed else "All tables are up to date.")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write the regenerated tables")
    ap.add_argument("--report", help="also save the diff report to this Markdown file")
    ap.add_argument("--vanilla-root", help="behavior_packs root to read instead of reference/vanilla/current")
    args = ap.parse_args()
    tables, sources, notes = build_all(args.vanilla_root)
    text = report(tables, sources, notes, args.vanilla_root)
    sys.stdout.write(text)
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as output:
            output.write(text)
    if args.write:
        for rel, table in tables.items():
            path = os.path.join(MOD, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as output:
                json.dump(table, output, ensure_ascii=False, indent=2)
                output.write("\n")
        print(f"Wrote {len(tables)} tables.")
    else:
        print("Nothing written; pass --write to regenerate.")


if __name__ == "__main__":
    main()
