r"""Evaluate which items a "Peaceful resource" vending machine should sell.

    python -I mods\vending\tools\gen_peaceful_catalog.py            # write the catalogue and the audit report
    python -I mods\vending\tools\gen_peaceful_catalog.py --check    # exit 1 if the written files would change
    python -I mods\vending\tools\gen_peaceful_catalog.py --rules PATH   # another rules file (testing);
                                                                        # writes to <PATH minus .json>_out/, never to tools/ or docs/
    ... --out DIR                    # write both files into DIR instead

Reads   tools/peaceful_rules.json (hand-maintained knowledge; keys starting with "_" are ignored)
        and the layered vanilla game data via peaceful_sources.py.
Writes  tools/peaceful_catalog.json  (machine-readable: included items, quantity, price, upgraded price, stage)
        docs/peaceful-catalog.md     (audit report: every evaluated item with decision, reasons, sources,
                                      craft check and price derivation, plus what needs the owner's review)
Output is deterministic (sorted, LF). Nothing in a pack is touched.

The engine (docs/peaceful-machine.md has the owner decisions; temp plan "B. Tooling"):
 1. Candidates: items in the loot/equipment tables of `peaceful_mobs.absent` mobs, plus the keys of `special`.
 2. Sources per candidate: automatic (mob tables, chests, vaults, fishing, gifts, archaeology, barter, ...)
    plus the hand-written `sources` of the rules. Each source has a class: EASY, LIMITED or UNAVAILABLE.
    Mob tables: absent mob = UNAVAILABLE, `present_breedable` = EASY, any other present mob = LIMITED.
 3. Excluded when a villager, the wandering trader or one of this mod's machines SELLS it, or when any
    source is EASY.
 4. Unreachable set U = the remaining candidates. A U item is excluded as "crafted" when a recipe has all
    ingredients accessible. Accessible = a non-U item with a known source (or without any recipe), a
    non-U item with a recipe whose ingredients are all accessible, or a U item the machine sells. "Tainted"
    items (no known source, every recipe needs a U item or another tainted item) are listed in the report.
    Run to a fixed point; mutually crafted U items are resolved in alphabetical order, the other one stays.
 5. `decisions` of the rules (include / exclude / review) override the automatic result; the reason is shown.
 6. Price: price = ceil(B[class] * M[stage] / yield) emeralds for `quantity` items (quantity is raised for cheap
    items so a trade costs at least 1 emerald), unless `price_overrides` gives the price (the report shows the
    formula value next to it). Emeralds only, at most 128: `wants` splits the price into stacks of 64 (90 = 64 + 26);
    a higher price is clamped to 128 with a review note. `upgraded_wants` = the Upgrade Kit rule of
    gen_trade_tables._discounted_wants (per entry max(1, round(q * 0.7))). The class comes from
    `acquisition_class` (item first, else the origin mob), the stage from `item_stage`.
    An included item missing a yield, class or stage becomes `review`; nothing crashes on missing rules data.
 7. Both files are written sorted and with LF line endings, and a short summary is printed.

Ingredient classes: `ingredient_class` (item -> EASY / LIMITED / UNAVAILABLE) classes ingredients. A recipe
excludes an item only when every ingredient is EASY (listed as EASY, or a no-recipe item with no entry, which
defaults to EASY and is listed under "Needs owner review"); a recipe with a LIMITED ingredient adds a LIMITED
"craft" source instead and the item stays. UNAVAILABLE ingredients follow the U logic. This applies recursively.

Yield rules (first match): `yield_overrides` > `special[...].yield` > loot-table expected count of the best
absent-mob source (expected count per one kill, killed by a player, base chances, no Looting).
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I does not add the script folder
from peaceful_sources import DEFAULT_CLASS, display_id, load_game_data, normalise_id  # noqa: E402

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root
RULES_PATH = os.path.join(MOD, "tools", "peaceful_rules.json")
CATALOG_PATH = os.path.join(MOD, "tools", "peaceful_catalog.json")
REPORT_PATH = os.path.join(MOD, "docs", "peaceful-catalog.md")

CLASSES = ("EASY", "LIMITED", "UNAVAILABLE")
MAX_QUANTITY = 64          # one trade gives at most one stack
MAX_PRICE = 128            # two wants slots of one stack (64) each; prices are emeralds only
STACK = 64
LIMITED_TOKEN = "~"        # in a derivation: a LIMITED ingredient (ingredient_class)
ASSUMED_TOKEN = "?"        # in a derivation: a no-recipe ingredient assumed EASY (no ingredient_class entry)
SOURCE_LINE_TABLES = 6     # tables shown per source kind in the report


# --------------------------------------------------------------------------------------
# rules

def _mob(name):
    return str(name).removeprefix("minecraft:")


def _keyed(rules, name):
    """rules[name] as {normalised item id: entry}, dropping keys that start with "_"."""
    section = rules.get(name) or {}
    return {normalise_id(key): value for key, value in section.items() if not key.startswith("_")}


class Rules:
    def __init__(self, path):
        with open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
        self.raw = raw
        self.path = path
        self.game_version = raw.get("game_version")
        mobs = raw.get("peaceful_mobs") or {}
        self.absent = {_mob(m) for m in mobs.get("absent", [])}
        self.breedable = {_mob(m) for m in mobs.get("present_breedable", [])}
        self.limited = {_mob(m) for m in mobs.get("present_limited", [])}
        self.sources = {item: list(entries) if isinstance(entries, list) else [entries]
                        for item, entries in _keyed(raw, "sources").items()}
        self.special = _keyed(raw, "special")
        self.yield_overrides = _keyed(raw, "yield_overrides")
        self.item_stage = _keyed(raw, "item_stage")
        self.decisions = _keyed(raw, "decisions")
        self.ingredient_class = _keyed(raw, "ingredient_class")
        self.price_overrides = _keyed(raw, "price_overrides")
        # acquisition_class keys are items or mobs
        self.class_rules = {}
        for key, value in (raw.get("acquisition_class") or {}).items():
            if not key.startswith("_"):
                self.class_rules[key] = value
        stages = (raw.get("stages") or {}).get("order") or []
        self.stages = [s for s in stages if not str(s).startswith("_")]
        pricing = raw.get("pricing") or {}
        self.base = {k: self._number(v, ("B", "base", "value")) for k, v in (pricing.get("classes") or {}).items() if not k.startswith("_")}
        self.multiplier = {k: self._number(v, ("M", "multiplier", "value")) for k, v in (pricing.get("stage_multiplier") or {}).items() if not k.startswith("_")}
        self.anchors = pricing.get("anchors") or []
        self.mob_stage = {}

    @staticmethod
    def _number(value, names):
        if isinstance(value, dict):
            for name in names:
                if isinstance(value.get(name), (int, float)):
                    return float(value[name])
            return None
        return float(value) if isinstance(value, (int, float)) else None

    def class_of(self, item, mob):
        """(class name, reason) from acquisition_class: the item first, then the origin mob."""
        for key in (item, item.removeprefix("minecraft:")):
            entry = self.class_rules.get(key) or self.class_rules.get(normalise_id(key))
            if entry:
                return entry.get("class"), f"acquisition_class[{item}]: {entry.get('reason', '')}".rstrip(": ")
        if mob:
            for key in (mob, "minecraft:" + mob):
                if key in self.class_rules:
                    entry = self.class_rules[key]
                    return entry.get("class"), f"acquisition_class[{mob}]: {entry.get('reason', '')}".rstrip(": ")
        return None, None


# --------------------------------------------------------------------------------------
# the engine

class Engine:
    def __init__(self, rules, data):
        self.rules, self.data = rules, data
        self.review = defaultdict(list)       # section -> lines for "Needs owner review"
        self.unclassified_mobs = set()
        self.items = {}                       # candidate id -> evaluation record
        self.sources = {}                     # item id -> classified source list (automatic + rules)
        self.run()

    # -- sources ----------------------------------------------------------------------
    def mob_class(self, mob):
        if mob in self.rules.absent:
            return "UNAVAILABLE"
        if mob in self.rules.breedable:
            return "EASY"
        if mob not in self.rules.limited:
            self.unclassified_mobs.add(mob)
        return "LIMITED"

    def source_class(self, src):
        if src["kind"] in ("mob_loot", "mob_equipment"):
            return self.mob_class(src["mob"])
        return DEFAULT_CLASS[src["kind"]]

    def classified_sources(self, item):
        out = []
        for src in self.data.sources.get(item, []):
            out.append({**src, "class": self.source_class(src), "origin": "data"})
        for entry in self.rules.sources.get(item, []):
            cls = str(entry.get("class", "")).upper()
            out.append({"kind": entry.get("kind", "?"), "ref": entry.get("detail", ""), "mob": None, "expected": None,
                        "notes": [], "unknown": [], "class": cls if cls in CLASSES else "?", "origin": "rules",
                        "reason": entry.get("reason", ""), "wiki": entry.get("ref", "")})
        return out

    def run(self):
        rules, data = self.rules, self.data
        candidates = set(rules.special)
        origins = defaultdict(list)
        for item, sources in data.sources.items():
            for src in sources:
                if src["kind"] in ("mob_loot", "mob_equipment") and src["mob"] in rules.absent:
                    candidates.add(item)
                    origins[item].append(src)
        self.candidates = candidates
        for item in sorted(candidates):
            self.sources[item] = self.classified_sources(item)
        # step 3: sold elsewhere or an EASY source
        self.step3 = {}
        for item in sorted(candidates):
            sold = data.sold.get(item, [])
            easy = [s for s in self.sources[item] if s["class"] == "EASY"]
            if sold:
                self.step3[item] = ("sold", "sold by " + ", ".join(sold))
            elif easy:
                first = easy[0]
                self.step3[item] = ("easy", f"EASY source: {first['kind']} {first['mob'] or first['ref']}"
                                    + (f" (+{len(easy) - 1} more)" if len(easy) > 1 else ""))
        # known sources of non-U items, for accessibility
        self.known = set(data.sold)
        for item, sources in data.sources.items():
            if item not in candidates and any(self.source_class(s) != "UNAVAILABLE" for s in sources):
                self.known.add(item)
        for item, entries in rules.sources.items():
            if any(str(e.get("class", "")).upper() != "UNAVAILABLE" for e in entries):
                self.known.add(item)
        self.known |= set(self.step3)
        self.u_all = {item for item in candidates if item not in self.step3}
        for item, entry in rules.decisions.items():
            if item in candidates and entry.get("decision") == "include":
                self.u_all.add(item)
        self.origins = origins
        self.fixed_point()
        self.tainted = self.find_tainted()
        for item in sorted(candidates):
            self.items[item] = self.evaluate(item)
        self.collect_review()

    # -- accessibility ----------------------------------------------------------------
    def closure(self, deps):
        """Expand dependencies to the U items the machine still sells."""
        out, todo, seen = set(), list(deps), set()
        while todo:
            item = todo.pop()
            if item in seen:
                continue
            seen.add(item)
            if item.startswith((LIMITED_TOKEN, ASSUMED_TOKEN)):
                out.add(item)
            elif self.state.get(item) == "included":
                out.add(item)
            elif self.state.get(item) == "crafted":
                todo.extend(self.crafted[item]["deps"])
        return out

    def proof(self, item, target, stack, memo):
        """Set of sold U items a derivation of `item` needs, or None when it is not accessible."""
        if item == target:
            return None
        if item.startswith("#"):
            return frozenset()  # tag the data does not define: assume common
        if item in memo:
            return memo[item]
        if item in self.state:
            state = self.state[item]
            if state == "owner_excluded":
                result = frozenset()
            elif state == "included":
                result = frozenset([item])
            else:
                deps = self.closure(self.crafted[item]["deps"])
                result = None if target in deps else frozenset(deps)
        elif item in self.rules.ingredient_class:
            cls = str(self.rules.ingredient_class[item].get("class", "")).upper()
            result = {"EASY": frozenset(), "LIMITED": frozenset([LIMITED_TOKEN + item])}.get(cls)  # UNAVAILABLE or invalid: no
        elif item not in self.data.recipes:
            result = frozenset() if item in self.data.sold else frozenset([ASSUMED_TOKEN + item])
        elif item in self.known:
            result = frozenset()
        elif item in stack:
            return None
        else:
            result = None
            for recipe in self.sorted_recipes(item):
                found = self.recipe_proof(recipe, target, stack | {item}, memo)
                if found is not None and (result is None or _limited(result) and not _limited(found)):
                    result = found  # prefer a derivation without LIMITED ingredients
                if result is not None and not _limited(result):
                    break
        memo[item] = result
        return result

    def sorted_recipes(self, item):
        rank = {"shaped": 0, "shapeless": 1, "furnace": 2, "smithing_transform": 3}  # crafting first, smelting tools last
        return sorted(self.data.recipes.get(item, []), key=lambda r: (rank.get(r["kind"], 9), r["kind"], r["id"]))

    def recipe_proof(self, recipe, target, stack, memo):
        deps = set()
        for alternatives in recipe["ingredients"]:
            best = None
            for alt in alternatives:
                found = self.proof(alt, target, stack, memo)
                if found is not None and (best is None or _limited(best) and not _limited(found)):
                    best = found
                if best is not None and not _limited(best):
                    break
            if best is None:
                return None
            deps |= best
        return frozenset(deps)

    def best_recipe(self, item):
        """(recipe, deps, limited) of the best recipe: all-EASY first, else one with LIMITED ingredients, else None."""
        fallback = None
        for recipe in self.sorted_recipes(item):
            deps = self.recipe_proof(recipe, item, frozenset({item}), {})
            if deps is None:
                continue
            if not _limited(deps):
                return recipe, deps, False
            fallback = fallback or (recipe, deps, True)
        return fallback

    def fixed_point(self):
        decisions = self.rules.decisions
        self.state, self.crafted, self.forced_craftable, self.limited_craft = {}, {}, {}, {}
        for item in self.u_all:
            self.state[item] = "owner_excluded" if decisions.get(item, {}).get("decision") == "exclude" else "included"
        changed = True
        while changed:
            changed = False
            for item in sorted(i for i, s in self.state.items() if s == "included"):
                if decisions.get(item, {}).get("decision") == "include":
                    continue  # owner keeps it for sale; see forced_craftable below
                best = self.best_recipe(item)
                if best and not best[2]:
                    self.state[item] = "crafted"
                    self.crafted[item] = {"recipe": best[0], "deps": sorted(best[1])}
                    changed = True
        for item in self.crafted:  # deps were recorded while later items were still for sale: keep only what is sold now
            self.crafted[item]["deps"] = sorted(self.closure(self.crafted[item]["deps"]))
        for item in sorted(self.u_all):
            if self.state[item] != "included":
                continue
            best = self.best_recipe(item)  # a LIMITED craft source does not exclude the item
            if best and best[2]:
                self.limited_craft[item] = {"recipe": best[0], "deps": sorted(best[1])}
            elif best and decisions.get(item, {}).get("decision") == "include":
                self.forced_craftable[item] = {"recipe": best[0], "deps": sorted(best[1])}

    def find_tainted(self):
        """Non-U items without a known source whose every recipe needs an unreachable (sold) or tainted item.
        Unreachable = the U items that stay for sale after the craft check; crafted ones are accessible."""
        tainted = {}
        unreachable = {item for item, state in self.state.items() if state == "included"}
        changed = True
        while changed:
            changed = False
            for item in sorted(self.data.recipes):
                if item in tainted or item in self.known or item in self.state:
                    continue
                needs = set()
                for recipe in self.data.recipes[item]:
                    hit = set()
                    for alternatives in recipe["ingredients"]:
                        if alternatives and all(a in unreachable or a in tainted for a in alternatives):
                            hit |= set(alternatives)
                    if not hit:
                        break
                    needs |= hit
                else:
                    tainted[item] = sorted(needs)
                    changed = True
        return tainted

    def craft_blockers(self, item):
        """For an item that is sold: per recipe, the ingredient slots with no accessible alternative."""
        out = []
        for recipe in self.sorted_recipes(item):
            missing = []
            for alternatives in recipe["ingredients"]:
                if all(self.proof(alt, item, frozenset({item}), {}) is None for alt in alternatives):
                    missing.append(" or ".join(alternatives))
            out.append((recipe, missing))
        return out

    # -- per item ---------------------------------------------------------------------
    def evaluate(self, item):
        rules, data = self.rules, self.data
        rec = {"item": item, "reasons": [], "unknown": [], "missing": []}
        special = rules.special.get(item)
        origin_srcs = sorted(self.origins.get(item, []), key=lambda s: (-s["expected"], s["mob"] or "", s["ref"]))
        rec["origins"] = origin_srcs
        if special:
            rec["reasons"].append(f"special mechanic: {special.get('mechanic', '?')} (unavailable because: {special.get('why_unavailable', '?')})")
        mobs = sorted({s["mob"] for s in origin_srcs})
        if mobs:
            rec["reasons"].append("drops from Peaceful-absent mobs: " + ", ".join(mobs))
        # automatic result
        step = self.step3.get(item)
        decision = rules.decisions.get(item)
        if step:
            auto, why = "exclude", step[1]
        elif self.state.get(item) == "crafted" or item in self.forced_craftable:
            crafted = self.crafted.get(item) or self.forced_craftable[item]
            recipe = crafted["recipe"]
            parts = [" or ".join(a) for a in recipe["ingredients"]]
            auto = "exclude"
            why = f"craftable ({recipe['kind']} {recipe['id']} at {'/'.join(recipe['station']) or '?'}) from " + ", ".join(parts)
            sold = [d for d in crafted["deps"] if not d.startswith((LIMITED_TOKEN, ASSUMED_TOKEN))]
            if sold:
                why += "; needs items the machine sells: " + ", ".join(sold)
            assumed = [d[1:] for d in crafted["deps"] if d.startswith(ASSUMED_TOKEN)]
            if assumed:
                why += "; assumes EASY (no recipe, no ingredient_class): " + ", ".join(assumed)
        else:
            auto, why = "include", "no seller, no EASY source and no craftable recipe from accessible items"
        rec["auto"], rec["reasons"] = auto, rec["reasons"] + [f"automatic: {auto} ({why})"]
        rec["auto_kind"] = step[0] if step else ("crafted" if auto == "exclude" else "include")
        rec["state"] = self.state.get(item, "n/a")
        rec["limited_craft"] = item in self.limited_craft
        rec["sold_by"] = data.sold.get(item, [])
        rec["sources"] = list(self.sources[item])
        if item in self.limited_craft:
            limited = self.limited_craft[item]
            rec["sources"].append({"kind": "craft", "ref": limited["recipe"]["id"], "mob": None, "expected": None, "notes": [],
                                   "unknown": [], "class": "LIMITED", "origin": "craft",
                                   "reason": "LIMITED ingredients: " + ", ".join(d[1:] for d in limited["deps"] if d.startswith(LIMITED_TOKEN))})
        rec["craft_blockers"] = self.craft_blockers(item) if rec["auto_kind"] == "include" else []
        # decision override
        final = auto
        if decision and decision.get("decision") in ("include", "exclude", "review"):
            final = decision["decision"]
            rec["reasons"].append(f"decision {final} by {decision.get('by', '?')} {decision.get('date', '')}: "
                                  f"{decision.get('reason', '(no reason given)')}".replace("  ", " "))
            rec["decision"] = decision
        elif decision:
            rec["reasons"].append(f"decision entry ignored: unknown value {decision.get('decision')!r}")
        # yield, class, stage, price
        rec["yield"] = self.pick_yield(item, special, origin_srcs)
        rec["class"], rec["class_reason"] = self.pick_class(item, special, rec["yield"])
        rec["stage"], rec["stage_reason"] = self.pick_stage(item, special)
        rec["price"] = self.price(rec["yield"], rec["class"], rec["stage"], rules.price_overrides.get(item))
        if final == "include":
            overridden = item in rules.price_overrides and isinstance(rules.price_overrides[item].get("price"), int)
            for name, value in (("yield", rec["yield"]["value"]), ("class", rec["class"]), ("stage", rec["stage"])):
                if value is None and not (overridden and name != "stage"):
                    rec["missing"].append(name)
            if rec["price"] is None and not rec["missing"]:
                rec["missing"].append("pricing coefficient (B for the class or M for the stage)")
            if rec["missing"]:
                final = "review"
                rec["reasons"].append("review: missing " + ", ".join(rec["missing"]))
        if rec["yield"]["unknown"]:
            rec["unknown"] = rec["yield"]["unknown"]
        rec["final"] = final
        return rec

    def pick_yield(self, item, special, origin_srcs):
        rules = self.rules
        loot = [s for s in origin_srcs if s["kind"] == "mob_loot"]
        best = loot[0] if loot else None
        out = {"value": None, "attempt": None, "basis": None, "unknown": [], "notes": [], "mob": best["mob"] if best else None}
        if item in rules.yield_overrides and isinstance(rules.yield_overrides[item].get("yield"), (int, float)):
            entry = rules.yield_overrides[item]
            out.update(value=float(entry["yield"]), attempt=entry.get("attempt", "one attempt"),
                       basis=f"yield_overrides: {entry.get('reason', '')}")
        elif special and isinstance(special.get("yield"), (int, float)):
            out.update(value=float(special["yield"]), attempt=special.get("attempt", "one attempt"),
                       basis=f"special: {special.get('mechanic', '')}")
        elif best:
            out.update(value=best["expected"], attempt=f"one {best['mob']} kill (loot table {best['ref']})",
                       basis="loot table expected value", unknown=list(best["unknown"]), notes=list(best["notes"]))
        elif origin_srcs:
            out["basis"] = "equipment-only source: drop chance not modelled; set yield_overrides"
        else:
            out["basis"] = "no data source"
        return out

    def pick_class(self, item, special, yld):
        cls, reason = self.rules.class_of(item, yld["mob"])
        if cls is None and special and special.get("acquisition_class"):
            cls, reason = special["acquisition_class"], f"special[{item}].acquisition_class"
        return cls, reason

    def pick_stage(self, item, special):
        entry = self.rules.item_stage.get(item)
        if entry and entry.get("stage"):
            stage, reason = entry["stage"], entry.get("reason", "")
        elif special and special.get("stage"):
            stage, reason = special["stage"], f"special[{item}].stage"
        else:
            return None, None
        if self.rules.stages and stage not in self.rules.stages:
            return None, f"unknown stage {stage!r} (stages: {', '.join(self.rules.stages)})"
        return stage, reason

    def price(self, yld, cls, stage, override=None):
        """Emeralds only, at most MAX_PRICE; `wants` holds the stacks (a second slot carries the excess)."""
        value = yld["value"]
        base, mult = self.rules.base.get(cls), self.rules.multiplier.get(stage)
        formula = None
        if value and value > 0 and base is not None and mult is not None:
            per_item = base * mult / value
            quantity = 1 if per_item >= 1 else min(MAX_QUANTITY, math.ceil(1 / per_item - 1e-9))
            formula = {"per_item": per_item, "quantity": quantity, "emeralds": max(1, math.ceil(quantity * per_item - 1e-9))}
        note = None
        if isinstance(override, dict) and isinstance(override.get("price"), int) and override["price"] >= 1:
            total, quantity = override["price"], int(override.get("quantity", 1))
            note = f"price_overrides ({override.get('by', '?')} {override.get('date', '')}): {override.get('reason', '')}".replace("  ", " ")
        elif formula:
            total, quantity = formula["emeralds"], formula["quantity"]
        else:
            return None
        if total > MAX_PRICE:
            note = (note + "; " if note else "") + f"price {total} exceeds {MAX_PRICE} emeralds, clamped"
            total = MAX_PRICE
        wants = wants_of(total)
        upgraded = discounted_wants(wants)
        return {"B": base, "M": mult, "yield": value, "formula": formula, "override": bool(note and "price_overrides" in note),
                "quantity": quantity, "emeralds": total, "price": total, "wants": wants, "upgraded_wants": upgraded,
                "upgraded": sum(w["quantity"] for w in upgraded), "note": note, "clamped": total == MAX_PRICE and bool(note and "clamped" in note)}

    # -- review -----------------------------------------------------------------------
    def collect_review(self):
        rules, data, review = self.rules, self.data, self.review
        for item, rec in sorted(self.items.items()):
            if rec["price"] and rec["price"]["clamped"]:
                review["review"].append(f"`{item}`: price clamped to {MAX_PRICE} emeralds ({rec['price']['note']})")
            if rec["final"] == "review":
                review["review"].append(f"`{item}`: " + "; ".join(r for r in rec["reasons"] if r.startswith(("decision", "review"))))
            if rec["final"] == "include" and rec["unknown"]:
                review["unknown"].append(f"`{item}` yield uses unevaluated loot conditions (assumed true): " + ", ".join(rec["unknown"]))
            if rec["final"] == "include" and rec["yield"]["basis"] and rec["yield"]["basis"].startswith("equipment-only"):
                review["missing"].append(f"`{item}`: {rec['yield']['basis']}")
        star = self.items.get("minecraft:nether_star")
        if star and star["final"] == "include":
            dearer = [i for i, r in sorted(self.items.items()) if r["final"] == "include" and i != star["item"]
                      and r["price"]["price"] >= star["price"]["price"]]
            if dearer:
                review["review"].append("`minecraft:nether_star` must stay the most expensive item, but these cost as much or more: "
                                        + ", ".join(f"`{i}`" for i in dearer))
        for name, section in (("sources", rules.sources), ("special", rules.special), ("yield_overrides", rules.yield_overrides),
                              ("item_stage", rules.item_stage), ("decisions", rules.decisions),
                              ("price_overrides", rules.price_overrides)):
            for item in sorted(section):
                if item not in self.candidates:
                    review["noncandidate"].append(f"`{name}[{item}]`: not a candidate (no Peaceful-absent mob drops it and it is not in `special`)"
                                                  + (" - used for the craft check only" if name == "sources" else ""))
        mobs = set(data.entity_tables) | rules.absent | rules.breedable | rules.limited
        for key in sorted(rules.class_rules):
            item = normalise_id(key)
            if item not in self.candidates and _mob(key) not in mobs:
                review["noncandidate"].append(f"`acquisition_class[{key}]`: neither a candidate item nor a known mob")
        for name, section in (("sources", {i: e for i, es in rules.sources.items() for e in es}.items()),
                              ("special", rules.special.items()), ("yield_overrides", rules.yield_overrides.items()),
                              ("item_stage", rules.item_stage.items()), ("decisions", rules.decisions.items()),
                              ("acquisition_class", rules.class_rules.items()),
                              ("ingredient_class", rules.ingredient_class.items()),
                              ("price_overrides", rules.price_overrides.items())):
            for key, entry in section:
                if isinstance(entry, dict) and not (entry.get("reason") and entry.get("ref") or name == "decisions" and entry.get("reason")):
                    review["rules"].append(f"`{name}[{key}]`: missing `reason` or `ref`")
        assumed = defaultdict(list)
        for item, crafted in sorted(self.crafted.items()):
            for dep in crafted["deps"]:
                if dep.startswith(ASSUMED_TOKEN):
                    assumed[dep[1:]].append(item)
        for ingredient, makes in sorted(assumed.items()):
            review["assumed"].append(f"`{ingredient}` has no recipe and no `ingredient_class`; assumed EASY, so it excludes as crafted: "
                                     + ", ".join(f"`{m}`" for m in makes))
        for mob in sorted(self.unclassified_mobs):
            if any(s["mob"] == mob for item in self.candidates for s in self.sources[item]):
                review["mobs"].append(f"present mob `{mob}` is in neither `present_breedable` nor `present_limited` (treated as LIMITED)")
        if rules.game_version and rules.game_version != _short_version(data.version):
            review["rules"].append(f"rules `game_version` {rules.game_version} differs from the installed data {data.version}")
        if not rules.absent:
            review["rules"].append("`peaceful_mobs.absent` is empty: there are no candidates besides `special`")
        for line in data.problems:
            review["data"].append(line)
        for line in data.notes:
            review["data"].append(line)


def _short_version(pack):
    return pack.removeprefix("vanilla_")


# --------------------------------------------------------------------------------------
# output

def wants_of(total):
    """Total emeralds -> wants entries of at most one stack each: 128 = 64 + 64, 90 = 64 + 26."""
    out = []
    while total > 0:
        out.append({"item": "minecraft:emerald", "quantity": min(STACK, total)})
        total -= STACK
    return out


def discounted_wants(wants):
    """Upgrade Kit rule, mirrored from gen_trade_tables._discounted_wants: per wants entry max(1, round(q * 0.7))."""
    return [{**want, "quantity": max(1, round(want["quantity"] * 0.7))} for want in wants]


def _limited(deps):
    return any(d.startswith(LIMITED_TOKEN) for d in deps)


def num(value):
    return f"{value:.4g}"


def _by_kind(sources):
    groups = defaultdict(list)
    for src in sources:
        groups[(src["kind"], src["class"])].append(src)
    return groups


def source_lines(sources):
    lines = []
    for (kind, cls), group in sorted(_by_kind(sources).items()):
        parts = []
        for src in group[:SOURCE_LINE_TABLES]:
            label = src["mob"] + ": " + src["ref"] if src["mob"] else src["ref"]
            if src["expected"] is not None:
                label += f" ({num(src['expected'])})"
            if src.get("reason"):
                label += f" - {src['reason']}"
            if src.get("wiki"):
                label += f" [{src['wiki']}]"
            extra = sorted({n for n in src["notes"] if not n.startswith("legacy name")} | {"unevaluated: " + u for u in src["unknown"]})
            parts.append(label + (f" [{'; '.join(extra)}]" if extra else ""))
        more = f"; +{len(group) - SOURCE_LINE_TABLES} more" if len(group) > SOURCE_LINE_TABLES else ""
        origin = " (rules)" if group[0]["origin"] == "rules" else ""
        lines.append(f"- {cls} {kind}{origin}: " + "; ".join(parts) + more)
    return lines


def build_catalog(engine):
    rules = engine.rules
    order = {s: n for n, s in enumerate(rules.stages)}
    included = []
    for item, rec in engine.items.items():
        if rec["final"] != "include":
            continue
        price = rec["price"]
        special = rules.special.get(item)
        included.append({
            "item": item, "quantity": price["quantity"], "price": price["price"], "wants": price["wants"],
            "upgraded_price": price["upgraded"], "upgraded_wants": price["upgraded_wants"], "stage": rec["stage"], "class": rec["class"],
            "yield": round(price["yield"], 6), "attempt": rec["yield"]["attempt"],
            "replaces": special.get("mechanic") if special else "drop of " + ", ".join(sorted({s["mob"] for s in rec["origins"]})),
        })
    included.sort(key=lambda e: (order.get(e["stage"], 99), e["item"]))
    return {
        "game_version": engine.data.version,
        "rules_game_version": rules.game_version,
        "stages": rules.stages,
        "included": included,
        "review": sorted(i for i, r in engine.items.items() if r["final"] == "review"),
        "excluded": {i: ("decision" if "decision" in r else r["auto_kind"])
                     for i, r in sorted(engine.items.items()) if r["final"] == "exclude"},
    }


def build_report(engine):
    rules, items = engine.rules, engine.items
    finals = defaultdict(list)
    for item, rec in sorted(items.items()):
        finals[rec["final"]].append(item)
    out = []
    w = out.append
    w("# Peaceful resource machine: catalogue audit")
    w("")
    w("Generated by `tools/gen_peaceful_catalog.py` from `tools/peaceful_rules.json` and the installed game data")
    w(f"({engine.data.version}). Do not edit by hand; change the rules and rerun the tool.")
    w("")
    w("## Summary")
    w("")
    w(f"- Candidates evaluated: {len(items)}")
    for name in ("include", "review", "exclude"):
        w(f"- {name}: {len(finals[name])}")
    w(f"- Excluded as sold elsewhere: {sum(1 for r in items.values() if r['final'] == 'exclude' and r['sold_by'])}")
    w(f"- Excluded as crafted from accessible items: {sum(1 for r in items.values() if r['final'] == 'exclude' and r['state'] == 'crafted')}")
    w(f"- Tainted items (derived only from unreachable items): {len(engine.tainted)}")
    w(f"- Peaceful-absent mobs in the rules: {len(rules.absent)}; special mechanics: {len(rules.special)}; decisions: {len(rules.decisions)}")
    w("")
    w("Pricing inputs (proposals until the owner approves):")
    w("")
    w(f"- Base cost B per class: " + (", ".join(f"{k}={num(v)}" for k, v in sorted(rules.base.items())) or "none yet"))
    w(f"- Stage multiplier M: " + (", ".join(f"{k}={num(v)}" for k, v in sorted(rules.multiplier.items())) or "none yet"))
    w(f"- Stage order: " + (", ".join(rules.stages) or "none"))
    w(f"- Price anchors in the rules: {len(rules.anchors)}")
    w("")
    w("## Included items")
    w("")
    catalog = build_catalog(engine)
    if catalog["included"]:
        w("| Item | Quantity | Price | Upgraded | Stage | Class | Replaces |")
        w("|---|---|---|---|---|---|---|")
        for e in catalog["included"]:
            w(f"| `{e['item']}` | {e['quantity']} | {e['price']} | {e['upgraded_price']} | {e['stage']} | {e['class']} | {e['replaces']} |")
    else:
        w("None.")
    w("")
    w("## Needs owner review")
    w("")
    titles = (("review", "Decision `review` or missing data"), ("missing", "Missing yield"), ("unknown", "Unevaluated loot conditions"),
              ("assumed", "No-recipe ingredients assumed EASY (add `ingredient_class`)"),
              ("noncandidate", "Rule entries for items that are not candidates"), ("mobs", "Unclassified present mobs"),
              ("rules", "Rules file"), ("data", "Game data notes"))
    any_review = False
    for key, title in titles:
        lines = engine.review.get(key)
        if lines:
            any_review = True
            w(f"### {title} ({len(lines)})")
            w("")
            for line in lines:
                w(f"- {line}")
            w("")
    if not any_review:
        w("Nothing.")
        w("")
    w("## Tainted (derived only from unreachable items)")
    w("")
    w("Items without a known source whose every recipe needs an unreachable item (or another tainted item). They become")
    w("accessible when the machine sells the item they need (the craft check counts that).")
    w("")
    if engine.tainted:
        for item, needs in sorted(engine.tainted.items()):
            w(f"- `{item}`: needs " + ", ".join(f"`{n}`" for n in needs))
    else:
        w("None.")
    w("")
    w("## Evaluated items")
    w("")
    for name in ("include", "review", "exclude"):
        for item in finals[name]:
            rec = items[item]
            w(f"### {item}")
            w("")
            if display_id(item) != item:
                w(f"Name: {display_id(item)[len(item) + 2:-1]}")
                w("")
            w(f"- Decision: **{rec['final']}** (automatic: {rec['auto']})")
            w("- Reason chain:")
            for reason in rec["reasons"]:
                w(f"  - {reason}")
            w("- Sources:")
            for line in source_lines(rec["sources"]) or ["- none found in the data or the rules"]:
                w("  " + line)
            if rec["sold_by"]:
                w("  - SOLD by: " + ", ".join(rec["sold_by"]))
            if rec["auto_kind"] == "crafted":
                w("- Craft check: craftable" + (" (kept for sale by the owner's decision)" if rec.get("decision", {}).get("decision") == "include" else ", so not sold"))
            elif rec["limited_craft"]:
                w("- Craft check: craftable only with LIMITED ingredients, so it stays for sale (a LIMITED craft source is listed)")
            elif rec["craft_blockers"]:
                w("- Craft check: no recipe has all ingredients accessible")
                for recipe, missing in rec["craft_blockers"][:4]:
                    w(f"  - {recipe['kind']} {recipe['id']}: not accessible: " + (", ".join(missing) or "(none)"))
            elif rec["auto_kind"] == "include":
                w("- Craft check: no recipe exists")
            yld = rec["yield"]
            w(f"- Yield: {num(yld['value']) if yld['value'] is not None else 'unknown'} per attempt"
              f" ({yld['attempt'] or 'no attempt known'}; {yld['basis']})")
            for note in yld["notes"]:
                w(f"  - note: {note}")
            for unknown in yld["unknown"]:
                w(f"  - unevaluated (assumed true): {unknown}")
            w(f"- Class: {rec['class'] or 'missing'}" + (f" ({rec['class_reason']})" if rec["class_reason"] else ""))
            w(f"- Stage: {rec['stage'] or 'missing'}" + (f" ({rec['stage_reason']})" if rec["stage_reason"] else ""))
            price = rec["price"]
            if price:
                formula = price["formula"]
                formula_text = (f"ceil({num(price['B'])} x {num(price['M'])} / {num(price['yield'])}) = {num(formula['per_item'])} emeralds per item,"
                                f" quantity {formula['quantity']}, {formula['emeralds']} emeralds" if formula else "not derivable (missing yield, class or stage data)")
                w(f"- Formula: {formula_text}")
                w(f"- Price: {price['price']} emeralds for {price['quantity']} = wants {'+'.join(str(x['quantity']) for x in price['wants'])};"
                  f" upgraded {price['upgraded']} = {'+'.join(str(x['quantity']) for x in price['upgraded_wants'])}"
                  + (f" ({price['note']})" if price["note"] else ""))
            else:
                w("- Price: not derived" + (f" (missing {', '.join(rec['missing'])})" if rec["missing"] else ""))
            w("")
    return "\n".join(out).rstrip("\n") + "\n"


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def read_text(path):
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()
    except FileNotFoundError:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--rules", default=RULES_PATH, help="rules file (default tools/peaceful_rules.json)")
    parser.add_argument("--out", help="output folder for both files (default: tools/ and docs/; with --rules: <rules folder>/<rules name>_out)")
    parser.add_argument("--check", action="store_true", help="exit 1 if the written files would change; write nothing")
    args = parser.parse_args()
    catalog_path, report_path = CATALOG_PATH, REPORT_PATH
    out_dir = args.out or (None if os.path.abspath(args.rules) == os.path.abspath(RULES_PATH) else
                           os.path.splitext(os.path.abspath(args.rules))[0] + "_out")
    if out_dir:
        catalog_path, report_path = (os.path.join(out_dir, "peaceful_catalog.json"), os.path.join(out_dir, "peaceful-catalog.md"))
    rules = Rules(args.rules)
    engine = Engine(rules, load_game_data())
    catalog_text = json.dumps(build_catalog(engine), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    report_text = build_report(engine)
    finals = defaultdict(int)
    for rec in engine.items.values():
        finals[rec["final"]] += 1
    summary = (f"{len(engine.items)} candidates: {finals['include']} include, {finals['review']} review, "
               f"{finals['exclude']} exclude; {len(engine.tainted)} tainted; "
               f"{sum(len(v) for v in engine.review.values())} review lines")
    if args.check:
        stale = [p for p, t in ((catalog_path, catalog_text), (report_path, report_text)) if read_text(p) != t]
        if stale:
            print("peaceful catalogue would change: " + ", ".join(stale))
            return 1
        print("peaceful catalogue up to date. " + summary)
        return 0
    write_text(catalog_path, catalog_text)
    write_text(report_path, report_text)
    print(summary)
    print(f"wrote {os.path.relpath(catalog_path)} and {os.path.relpath(report_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
