"""Resolve current installed vanilla trade overrides, without an old-install fallback."""
import copy
import json
from pathlib import Path

VANILLA_PACKS = Path('C:/mcmods/reference/vanilla/current/behavior_packs')
BINARY_MAGIC = b'\x7fMCB'


def load_trade_source(name, root=None):
    root = Path(root) if root is not None else VANILLA_PACKS
    filename = name + '_trades.json'
    # An explicitly supplied economy_trades directory remains supported.
    if root.name == 'economy_trades':
        candidates = [root / filename]
    else:
        def version(path):
            pack = path.parents[2].name
            return tuple(map(int, pack.removeprefix('vanilla_').split('.'))) if pack.startswith('vanilla_') else (0,)
        candidates = sorted(root.glob('vanilla*/trading/economy_trades/' + filename), key=version)
    if not candidates:
        raise ValueError(f'No vanilla trade source for {name} under {root}')
    path = candidates[-1]
    raw = path.read_bytes()
    if raw.startswith(BINARY_MAGIC):
        raise ValueError(f'Current source {path} is binary; supply an explicit readable economy_trades directory. No older source was substituted.')
    return json.loads(raw.decode('utf-8-sig')), path


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
