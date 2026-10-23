"""Read vanilla trade and enchantment data from the installed game.

Trade sources: the game layers versioned packs (vanilla, vanilla_1.16, ...,
vanilla_1.26.50); the newest pack that ships a profession's file wins. Since 1.26 some
of those files are binary "MCB" (magic 0x7f 'MCB', version 1): an uncompressed,
schema-bound serialisation that stores only the root key name ("tiers") and then
positional values, so it is not a known container and cannot be decoded without
Mojang's schema. For such a file the resolver reads the SAME versioned slice as JSON
from an older launcher install (%APPDATA%/.minecraft_bedrock/versions/*/data) and
checks that its item IDs, in order, equal the IDs embedded in the binary file. If no
such copy exists it falls back to the newest older readable slice and says so.
Every substitution comes back as a note for the diff report.
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


def _read_json(raw):
    return json.loads(raw.decode('utf-8-sig'))


def load_trade_source(name, root=None, launchers=None):
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
