"""Trade generation regressions against inspected native inputs."""
import copy
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import tempfile
import unittest

MOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MOD / 'tools'))
import gen_book_trades as books
import gen_extra_machines as extra
import gen_trade_tables as trades
from trade_sources import load_trade_source, fixture_filters

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def offers(table):
    return [offer for tier in table['tiers'] for offer in trades._tier_trades(tier)]

@contextmanager
def sources():
    scratch = MOD.parents[1] / 'temp/vending-inspection'
    scratch.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='source-fixture-', dir=scratch))
    files, directories = [], {root}
    def write(version, content):
        path = root / version / 'trading/economy_trades/fixture_trades.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        files.append(path)
        directories.update(parent for parent in path.parents if parent == root or root in parent.parents)
        path.write_bytes(content)
    try:
        yield root, write
    finally:
        for path in files:
            path.unlink()
        for path in sorted(directories, key=lambda p: len(p.parts), reverse=True):
            path.rmdir()  # Exact known empty directories only.

class Catalogs(unittest.TestCase):
    def test_current_wandering_catalog_and_buybacks(self):
        native, path = load_trade_source('wandering_trader')
        self.assertEqual(path.parents[2].name, 'vanilla_1.26.50')
        expected = [variant for t in offers(native) for variant in trades._expand_choices(t)]
        upgraded = offers(extra.wandering_table(True))
        self.assertEqual(len(upgraded), 100)
        self.assertEqual(len(upgraded), len(expected))
        for actual, source in zip(upgraded, expected):
            self.assertEqual(actual['wants'], source['wants'])
            self.assertEqual(actual['gives'], source['gives'])
            self.assertEqual(actual['trader_exp'], 0)
            self.assertEqual(actual['max_uses'], 9999999)
        self.assertEqual(sum(t['gives'][0]['item'] == 'minecraft:emerald' for t in upgraded), 6)
        for cured in [False, True]:
            name = 'wandering_trader_cured.json' if cured else 'wandering_trader.json'
            self.assertEqual(read(MOD/'vending_wandering_bp/trading/vm'/name), extra.wandering_table(cured))

    def test_buybacks_never_require_stacks_of_unstackable_inputs(self):
        for base, upgraded in zip(offers(extra.wandering_table(False)), offers(extra.wandering_table(True))):
            if upgraded['gives'][0]['item'] == 'minecraft:emerald':
                self.assertEqual(base['wants'], upgraded['wants'])
                self.assertGreaterEqual(base['gives'][0]['quantity'], 1)
                self.assertLessEqual(base['gives'][0]['quantity'], upgraded['gives'][0]['quantity'])
            else:
                self.assertGreaterEqual(base['wants'][0]['quantity'], upgraded['wants'][0]['quantity'])
                self.assertLessEqual(base['wants'][0]['quantity'], 64)

    def test_potions_and_enchanted_tool_functions_survive(self):
        table = offers(extra.wandering_table(True))
        potion = next(t for t in table if t['gives'][0]['item'] == 'minecraft:potion:8')
        self.assertEqual(potion['wants'][0]['quantity'], 5)
        pickaxe = next(t for t in table if t['gives'][0]['item'] == 'minecraft:iron_pickaxe')
        self.assertEqual(pickaxe['gives'][0]['functions'][0]['function'], 'enchant_with_levels')

    def test_cartographer_destinations_and_dimension_filters(self):
        native, _ = load_trade_source('cartographer')
        destinations = set()
        for cured in [False, True]:
            generated = trades.build_table(native, cured)
            name = 'cartographer_cured.json' if cured else 'cartographer.json'
            self.assertEqual(read(MOD/'vending_villagers_bp/trading/vm'/name), generated)
            for offer in offers(generated):
                for item in offer['gives']:
                    for function in item.get('functions', []):
                        if function['function'] == 'exploration_map':
                            destinations.add(function['destination'])
                            encoded = json.dumps(item.get('filters'))
                            self.assertIn('in_overworld', encoded)
                            self.assertNotIn('is_mark_variant', encoded)
        self.assertEqual(destinations, {'monument', 'mansion', 'trial_chambers', 'jungle_temple', 'swamp_hut',
            'village_taiga', 'village_desert', 'village_plains', 'village_snowy', 'village_savanna'})

    def test_source_selection_never_silently_falls_back_from_binary(self):
        with sources() as (root, write):
            write('vanilla_1.9.0', b'{"source": "old"}')
            write('vanilla_1.26.50', b'{"source": "current"}')
            self.assertEqual(load_trade_source('fixture', root)[0]['source'], 'current')
            write('vanilla_1.26.60', b'\x7fMCBbinary')
            with self.assertRaisesRegex(ValueError, 'No older source was substituted'):
                load_trade_source('fixture', root)

    def test_filter_pruning_preserves_other_restrictions_and_source(self):
        original = {'all_of': [{'test': 'in_overworld', 'value': True},
            {'any_of': [{'test': 'is_mark_variant', 'value': 1}, {'test': 'is_mark_variant', 'value': 2}]}]}
        snapshot = copy.deepcopy(original)
        self.assertEqual(fixture_filters(original), {'all_of': [{'test': 'in_overworld', 'value': True}]})
        self.assertEqual(original, snapshot)

    def test_book_patch_is_idempotent_and_preserves_other_offers(self):
        for cured in [False, True]:
            name = 'librarian_cured.json' if cured else 'librarian.json'
            table = read(MOD/'vending_villagers_bp/trading/vm'/name)
            original = copy.deepcopy(table)
            for _ in range(2):
                self.assertEqual(books._patch(table, books._load_enchants(), cured), 36)
                self.assertEqual(table, original)

    def test_all_machine_bindings_and_internal_actor_descriptions(self):
        blocks = list(MOD.glob('*_bp/blocks/machine_*.json'))
        entities = list(MOD.glob('*_bp/entities/trader_*.json'))
        self.assertEqual(len(blocks), 15); self.assertEqual(len(entities), 15)
        for path in blocks:
            block = read(path)['minecraft:block']
            self.assertEqual(block['components']['vm:machine'], {})
            self.assertEqual(block['components']['minecraft:instrument_sound'], {'down': 'note.iron_xylophone'})
            policy = read(path.parents[1]/'block_materials.json')['blocks'][block['description']['identifier']]
            self.assertEqual(policy['property_checks']['minecraft:instrument_sound']['expected'], {'down': 'note.iron_xylophone'})
        for path in entities:
            description = read(path)['minecraft:entity']['description']
            self.assertFalse(description['is_spawnable']); self.assertTrue(description['is_summonable'])

if __name__ == '__main__':
    unittest.main()
