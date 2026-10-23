"""Read vanilla trade and enchantment data from the installed game.

Trade sources: the game layers versioned packs (vanilla, vanilla_1.16, ...,
vanilla_1.26.50); the newest pack that ships a profession's file wins.

Binary "MCB" files: since 1.26 the game ships minified JSON, and every trade file
whose trades use no item `functions` is stored instead in a schema-bound binary form
(magic 0x7f 'MCB', version 1: the root key "tiers", then positional values; every
quantity as a min/max pair). It is a build-time packing choice, not a content
change or a naming problem: each MCB file holds exactly the trades of the old JSON.
For such a file the resolver reads, in order:
  1. Mojang/bedrock-samples (reference/bedrock-samples/<tag>, fetched by
     tools/fetch_bedrock_samples.py): the official JSON of the newest release, in a
     normalised form (single-option "choice" wrappers, {"min": n, "max": n}
     quantities, empty function lists) that is folded back to the plain form;
  2. the SAME versioned slice as JSON from an older launcher install
     (%APPDATA%/.minecraft_bedrock/versions/*/data);
  3. the newest older readable slice (flagged FALLBACK).
1 and 2 are used only when their item IDs, in order, equal the IDs embedded in the
binary file. Every substitution comes back as a note for the diff report.
"""
import copy
import json
import os
import re
from collections import namedtuple
from pathlib import Path

REFERENCE = Path('C:/mcmods/reference/vanilla/current')
VANILLA_PACKS = REFERENCE / 'behavior_packs'
LAUNCHER_VERSIONS = Path(os.environ.get('APPDATA', '')) / '.minecraft_bedrock' / 'versions'
SAMPLES = Path('C:/mcmods/reference/bedrock-samples')
SAMPLES_TRADES = Path('behavior_pack/trading/economy_trades')
BINARY_MAGIC = b'\x7fMCB'
ITEM_ID = re.compile(rb'minecraft:[a-z0-9_.:]+')

Source = namedtuple('Source', 'data path note')


def pack_version(pack):
    """vanilla_1.21.40 -> (1, 21, 40); the unversioned base pack sorts first."""
    return tuple(map(int, pack.removeprefix('vanilla_').split('.'))) if pack.startswith('vanilla_') else (0,)


def game_version(root=None):
    packs = [p.name for p in Path(root or VANILLA_PACKS).glob('vanilla_*') if re.fullmatch(r'vanilla_[\d.]+', p.name)]
    return max(packs, key=pack_version) if packs else 'unknown'


def json_item_ids(value, out=None):
    out = [] if out is None else out
    if isinstance(value, dict):
        for item in value.values():
            json_item_ids(item, out)
    elif isinstance(value, list):
        for item in value:
            json_item_ids(item, out)
    elif isinstance(value, str) and value.startswith('minecraft:'):
        out.append(value)
    return out


def binary_item_ids(raw):
    return [match.decode() for match in ITEM_ID.findall(raw)]


JSON_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', re.S)


def _strip_comments(text):
    """Drop // and /* */ comments outside strings (bedrock-samples JSON carries a few)."""
    return JSON_TOKEN.sub(lambda m: m.group(0) if m.group(0).startswith('"') else '', text)


def _read_json(raw):
    return json.loads(_strip_comments(raw.decode('utf-8-sig')))


def _plain_line(line, option=False):
    """bedrock-samples form -> plain form: unwrap one-option choices, fixed quantities as numbers."""
    if set(line) == {'choice'} and len(line['choice']) == 1:
        return _plain_line(line['choice'][0])
    if 'choice' in line:
        return {**line, 'choice': [_plain_line(option, option=True) for option in line['choice']]}
    # Samples drop a quantity of 1; vanilla files spell it out on plain lines, not on choice options.
    quantity = line.get('quantity', None if option else 1)
    if isinstance(quantity, dict) and quantity.get('min') == quantity.get('max'):
        quantity = quantity['min']
    plain = {'item': line['item']} if quantity is None else {'item': line['item'], 'quantity': quantity}
    plain.update((key, value) for key, value in line.items() if key not in plain and key != 'quantity' and value != [])
    return plain


def plain_trades(data):
    """Fold the normalised bedrock-samples serialisation back to the plain vanilla form."""
    data = copy.deepcopy(data)
    for tier in data.get('tiers', []):
        for trade in [t for g in tier.get('groups') or [] for t in g.get('trades') or []] + (tier.get('trades') or []):
            for key in ('wants', 'gives'):
                if key in trade:
                    trade[key] = [_plain_line(line) for line in trade[key]]
    return data


def samples_release(samples=None):
    """Newest bedrock-samples tag folder that holds trade files, or None."""
    samples = Path(samples) if samples is not None else SAMPLES
    tags = [p for p in samples.glob('v*') if (p / SAMPLES_TRADES).is_dir()]
    key = lambda p: tuple(int(x) for x in re.findall(r'\d+', p.name.split('-')[0]))
    return max(tags, key=key) if tags else None


def _samples_commit(release):
    source = release / 'SOURCE.txt'
    match = re.search(r'commit ([0-9a-f]{10})', source.read_text(encoding='utf-8')) if source.exists() else None
    return f' commit {match.group(1)}' if match else ''


def load_trade_source(name, root=None, launchers=None, samples=None):
    root = Path(root) if root is not None else VANILLA_PACKS
    launchers = Path(launchers) if launchers is not None else LAUNCHER_VERSIONS
    filename = name + '_trades.json'
    if root.name == 'economy_trades':  # an explicit readable directory
        path = root / filename
        return Source(_read_json(path.read_bytes()), path, None)
    candidates = sorted(root.glob('vanilla*/trading/economy_trades/' + filename),
                        key=lambda p: pack_version(p.parents[2].name))
    if not candidates:
        raise ValueError(f'No vanilla trade source for {name} under {root}')
    newest = candidates[-1]
    raw = newest.read_bytes()
    if not raw.startswith(BINARY_MAGIC):
        return Source(_read_json(raw), newest, None)

    pack = newest.parents[2].name
    ids = binary_item_ids(raw)
    release = samples_release(samples)
    if release is not None and (release / SAMPLES_TRADES / filename).exists():
        path = release / SAMPLES_TRADES / filename
        data = plain_trades(_read_json(path.read_bytes()))
        if json_item_ids(data) == ids:
            return Source(data, path, f'{pack} is binary (MCB) in the game; read as JSON from Mojang/bedrock-samples '
                          f'{release.name}{_samples_commit(release)}; all {len(ids)} item IDs match the binary file.')
    for copy_path in sorted(launchers.glob(f'*/data/behavior_packs/{pack}/trading/economy_trades/{filename}')):
        copy_raw = copy_path.read_bytes()
        if copy_raw.startswith(BINARY_MAGIC):
            continue
        data = _read_json(copy_raw)
        if json_item_ids(data) == ids:
            return Source(data, copy_path, f'{pack} is binary in the game; read the same slice as JSON from launcher '
                          f'install {copy_path.parents[5].name[:8]} (game {game_version(copy_path.parents[3])}); '
                          f'all {len(ids)} item IDs match the binary file.')
    for older in reversed(candidates[:-1]):
        older_raw = older.read_bytes()
        if not older_raw.startswith(BINARY_MAGIC):
            return Source(_read_json(older_raw), older, f'FALLBACK: {pack} is binary and no readable copy exists; used older '
                          f'{older.parents[2].name}. Trades added in {pack} are MISSING.')
    raise ValueError(f'{newest} is binary and no readable {filename} exists (game or launcher installs).')


def game_enchantments(root=None):
    """Enchantment IDs the game knows, from the vanilla-data enum the game ships in its editor script."""
    script = Path(root or VANILLA_PACKS) / 'editor' / 'scripts' / 'Main.js'
    ids = re.findall(r'MinecraftEnchantmentTypes\d*\["\w+"\] = "minecraft:(\w+)";', script.read_text(encoding='utf-8'))
    if not ids:
        raise ValueError(f'No enchantment list found in {script}')
    return sorted(set(ids))


def fixture_filters(value):
    """Remove villager biome-variant gates; preserve other native restrictions."""
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    if value.get('test') == 'is_mark_variant':
        return None
    result = {}
    for key, item in value.items():
        if key in ('all_of', 'any_of', 'none_of'):
            conditions = [condition for term in item if (condition := fixture_filters(term)) is not None]
            if conditions:
                result[key] = conditions
        else:
            result[key] = copy.deepcopy(item)
    return result or None


def fixture_items(items):
    result = copy.deepcopy(items)
    for item in result:
        if 'filters' in item:
            filters = fixture_filters(item['filters'])
            if filters is None:
                del item['filters']
            else:
                item['filters'] = filters
    return result
