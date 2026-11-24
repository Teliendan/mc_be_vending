# Vending Machines: development

Villager-style vending machines: engine-levelled trade tables on invisible fixture entities.
Namespace `vm:`.

## Packs

One Core plus one data-only pack per feature, all sharing `vending_rp/`:

| Pack | Content |
|---|---|
| `vending_bp` | Core: `scripts/main.js` + Upgrade Kit. Every feature pack depends on it. |
| `vending_villagers_bp` | the 13 villager profession machines |
| `vending_wandering_bp` | wandering trader machine |
| `vending_shulker_bp` | shulker machine + `vm:shulker_core` |
| `vending_loot_bp` | the four Loot Machines (Overworld, Nether, Trial, End): mob loot a Peaceful world cannot produce |
| `vending_rp` | shared resources |

A new feature = a new small BP depending on Core + an entry in `tools/gen_extra_machines.py`.
Deploy with `.\mods deploy vending` from the workspace; build the add-on locally with
`.\mods package vending`.

Crouch placement against the upper block uses native Minecraft placement; a standing player aiming
at the same machine wins, because the selection box is shared. Implementation and test status:
[INTERACTIONS.md](INTERACTIONS.md).

## Generators (`tools/`)

Run from anywhere; generators locate packs relative to this repo.

`python tools/build.py` runs the six JSON generators in the one order that works
(`--art` adds the texture and pack icon generators); suite `generated` checks that this
reproduces the shipped files exactly. Run single generators only for a quick look:
the shared RP files are wrong until the whole order has run.

- `gen_trade_tables.py` - every trade table (13 villagers, wandering trader, shulker;
  basic + `_cured`/upgraded) from the installed game. Without `--write` it only prints
  what would change. See "How to update trades" in [VANILLA_PARITY.md](VANILLA_PARITY.md).
  It uses `trade_sources.py` (game data), `gen_book_trades.py` + `enchantments.json`
  (librarian books) and the wandering/shulker rules in `gen_extra_machines.py`.
- `gen_machine_blocks.py`, `gen_machine_entities.py`, `gen_machine_recipes.py` - the
  13 villager machines (blocks carry the `vm:upgraded` state for the Upgrade Kit).
- `gen_machine_models.py` - their RP side: the empty trader model, client entities,
  `blocks.json`, atlases and lang. It rewrites those shared files with the villager
  entries only; `build.py` runs `gen_extra_machines.py` after it.
- `gen_extra_machines.py` - the non-villager feature packs (wandering trader, shulker),
  built from the villager templates; a new feature is an entry in its MACHINES.
  `--blocks-only` refreshes block definitions only.
- `gen_peaceful_catalog.py` (+ `peaceful_sources.py`) - evaluates the Peaceful machines' catalogue from
  `peaceful_rules.json` and the game data; writes `peaceful_catalog.json` and `peaceful-catalog.md`
  (`--check` = stale test). `build.py` runs it before `gen_extra_machines.py`, which turns the catalogue
  into the Loot Machines' trade tables; suite `generated` runs `--check`. `gen_loot_wiki.py` writes their
  wiki records. See [peaceful-machine.md](peaceful-machine.md).
- Art: `make_machine_textures.py`, `vm_make_upgraded_textures.py`, `make_pack_icon.py`.
- PBR (Vibrant Visuals): `tools/pbr_spec.json` is the source of every `*.texture_set.json` and `*_mers.tga` in
  `vending_rp/textures/` (chassis like the vanilla vault, gold trim like gold block, glass like vanilla glass, display
  goods copy their vanilla item's MERS with `"E": 0`; owner 2026-11-24: heads never glow, only the emerald
  status lights on body/top and the Shulker Core). Rebuild with
  `python -I .claude/skills/bedrock-art/scripts/pbr_mers.py build mods/vending/tools/pbr_spec.json` from the workspace
  root; **rerun it after any colour-texture change** (a moved good or a new colour breaks the selectors), and
  `build ... --check` must report 0 differences. Do not edit the sets by hand.
- `machine_catalog.py` is the shared source for the 13 villager machines' displayed
  goods and recipe signature ingredients. Accepted art and item choices:
  [GRAPHICS_CONCEPT.md](GRAPHICS_CONCEPT.md).

## Prices

Villager machines charge vanilla prices; the Upgrade Kit is their "cure" and cuts every wanted quantity 30% (floor 1).
Wandering machines charge more than vanilla until upgraded. Shulker prices are the
mod's own (12/24 emeralds, 8/16 upgraded).

## Tests and design

Tests: `node tests/run.mjs` (also run by `.\mods verify vending`); select with `--suite upgrades`,
`--suite placement`, `--suite catalogs`, `--suite lifecycle` or `--suite build-mode`.
Design, decisions and open game checks: [VANILLA_PARITY.md](VANILLA_PARITY.md).

Localization: nine locales use a mod-scoped contextual catalog. Read
[LOCALIZATION.md](LOCALIZATION.md) before adding or changing player-facing text.
