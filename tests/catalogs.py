"""Trade generator: smoke test against the shipped tables, source resolution and book rules."""
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
from trade_sources import load_trade_source, fixture_filters, game_enchantments, plain_trades

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
    def write(relative, content):
        path = root / relative
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
        native, path, _ = load_trade_source('wandering_trader')
        self.assertEqual(path.parents[2].name, 'vanilla_1.26.50')
        expected = [variant for t in offers(native) for variant in trades.deterministic_variants(t)]
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
        self.assertEqual(pickaxe['gives'][0]['functions'][0]['function'], 'enchant_with_levels')  # owner exception

    def test_cartographer_destinations_and_dimension_filters(self):
        native = load_trade_source('cartographer').data
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

    def test_binary_source_uses_verified_readable_copy_or_flagged_fallback(self):
        trades_file = 'trading/economy_trades/fixture_trades.json'
        with sources() as (root, write):
            game, launchers, samples = root / 'game', root / 'launchers', root / 'samples'
            load = lambda: load_trade_source('fixture', game, launchers, samples)
            write(f'game/vanilla_1.9.0/{trades_file}', b'{"tiers": [], "item": "minecraft:old"}')
            write(f'game/vanilla_1.26.50/{trades_file}', b'{"tiers": [], "item": "minecraft:current"}')
            self.assertEqual(load().data['item'], 'minecraft:current')
            write(f'game/vanilla_1.26.60/{trades_file}', b'\x7fMCB\x01\x00\x05tiers\x11minecraft:newest')
            fallback = load()
            self.assertEqual(fallback.data['item'], 'minecraft:current')
            self.assertIn('FALLBACK', fallback.note)
            write(f'launchers/guid/data/behavior_packs/vanilla_1.26.60/{trades_file}', b'{"item": "minecraft:wrong"}')
            self.assertIn('FALLBACK', load().note)
            write(f'launchers/guid2/data/behavior_packs/vanilla_1.26.60/{trades_file}', b'{"item": "minecraft:newest"}')
            same = load()
            self.assertEqual(same.data['item'], 'minecraft:newest')
            self.assertIn('launcher install', same.note)
            # bedrock-samples (newest tag) wins over launcher installs; its normalised form is folded back.
            write(f'samples/v1.26.60.1/behavior_pack/{trades_file}', b'{"tiers": [], "item": "minecraft:wrong"}')
            self.assertIn('launcher install', load().note)
            write(f'samples/v1.26.60.10/behavior_pack/{trades_file}', b'{"tiers": [{"groups": [{"trades": [{ // note\n'
                  b'"wants": [{"choice": [{"quantity": {"min": 3, "max": 3}, "item": "minecraft:newest", "functions": []}]}]}]}]}]}')
            official = load()
            self.assertIn('bedrock-samples v1.26.60.10', official.note)
            self.assertEqual(official.data['tiers'][0]['groups'][0]['trades'][0]['wants'],
                             [{'item': 'minecraft:newest', 'quantity': 3}])
        options = {'tiers': [{'trades': [{'gives': [{'choice': [{'item': 'minecraft:a'}, {'item': 'minecraft:b'}]}]}]}]}
        self.assertEqual(plain_trades(options), options)  # real choices stay for _expand_choices

    def test_no_random_element_in_shipped_tables(self):
        shipped = list(MOD.glob('*_bp/trading/vm/*.json'))
        self.assertEqual(len(shipped), 30)
        enchanted = 0
        for path in shipped:
            self.assertEqual(trades.random_parts(read(path)), [], path.name)
            enchanted += json.dumps(read(path)).count('"enchant_with_levels"')
        self.assertEqual(trades.ALLOWED_RANDOM, {'enchant_with_levels'})  # the owner's only exception
        self.assertEqual(enchanted, 34)  # 17 vanilla gear offers x basic/upgraded

    def test_pick_n_groups_sell_all_m_and_random_functions_resolve(self):
        emerald = [{'item': 'minecraft:emerald'}]
        potion = {'item': 'minecraft:arrow', 'functions': [{'function': 'set_potion', 'id': 'healing'}]}
        tier = {'groups': [{'num_to_select': 1, 'trades': [
            {'wants': emerald, 'gives': [{'item': 'minecraft:leather_boots', 'functions': [{'function': 'random_dye'}]}]},
            {'wants': emerald, 'gives': [{'item': 'minecraft:bow', 'functions': [
                {'function': 'enchant_with_levels', 'levels': {'min': 5, 'max': 19}}]}]},
            {'wants': emerald, 'gives': [potion]}]}]}
        table = trades.build_table({'tiers': [tier] + [{}] * 4}, False)
        self.assertEqual([t['gives'][0] for t in offers(table)],
                         [{'item': 'minecraft:leather_boots'}, tier['groups'][0]['trades'][1]['gives'][0], potion])
        self.assertEqual(trades.random_parts(table), [])
        self.assertTrue(trades.random_parts({'tiers': [tier]}))
        ranged = {'trades': [{'wants': [{'item': 'minecraft:emerald', 'quantity': {'min': 1, 'max': 3}}], 'gives': emerald}]}
        with self.assertRaises(ValueError):
            trades.build_table({'tiers': [ranged] + [{}] * 4}, False)

    def test_shipped_tables_match_the_generator(self):
        tables, sources_used, notes = trades.build_all()
        self.assertEqual(len(tables), 30)
        self.assertFalse([note for note in notes if 'FALLBACK' in note or 'NEW' in note], notes)
        for rel, table in tables.items():
            self.assertEqual(read(MOD / rel), table, rel)
        self.assertIn('All tables are up to date.', trades.report(tables, sources_used, notes))

    def test_every_variant_once(self):
        tier = {'trades': [
            {'wants': [{'item': 'minecraft:emerald'}], 'gives': [{'item': 'minecraft:bed',
                'functions': [{'function': 'random_aux_value', 'values': {'min': 0, 'max': 2}}]}]},
            {'wants': [{'item': 'minecraft:emerald'}], 'gives': [{'item': 'minecraft:red_candle'}]},
            {'wants': [{'item': 'minecraft:emerald'}], 'gives': [{'item': 'minecraft:red_candle'}]}]}
        table = trades.build_table({'tiers': [tier] + [{}] * 4}, False)
        self.assertEqual([t['gives'][0]['item'] for t in offers(table)],
                         ['minecraft:bed:0', 'minecraft:bed:1', 'minecraft:bed:2', 'minecraft:red_candle'])
        self.assertNotIn('functions', offers(table)[0]['gives'][0])

    def test_books_follow_the_game_enchantment_list(self):
        game = game_enchantments()
        self.assertIn('lunge', game)
        enchants, notes = books.book_catalog()
        self.assertEqual(set(enchants), set(game))
        self.assertEqual(notes, [])
        sold = {f['enchants']['id'] for t in offers(read(MOD/'vending_villagers_bp/trading/vm/librarian.json'))
                for line in t['gives'] for f in line.get('functions', []) if f['function'] == 'specific_enchants'}
        self.assertEqual(sold, {i for i, spec in enchants.items() if not spec['curse']})

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
                self.assertEqual(books._patch(table, books.book_catalog()[0], cured), 40)
                self.assertEqual(table, original)

    def test_all_machine_bindings_and_internal_actor_descriptions(self):
        blocks = list(MOD.glob('*_bp/blocks/machine_*.json'))
        entities = list(MOD.glob('*_bp/entities/trader_*.json'))
        self.assertEqual(len(blocks), 15); self.assertEqual(len(entities), 15)
        for path in blocks:
            block = read(path)['minecraft:block']
            self.assertEqual(block['components']['vm:machine'], {})
            self.assertEqual(block['components']['minecraft:instrument_sound'], {'up': 'note.iron_xylophone'})
            policy = read(path.parents[1]/'block_materials.json')['blocks'][block['description']['identifier']]
            self.assertEqual(policy['property_checks']['minecraft:instrument_sound']['expected'], {'up': 'note.iron_xylophone'})
        for path in entities:
            description = read(path)['minecraft:entity']['description']
            self.assertFalse(description['is_spawnable']); self.assertTrue(description['is_summonable'])

if __name__ == '__main__':
    unittest.main()
