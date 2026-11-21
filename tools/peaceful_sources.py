r"""Read layered vanilla game data for the Peaceful catalogue (gen_peaceful_catalog.py).

Reads (never writes): reference/vanilla/current/behavior_packs, packs `vanilla` and
`vanilla_<x.y.z>` (newest pack wins per relative path, like trade_sources.py; the
experimental_* and chemistry* packs are skipped), plus this mod's machine trade
tables (vending_*_bp/trading/vm/*.json).

Provides one object, `GameData` (built by `load_game_data()`):

  entity_tables   entity id -> {"loot": [table keys], "equipment": [table keys]}
                  (`minecraft:loot` / `minecraft:equipment` anywhere in the entity file,
                  component groups included)
  table_yield(k)  loot table key -> {item id: {"expected", "notes", "unknown"}}:
                  expected count per ONE roll set of the table (see "Loot maths")
  recipes         result item id -> [recipe dicts] (shaped, shapeless, furnace,
                  brewing_mix/container, smithing_transform), item tags resolved
                  where the data defines them
  sold            item id -> ["villager:cleric", "wandering_trader", "machine:farmer", ...]
  sources         item id -> [source dicts] (kind, ref, mob, expected, notes, unknown)
  notes           data problems and substitutions worth showing in the report

Loot maths (expected count of an item per roll set of a table):
  contribution = rolls * pool chance * weight / total weight * entry chance * avg count
  - rolls: number, {min,max} average, or `tiers` (initial_range + bonus_rolls * bonus_chance,
    an approximation); bonus_rolls without tiers is Luck and ignored
  - set_count: number or {min,max} average; `add: true` adds to the stack of 1
  - set_data / random_aux_value select the item variant (a range splits evenly);
    a variant keeps its data value in the id, e.g. minecraft:dye:4
  - random_chance and random_chance_with_looting use the BASE chance (looting ignored);
    random_difficulty_chance uses the Normal value (`normal`, else `default_chance`)
  - nested loot_table entries are evaluated recursively; `empty` entries only take weight
  - killed_by_player / killed_by_player_or_pets are ASSUMED true (they are the intended
    attempt) and noted; every other condition the engine cannot evaluate is ASSUMED true
    and listed in "unknown" (e.g. has_mark_variant, killed_by_entity, biome_has_tag).
    Pools gated by different killed_by_entity / has_mark_variant / has_variant values
    are mutually exclusive, so their contributions combine by max, not by sum.
  - unknown functions are listed in "unknown" as fn:<name>

Item ids are normalised to `minecraft:<name>` with a data value only where it is not
0 (`minecraft:dye:4`); legacy skull data values become the current ids
(`minecraft:skull:1` is `minecraft:wither_skeleton_skull`, as trade tables need); legacy names are mapped (netherStar, record_*, muttonRaw ...)
and `legacy_note()` explains each mapping.

Run directly for a quick dump:  python -I mods\vending\tools\peaceful_sources.py [loot-table-key]
"""

import glob
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I does not add the script folder
from trade_sources import VANILLA_PACKS, _read_json, game_version, load_trade_source, pack_version  # noqa: E402

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # this mod's repo root

# --------------------------------------------------------------------------------------
# item ids

ALIASES = {  # legacy or alternative name -> name this tool uses
    "netherStar": "nether_star",
    "appleEnchanted": "enchanted_golden_apple",
    "muttonRaw": "mutton",
    "muttonCooked": "cooked_mutton",
    "cod": "fish",  # minecraft:fish is raw cod in the data files
    "totem": "totem_of_undying",  # the loot tables still use the legacy name; the item id is the long one
}
SKULL_IDS = {  # legacy minecraft:skull data value -> current item id (trade tables need the current id)
    0: "minecraft:skeleton_skull", 1: "minecraft:wither_skeleton_skull", 2: "minecraft:zombie_head",
    3: "minecraft:player_head", 4: "minecraft:creeper_head", 5: "minecraft:dragon_head",
    6: "minecraft:piglin_head",
}
DATA_NAMES = {"minecraft:coal:1": "charcoal"}
ID_PATTERN = re.compile(r"^(?:(?P<ns>[a-z0-9_.]+):)?(?P<name>[A-Za-z0-9_.]+)(?::(?P<data>-?\d+))?$")


def normalise_id(raw, data=None):
    """`raw` is a string ("minecraft:dye:4", "netherStar") or {"item"/"name": ..., "data": n}; returns the id."""
    if isinstance(raw, dict):
        data = raw.get("data", raw.get("aux", data))
        raw = raw.get("item", raw.get("name"))
    raw = str(raw)
    if "potion_type:" in raw:  # brewing states, not items
        return "minecraft:potion_type:" + raw.split("potion_type:")[1].lower()
    if raw.startswith("#"):
        return raw
    match = ID_PATTERN.match(raw)
    if not match:
        return raw
    namespace, name, raw_data = match.group("ns") or "minecraft", match.group("name"), match.group("data")
    if data is None and raw_data is not None:
        data = int(raw_data)
    name = ALIASES.get(name, name)
    if namespace == "minecraft" and name.startswith("record_"):
        name = "music_disc_" + name[len("record_"):]
    if namespace == "minecraft" and name == "skull" and data in (None, -1, *SKULL_IDS):
        return SKULL_IDS[0 if data in (None, -1) else int(data)]
    ident = f"{namespace}:{name}"
    return ident if data in (None, 0, -1) else f"{ident}:{int(data)}"


def legacy_note(raw):
    """Why a raw id from the game data differs from its normalised form, or None."""
    text = raw if isinstance(raw, str) else str(raw.get("item", raw.get("name")))
    name = text.removeprefix("minecraft:").split(":")[0]
    if name in ALIASES:
        return f"legacy name {text} is {normalise_id(text)}"
    if name.startswith("record_"):
        return f"legacy name {text} is {normalise_id(text)}"
    return None


def display_id(item):
    """The id plus a plain name where the data value hides it (skull variants, charcoal)."""
    if item in DATA_NAMES:
        return f"{item} ({DATA_NAMES[item]})"
    return item


# --------------------------------------------------------------------------------------
# layered packs

def layered_packs(root=None):
    root = root or VANILLA_PACKS
    packs = [p for p in os.listdir(root) if p == "vanilla" or re.fullmatch(r"vanilla_[\d.]+", p)]
    return [os.path.join(root, p) for p in sorted(packs, key=pack_version)]


def layered_files(packs, sub):
    """{path relative to <pack>/<sub>, posix: absolute path}; the newest pack wins."""
    out = {}
    for pack in packs:
        base = os.path.join(pack, sub)
        for path in glob.glob(os.path.join(base, "**", "*.json"), recursive=True):
            out[os.path.relpath(path, base).replace(os.sep, "/")] = path
    return out


def read_json_file(path):
    with open(path, "rb") as handle:
        return _read_json(handle.read())


# --------------------------------------------------------------------------------------
# loot table maths

HARMLESS_FUNCTIONS = {  # change the stack but not the count or the identity of the item
    "looting_enchant", "enchant_randomly", "enchant_with_levels", "enchant_random_gear", "specific_enchants",
    "set_damage", "set_potion", "set_banner_details", "exploration_map", "set_armor_trim", "set_ominous_bottle_amplifier",
    "enchant_book_for_trading", "set_stew_effect", "explosion_decay",
}
ASSUMED_CONDITIONS = {"killed_by_player", "killed_by_player_or_pets"}
EXCLUSIVE = {"killed_by_entity": "entity_type", "has_mark_variant": "value", "has_variant": "value"}


def _avg(value, default=1.0):
    if isinstance(value, dict):
        return (float(value.get("min", 0)) + float(value.get("max", 0))) / 2
    return default if value is None else float(value)


def _short(name):
    return name.removeprefix("minecraft:")


def condition_effect(cond):
    """(chance factor, note or None, unknown description or None, exclusive group or None)."""
    name = _short(str(cond.get("condition", "?")))
    if name in ("random_chance", "random_chance_with_looting"):
        return float(cond.get("chance", 1.0)), None, None, None
    if name == "random_difficulty_chance":
        return float(cond.get("normal", cond.get("default_chance", 1.0))), None, None, None
    if name in ASSUMED_CONDITIONS:
        return 1.0, f"assumes {name}", None, None
    args = ",".join(f"{k}={json.dumps(v, sort_keys=True)}" for k, v in sorted(cond.items()) if k != "condition")
    text = f"{name}({args})".replace('"', "")
    group = None
    if name in EXCLUSIVE:
        group = (name, str(cond.get(EXCLUSIVE[name])))
    return 1.0, None, text, group


def _conditions(conds):
    factor, notes, unknown, group = 1.0, set(), set(), None
    for cond in conds or []:
        f, note, unk, grp = condition_effect(cond)
        factor *= f
        if note:
            notes.add(note)
        if unk:
            unknown.add(unk)
        group = group or grp
    return factor, notes, unknown, group


class Accumulator:
    """Per-item expected counts of one table; exclusive pool groups combine by max."""

    def __init__(self):
        self.items = {}

    def add(self, item, amount, notes, unknown, group):
        rec = self.items.setdefault(item, {"base": 0.0, "excl": defaultdict(lambda: defaultdict(float)),
                                           "notes": set(), "unknown": set()})
        if group:
            rec["excl"][group[0]][group[1]] += amount
        else:
            rec["base"] += amount
        rec["notes"] |= notes
        rec["unknown"] |= unknown

    def result(self):
        out = {}
        for item, rec in self.items.items():
            total = rec["base"] + sum(max(values.values()) for values in rec["excl"].values())
            out[item] = {"expected": total, "notes": sorted(rec["notes"]), "unknown": sorted(rec["unknown"])}
        return out


def _variants(functions):
    """-> (data values or [None], notes, unknown, average count or None, add flag)."""
    data, notes, unknown, count, add = [None], set(), set(), None, False
    for fn in functions or []:
        name = _short(str(fn.get("function", "?")))
        fn_factor, fn_note, fn_unknown, _ = _conditions(fn.get("conditions"))
        if fn_unknown:
            unknown |= {f"{name}:{text}" for text in fn_unknown}
        if name == "set_count":
            count, add = _avg(fn.get("count")), bool(fn.get("add"))
        elif name in ("set_data", "random_aux_value"):
            value = fn.get("data", fn.get("values"))
            if isinstance(value, dict):
                low, high = int(value.get("min", 0)), int(value.get("max", 0))
                data = list(range(low, min(high, low + 63) + 1))
                notes.add(f"{name} data {low}..{high} split evenly")
            else:
                data = [int(value)]
        elif name == "set_data_from_color_index":
            notes.add("colour data from the mob's variant")
        elif name == "furnace_smelt":
            notes.add("smelted when the mob is on fire")
        elif name in HARMLESS_FUNCTIONS:
            pass
        else:
            unknown.add(f"fn:{name}")
        if name == "set_potion":
            notes.add(f"potion {fn.get('id')}")
    return data, notes, unknown, count, add


class LootTables:
    """Layered loot tables and their expected-value evaluation."""

    def __init__(self, files, problems):
        self.files = files  # key "entities/creeper.json" -> path
        self.problems = problems
        self.cache = {}

    @staticmethod
    def key(name):
        key = name.replace("\\", "/").removeprefix("loot_tables/")
        return key if key.endswith(".json") else key + ".json"

    def load(self, key):
        path = self.files.get(key)
        if path is None:
            return None
        try:
            return read_json_file(path)
        except (ValueError, OSError) as error:
            self.problems.append(f"loot table {key}: unreadable ({error})")
            return None

    def evaluate(self, key, _stack=()):
        """{item id: {"expected", "notes", "unknown"}} for one roll set of the table."""
        key = self.key(key)
        if key in self.cache:
            return self.cache[key]
        data = self.load(key)
        if data is None:
            self.problems.append(f"loot table {key}: not found")
            self.cache[key] = {}
            return {}
        if key in _stack:
            self.problems.append(f"loot table {key}: nested loop")
            return {}
        acc = Accumulator()
        for pool in data.get("pools", []):
            self._pool(pool, acc, _stack + (key,))
        self.cache[key] = acc.result()
        return self.cache[key]

    def _pool(self, pool, acc, stack):
        factor, notes, unknown, group = _conditions(pool.get("conditions"))
        tiers = pool.get("tiers")
        if tiers:
            rolls = float(tiers.get("initial_range", 1)) + float(tiers.get("bonus_rolls", 0)) * float(tiers.get("bonus_chance", 0))
            notes.add("tiers rolls approximated as initial_range + bonus_rolls * bonus_chance")
        else:
            rolls = _avg(pool.get("rolls"), 1.0)
        entries = pool.get("entries", [])
        total = sum(float(e.get("weight", 1)) for e in entries)
        if not total or not factor or not rolls:
            return
        for entry in entries:
            weight = float(entry.get("weight", 1)) / total
            e_factor, e_notes, e_unknown, e_group = _conditions(entry.get("conditions"))
            share = rolls * factor * weight * e_factor
            all_notes, all_unknown, all_group = notes | e_notes, unknown | e_unknown, group or e_group
            kind = entry.get("type")
            if kind == "item":
                data, f_notes, f_unknown, count, add = _variants(entry.get("functions"))
                amount = (1.0 + count if add and count is not None else (count if count is not None else 1.0))
                name = entry["name"]
                note = legacy_note(name)
                for value in data:
                    acc.add(normalise_id(name, value), share * amount / len(data),
                            all_notes | f_notes | ({note} if note else set()), all_unknown | f_unknown, all_group)
            elif kind == "loot_table":
                for item, rec in self.evaluate(entry["name"], stack).items():
                    acc.add(item, share * rec["expected"], all_notes | set(rec["notes"]),
                            all_unknown | set(rec["unknown"]), all_group)
            # `empty` entries only take weight


# --------------------------------------------------------------------------------------
# entities

def _find_components(value, name, out):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == name and isinstance(item, dict):
                out.append(item)
            else:
                _find_components(item, name, out)
    elif isinstance(value, list):
        for item in value:
            _find_components(item, name, out)
    return out


def read_entities(files, problems):
    """entity id -> {"loot": [...], "equipment": [...], "drop_chance": [...]}"""
    out = {}
    for rel, path in sorted(files.items()):
        try:
            data = read_json_file(path)
        except (ValueError, OSError) as error:
            problems.append(f"entity {rel}: unreadable ({error})")
            continue
        entity = data.get("minecraft:entity") or {}
        ident = entity.get("description", {}).get("identifier")
        if not ident:
            continue
        loot = sorted({LootTables.key(c["table"]) for c in _find_components(entity, "minecraft:loot", []) if "table" in c})
        equip_parts = _find_components(entity, "minecraft:equipment", [])
        equip = sorted({LootTables.key(c["table"]) for c in equip_parts if "table" in c})
        if loot or equip:
            out[ident.removeprefix("minecraft:")] = {"loot": loot, "equipment": equip}
    return out


# --------------------------------------------------------------------------------------
# recipes

def read_tags(files):
    """item tag -> sorted item ids, from `minecraft:tags` item components (blocks are not in the data)."""
    tags = defaultdict(set)
    for path in files.values():
        try:
            data = read_json_file(path)
        except (ValueError, OSError):
            continue
        item = data.get("minecraft:item") or {}
        ident = item.get("description", {}).get("identifier")
        for comp in _find_components(item, "minecraft:tags", []):
            for tag in comp.get("tags", []) if isinstance(comp.get("tags"), list) else []:
                if ident:
                    tags[tag].add(normalise_id(ident))
    return {tag: sorted(items) for tag, items in tags.items()}


def _ingredient(value, tags):
    """One ingredient -> tuple of alternative ids ("#tag" when the data does not define the tag)."""
    if isinstance(value, list):
        return tuple(sorted({alt for v in value for alt in _ingredient(v, tags)}))
    if isinstance(value, dict) and "tag" in value:
        tag = value["tag"]
        return tuple(tags[tag]) if tag in tags else ("#" + tag,)
    if isinstance(value, dict) and "item" not in value:
        return ()
    return (normalise_id(value),)


def read_recipes(files, tags, problems):
    """result item id -> [{"kind", "id", "station", "ingredients": [alt tuples], "count"}]"""
    out = defaultdict(list)
    for rel, path in sorted(files.items()):
        try:
            data = read_json_file(path)
        except (ValueError, OSError) as error:
            problems.append(f"recipe {rel}: unreadable ({error})")
            continue
        for rtype, body in data.items():
            if not rtype.startswith("minecraft:recipe_") or not isinstance(body, dict):
                continue
            kind = rtype.removeprefix("minecraft:recipe_")
            station = body.get("tags", [])
            if "deprecated" in station:
                continue
            ident = body.get("description", {}).get("identifier", rel)
            ingredients, results = [], []
            if kind == "shaped":
                used = sorted({c for row in body.get("pattern", []) for c in row if c != " "})
                ingredients = [_ingredient(body["key"][c], tags) for c in used if c in body.get("key", {})]
            elif kind == "shapeless":
                ingredients = [_ingredient(v, tags) for v in body.get("ingredients", [])]
            elif kind == "furnace":
                ingredients = [_ingredient(body["input"], tags)]
            elif kind in ("brewing_mix", "brewing_container"):
                ingredients = [_ingredient(body["input"], tags), _ingredient(body["reagent"], tags)]
            elif kind == "smithing_transform":
                ingredients = [_ingredient(body[k], tags) for k in ("template", "base", "addition")]
            else:
                continue  # smithing_trim has no result item
            result = body.get("result", body.get("output"))
            for res in result if isinstance(result, list) else [result]:
                if res is None:
                    continue
                count = res.get("count", 1) if isinstance(res, dict) else 1
                results.append((normalise_id(res), count))
            for item, count in results:
                out[item].append({"kind": kind, "id": ident, "station": sorted(station), "ingredients": ingredients,
                                  "count": count})
    return dict(out)


# --------------------------------------------------------------------------------------
# trades

def _gives_items(value, out):
    if isinstance(value, dict):
        if "item" in value:
            out.add(normalise_id(value))
        for item in value.values():
            if isinstance(item, (dict, list)):
                _gives_items(item, out)
    elif isinstance(value, list):
        for item in value:
            _gives_items(item, out)
    return out


def _trade_gives(data):
    out = set()
    for tier in data.get("tiers", []):
        trades = [t for g in tier.get("groups") or [] for t in g.get("trades") or []] + (tier.get("trades") or [])
        for trade in trades:
            _gives_items(trade.get("gives", []), out)
    return out


def read_sold(root, notes):
    """item id -> sellers: vanilla villager professions, the wandering trader, this mod's machines."""
    sold = defaultdict(set)
    names = set()
    for pack in layered_packs(root):
        names |= {os.path.basename(p).removesuffix("_trades.json")
                  for p in glob.glob(os.path.join(pack, "trading", "economy_trades", "*_trades.json"))}
    for name in sorted(names):  # the `_cured` machine tables below repeat the same goods
        source = load_trade_source(name, root)
        if source.note:
            notes.append(f"trades {name}: {source.note}")
        label = "wandering_trader" if name == "wandering_trader" else f"villager:{name}"
        for item in _trade_gives(source.data):
            sold[item].add(label)
    for path in sorted(glob.glob(os.path.join(MOD, "vending_*_bp", "trading", "vm", "*.json"))):
        if path.endswith("_cured.json"):
            continue  # same goods as the basic table at another price
        if os.sep + "vending_loot_bp" + os.sep in path:
            continue  # the Loot Machines sell this tool's own catalogue; counting them would exclude every item
        pack = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
        for item in _trade_gives(read_json_file(path)):
            sold[item].add(f"machine:{pack.removeprefix('vending_').removesuffix('_bp')}/{os.path.basename(path)[:-5]}")
    return {item: sorted(v) for item, v in sold.items()}


# --------------------------------------------------------------------------------------
# sources

SPECIAL_ENTITY_TABLES = [  # (regex on the table key, kind)
    (r"entities/cat_gift\.json", "gift"),
    (r"entities/piglin_barter\.json", "barter"),
    (r"entities/.*_brushable_block\.json", "archaeology"),
    (r"entities/armadillo_brush\.json", "gameplay"),
]
DEFAULT_CLASS = {  # class of a data-derived source of this kind; mobs are classed by the engine from the rules
    "chest": "LIMITED", "vault": "LIMITED", "fishing": "LIMITED", "gift": "LIMITED", "archaeology": "LIMITED",
    "barter": "LIMITED", "pot": "LIMITED", "dispenser": "LIMITED", "gameplay": "LIMITED",
    "trial_spawner": "UNAVAILABLE", "block": "EASY",
}


def container_kind(key):
    """Kind of a loot table that is not a mob's own table, or None when it is only ever nested."""
    for pattern, kind in SPECIAL_ENTITY_TABLES:
        if re.fullmatch(pattern, key):
            return kind
    if key.startswith("chests/trial_chambers/reward"):
        return "vault"
    if key.startswith(("chests/", "barrels/")):
        return "chest"
    if key in ("gameplay/fishing.json", "gameplay/jungle_fishing.json"):
        return "fishing"
    if key.startswith("gameplay/entities/"):
        return "gameplay"
    if key.startswith("pots/"):
        return "pot"
    if key.startswith("dispensers/"):
        return "dispenser"
    if key.startswith("spawners/"):
        return "trial_spawner"
    if key.startswith("blocks/"):
        return "block"
    return None


class GameData:
    def __init__(self, root=None):
        root = root or VANILLA_PACKS
        self.notes, self.problems = [], []
        packs = layered_packs(root)
        self.version = game_version(root)
        self.loot = LootTables(layered_files(packs, "loot_tables"), self.problems)
        self.entity_tables = read_entities(layered_files(packs, "entities"), self.problems)
        self.tags = read_tags(layered_files(packs, "items"))
        self.recipes = read_recipes(layered_files(packs, "recipes"), self.tags, self.problems)
        self.sold = read_sold(root, self.notes)
        self.sources = defaultdict(list)
        self._build_sources()

    def table_yield(self, key):
        return self.loot.evaluate(key)

    def _add(self, key, kind, mob=None, detail=None):
        for item, rec in self.loot.evaluate(key).items():
            self.sources[item].append({"kind": kind, "ref": key, "mob": mob, "expected": rec["expected"],
                                       "notes": list(rec["notes"]), "unknown": list(rec["unknown"]),
                                       **({"detail": detail} if detail else {})})

    def _build_sources(self):
        for mob, tables in sorted(self.entity_tables.items()):
            for key in tables["loot"]:
                self._add(key, "mob_loot", mob)
            for key in tables["equipment"]:
                self._add(key, "mob_equipment", mob,
                          "equipped items; the drop chance is not modelled (equipment tables hold what spawns, not what drops)")
        for key in sorted(self.loot.files):
            kind = container_kind(key)
            if kind:
                self._add(key, kind)
        for item in self.sources:
            self.sources[item].sort(key=lambda s: (s["kind"], s["ref"], s["mob"] or ""))
        self.sources = dict(self.sources)
        if not any(k.startswith("gameplay/") and "hero" in k for k in self.loot.files):
            self.notes.append("no hero-of-the-village gift tables exist in the game data (gifts are engine-defined)")


def load_game_data(root=None):
    return GameData(root)


if __name__ == "__main__":
    data = load_game_data()
    print(f"game data {data.version}: {len(data.entity_tables)} mobs with tables, {len(data.loot.files)} loot tables, "
          f"{len(data.recipes)} recipe results, {len(data.sold)} sold items, {len(data.sources)} items with sources")
    for line in data.notes + data.problems:
        print("note:", line)
    for key in sys.argv[1:]:
        for item, rec in sorted(data.table_yield(key).items()):
            print(f"  {display_id(item)}: {rec['expected']:.4f} {rec['notes']} {rec['unknown']}")
