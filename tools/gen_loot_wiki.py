"""Generate the player-wiki records of the four Loot Machines.

Owns, inside mods/vending/wiki/: the `vm:machine_loot_*` entries of features.json and media.json
(other entries are kept byte for byte), plus behavior/loot-machines.json and
player/loot-machines.json. Loot Machines have no limitations: no storage and blocking water are
intended machine behaviour, not limitations (owner, 2026-11-22; docs/wiki.md). The per-item "why is this sold" sentences come from
tools/peaceful_catalog.json (`replaces`, `class`, `stage`) and tools/peaceful_rules.json
(`peaceful_mobs.absent`, `decisions`), never from hand-typed per-item prose.

Evidence pins are sha256 of the shipped files. A pack or catalogue edit therefore makes `--check` fail
and the export stop: re-read the affected claims, then rerun this script (it is the re-review step,
do not run it blindly).

    python -B tools/gen_loot_wiki.py          # write
    python -B tools/gen_loot_wiki.py --check  # fail when the records are stale
"""
import hashlib
import json
import re
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
WIKI = MOD / 'wiki'

STAGES = [  # (catalogue stage, machine suffix, player name)
    ('overworld', 'overworld', 'Overworld Loot Machine'),
    ('nether', 'nether', 'Nether Loot Machine'),
    ('trial', 'trial', 'Trial Loot Machine'),
    ('end_boss', 'end', 'End Loot Machine'),
]

ITEM_NAMES = {
    'minecraft:creeper_head': 'Creeper Head', 'minecraft:skeleton_skull': 'Skeleton Skull',
    'minecraft:zombie_head': 'Zombie Head', 'minecraft:piglin_head': 'Piglin Head',
    'minecraft:wither_skeleton_skull': 'Wither Skeleton Skull',
    'minecraft:tide_armor_trim_smithing_template': 'Tide Armor Trim Smithing Template',
    'minecraft:music_disc_lava_chicken': 'Music Disc (Lava Chicken)',
}
MOB_PLURALS = {
    'blaze': 'blazes', 'bogged': 'bogged', 'breeze': 'breezes', 'camel_husk': 'camel husks',
    'cave_spider': 'cave spiders', 'creeper': 'creepers', 'drowned': 'drowned',
    'elder_guardian': 'elder guardians', 'evocation_illager': 'evokers', 'ghast': 'ghasts',
    'guardian': 'guardians', 'husk': 'husks', 'parched': 'parched', 'phantom': 'phantoms',
    'pillager': 'pillagers', 'skeleton': 'skeletons', 'skeleton_horse': 'skeleton horses',
    'spider': 'spiders', 'stray': 'strays', 'vindicator': 'vindicators', 'witch': 'witches',
    'wither': 'the Wither', 'wither_skeleton': 'wither skeletons', 'zoglin': 'zoglins',
    'zombie': 'zombies', 'zombie_horse': 'zombie horses', 'zombie_pigman': 'zombified piglins',
    'zombie_villager': 'zombie villagers',
}
MOB_ALIAS = {'zombie_villager_v2': 'zombie_villager'}
HEAD_MOB = {'creeper_head': 'creeper', 'skeleton_skull': 'skeleton', 'zombie_head': 'zombie', 'piglin_head': 'piglin'}

def sha(path):
    return hashlib.sha256((MOD / path).read_bytes()).hexdigest()


def pin(*paths):
    return [{'path': p, 'sha256': sha(p)} for p in sorted(paths)]


def item_name(item):
    if item in ITEM_NAMES:
        return ITEM_NAMES[item]
    short = item.split(':', 1)[1]
    if short.startswith('music_disc_'):
        return 'Music Disc (' + short[len('music_disc_'):].replace('_', ' ').title() + ')'
    return short.replace('_', ' ').title().replace(' Of ', ' of ')


def join_words(words):
    if len(words) == 1:
        return words[0]
    return ', '.join(words[:-1]) + ' and ' + words[-1]


def mob_list(ids, absent):
    seen, words = set(), []
    for mob in ids:
        mob = MOB_ALIAS.get(mob, mob)
        if mob in seen:
            continue
        seen.add(mob)
        if mob not in absent:
            raise SystemExit('Mob is not absent on Peaceful, reason would be false: ' + mob)
        words.append(MOB_PLURALS[mob])
    return words


def sentence(entry, absent, decisions):
    """One player sentence for a catalogue entry, from its `replaces` text."""
    item, text = entry['item'], entry['replaces']
    short = item.split(':')[1]
    match = re.fullmatch(r'drop of (.+)', text)
    if short.startswith('music_disc_') and short != 'music_disc_lava_chicken' and short != 'music_disc_tears':
        raise AssertionError('creeper discs are grouped by the caller')
    if short == 'music_disc_lava_chicken':
        return ('Normally dropped by a baby zombie or husk riding a chicken when a player kills it; '
                'zombies and husks do not appear on Peaceful.')
    if short == 'music_disc_tears':
        return ('Normally dropped by a ghast killed by its own fireball, which a player reflected; '
                'ghasts do not appear on Peaceful.')
    if short in HEAD_MOB:
        return ('Normally dropped by a ' + HEAD_MOB[short] + ' killed in a charged creeper explosion; '
                'creepers do not appear on Peaceful.')
    if short.endswith('_froglight'):
        frog = re.search(r'a (temperate|warm|cold) frog', text).group(1)
        return ('Normally made when a ' + frog + ' frog eats a tiny magma cube; magma cubes do not appear on Peaceful.')
    if short == 'resin_clump':
        return 'Normally harvested from the heart of a creaking, which a player hits at night; creakings do not appear on Peaceful.'
    if short == 'wither_rose':
        return ('Normally left behind where the Wither kills a mob or player; the Wither cannot be summoned on Peaceful, '
                'so this rose is decorative here.')
    if short == 'wither_skeleton_skull':
        return ('Normally dropped by wither skeletons; they do not appear on Peaceful. '
                'The skull is sold as a decorative item, since the Wither cannot be summoned there.')
    if short == 'nether_star':
        return 'Normally dropped by the Wither; it cannot be summoned on Peaceful.'
    if short == 'ominous_trial_key':
        return ('Normally ejected as a reward by a completed ominous trial spawner; trial spawners do not spawn mobs on Peaceful, '
                'so they are never completed.')
    if short == 'trial_key':
        return ('Normally ejected as a reward by a completed trial spawner; trial spawners do not spawn mobs on Peaceful, '
                'so they are never completed.')
    if short == 'ominous_bottle':
        return 'Normally dropped by pillagers; they do not appear on Peaceful. The bottle is sold as a decorative item.'
    if short == 'tide_armor_trim_smithing_template':
        return 'Normally dropped by elder guardians, which are monument guardians that do not appear on Peaceful.'
    if match:
        words = mob_list([m.strip() for m in match.group(1).split(',')], absent)
        text = 'Normally dropped by ' + join_words(words) + '; they do not appear on Peaceful.'
        if len(words) == 1 and words[0] == 'the Wither':
            text = 'Normally dropped by the Wither; it cannot be summoned on Peaceful.'
        return text
    raise SystemExit('No sentence rule for ' + item + ': ' + entry['replaces'])


def build():
    catalog = json.loads((MOD / 'tools/peaceful_catalog.json').read_text(encoding='utf-8'))
    rules = json.loads((MOD / 'tools/peaceful_rules.json').read_text(encoding='utf-8'))
    absent = set(rules['peaceful_mobs']['absent'])
    decisions = rules['decisions']
    for key in ('minecraft:wet_sponge', 'minecraft:string', 'minecraft:trial_key'):
        assert key in decisions, key  # the exclusion/exception sections below restate these decisions

    features, behavior, media, player = [], [], [], []
    for stage, suffix, name in STAGES:
        fid = 'vm:machine_loot_' + suffix
        pack = 'vending_loot_bp/'
        shipped = [pack + 'blocks/machine_loot_%s.json' % suffix, pack + 'entities/trader_loot_%s.json' % suffix]
        recipe = pack + 'recipes/machine_loot_%s.json' % suffix
        features.append({
            'id': fid, 'slug': 'machine_loot_' + suffix, 'name': name, 'kind': 'block',
            'aliases': [], 'nativeIds': ['vm:machine_loot_' + suffix, 'vm:trader_loot_' + suffix],
            'obtaining': [{'id': fid + '/obtain', 'kind': 'crafting',
                           'text': 'Craft using the recipe for this machine or material.', 'related': []}],
            'relations': [], 'evidence': pin(*shipped, recipe),
        })
        ev = pin(*shipped)
        behavior += [
            {'evidence': pin(*shipped, 'vending_bp/scripts/main.js'), 'featureId': fid, 'id': fid + '/place',
             'text': 'Place on a floor with a completely empty block above. Machines can stand directly side-by-side or diagonally. '
                     'The machine is two blocks tall. In Survival, mine the base to collect the machine; the upper half cannot be mined. '
                     'Breaking and replacing it resets any trading progress and removes any installed upgrade. '
                     'The recovered item places a base machine; train and upgrade it again after moving.'},
            {'evidence': ev, 'featureId': fid, 'id': fid + '/trade',
             'text': 'Stand to trade. Crouch and aim at the upper half to build against it; while flying in Creative, hold Sneak. '
                     'Offers stay in stock, and every offer is paid in emeralds. Anyone can craft and use it, in any difficulty.'},
            {'evidence': ev, 'featureId': fid, 'id': fid + '/upgrade',
             'text': 'Use an Upgrade Kit on the base to cut its prices by about 30% until the machine is broken. '
                     'Survival consumes the kit once; using a kit on an already upgraded machine costs nothing.'},
        ]
        if suffix == 'end':
            behavior.append({'evidence': ev, 'featureId': fid, 'id': fid + '/nether-star',
                             'text': 'The Nether Star costs two full stacks of emeralds, so put one stack in each payment slot of the trade screen.'})
        media.append({'id': fid + '/icon', 'featureId': fid,
                      'source': 'vending_rp/textures/blocks/vm_machine_head_loot_%s.png' % suffix,
                      'kind': 'texture', 'alt': name,
                      'render': {'adapter': 'vending-machine', 'blockId': fid}})

        rows = [e for e in catalog['included'] if e['stage'] == stage]
        sections, discs = [], []
        for entry in rows:
            short = entry['item'].split(':')[1]
            if entry['class'] == 'music_disc' and entry['replaces'] == 'drop of creeper':
                discs.append(item_name(entry['item']))
                continue
            text = sentence(entry, absent, decisions)
            if entry['item'] == 'minecraft:string':
                text += ' It is sold as a deliberate exception: string matters early, and its only early source on Peaceful is a cat gift.'
            sections.append({'title': item_name(entry['item']), 'text': text})
        if discs:
            inner = [d[len('Music Disc ('):-1] for d in discs]
            sections.append({'title': 'Music Discs (creeper)',
                             'text': 'The twelve discs a creeper drops when a skeleton-type mob kills it: ' + join_words(inner) +
                                     '. Creepers and skeletons do not appear on Peaceful.'})
        if suffix == 'overworld':
            sections.append({'title': 'Not sold: wet sponge',
                             'text': 'Wet sponge is left out. Its main source is the sponge rooms of ocean monuments, and elder guardians '
                                     'cannot be farmed even in normal play, so the machine would only duplicate that structure loot.'})
        if suffix == 'trial':
            sections.append({'title': 'Trial keys instead of spawner rewards',
                             'text': 'Trial spawners do not spawn mobs on Peaceful, so the machine sells their trial and ominous trial keys '
                                     'in place of the reward. The other rewards, such as food, potions and wind charges, are found elsewhere or can be crafted.'})
        count = len(rows)
        player.append({
            'featureId': fid,
            'details': {
                'summary': 'Sells mob loot for emeralds, for worlds where the mob that drops it never appears.',
                'sections': sections,
            },
            'evidence': pin(*shipped, 'tools/peaceful_catalog.json', 'tools/peaceful_rules.json'),
        })
        assert count == len([e for e in catalog['included'] if e['stage'] == stage])
    return features, behavior, media, player


def dumps(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + '\n'


def merge(path, new, key, prefix, section=None):
    """Replace this generator's entries of an existing list file; keep everything else."""
    raw = json.loads((WIKI / path).read_text(encoding='utf-8'))
    rows = raw[section] if section else raw
    rows = [r for r in rows if not str(r[key]).startswith(prefix)] + new
    if section:
        raw[section] = rows
    else:
        raw = rows
    return raw


def outputs():
    features, behavior, media, player = build()
    return {
        'features.json': dumps(merge('features.json', features, 'id', 'vm:machine_loot_', 'features')),
        'media.json': dumps(merge('media.json', media, 'id', 'vm:machine_loot_')),
        'behavior/loot-machines.json': dumps(behavior),
        'player/loot-machines.json': dumps(player),
    }


def main():
    out = outputs()
    stale = []
    for rel, text in out.items():
        path = WIKI / rel
        old = path.read_bytes().decode('utf-8') if path.exists() else None
        if old != text:
            stale.append(rel)
            if '--check' not in sys.argv:
                path.parent.mkdir(exist_ok=True)
                with open(path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(text)
    if '--check' in sys.argv:
        if stale:
            print('stale: ' + ', '.join(stale))
            sys.exit(1)
        print('loot wiki records are current')
    else:
        print('wrote: ' + (', '.join(stale) or 'nothing (already current)'))


if __name__ == '__main__':
    main()
