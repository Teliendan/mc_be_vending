# Vending Machines

Villager-style vending machines (engine-levelled trade tables on fixture entities).

Packs - one Core plus one data-only pack per feature, all sharing `vending_rp/`:

| Pack | Content |
|---|---|
| `vending_bp` | Core: `scripts/main.js` + Upgrade Kit. Every feature pack depends on it. |
| `vending_villagers_bp` | the 13 villager profession machines |
| `vending_wandering_bp` | wandering trader machine |
| `vending_shulker_bp` | shulker machine + `vm:shulker_core` |
| `vending_rp` | shared resources |

A new feature = a new small BP depending on Core + an entry in `tools/gen_extra_machines.py`.
Deploy with `mods deploy vending`.

Crouch and aim at the upper block to place blocks or attach torches using native
Minecraft placement. Stand up to trade. If a standing player aims at the same
machine, trade access takes priority because the selection box is shared.
See [interaction notes](docs/INTERACTIONS.md) for implementation and test status.

## Generators (`tools/`)

Run from anywhere; generators locate packs relative to this repo.

- `gen_trade_tables.py` - every trade table (13 villagers, wandering trader, shulker;
  basic + `_cured`/upgraded) from the installed game. Without `--write` it only prints
  what would change. See "How to update trades" in [docs/VANILLA_PARITY.md](docs/VANILLA_PARITY.md).
  It uses `trade_sources.py` (game data), `gen_book_trades.py` + `enchantments.json`
  (librarian books) and the wandering/shulker rules in `gen_extra_machines.py`.
- `gen_machine_blocks.py`, `gen_machine_entities.py`, `gen_machine_recipes.py` - the
  13 villager machines (blocks carry the `vm:upgraded` state for the Upgrade Kit).
- `gen_machine_models.py` - their RP side: the empty trader model, client entities,
  `blocks.json`, atlases and lang. It rewrites those shared files with the villager
  entries only, so run `gen_extra_machines.py` after it.
- `gen_extra_machines.py` - the non-villager feature packs (wandering trader, shulker),
  built from the villager templates; a new feature is an entry in its MACHINES.
  `--blocks-only` refreshes block definitions only.
- Art: `make_machine_textures.py`, `vm_make_upgraded_textures.py`, `make_pack_icon.py`.
- `machine_catalog.py` is the shared source for the 13 villager machines' displayed
  goods and recipe signature ingredients. Accepted art and item choices:
  [graphics notes](docs/GRAPHICS_CONCEPT.md).

Villager machines charge vanilla prices; the Upgrade Kit cuts every price 30%.
Wandering machines charge more than vanilla until upgraded. Shulker prices are the
mod's own (12/24 emeralds, 8/16 upgraded).

Tests: `node tests/run.mjs`; select with `--suite upgrades`, `--suite placement`,
`--suite catalogs`, `--suite lifecycle` or `--suite build-mode`.
Design, decisions and open game checks: [docs/VANILLA_PARITY.md](docs/VANILLA_PARITY.md).

## Localization

Nine locales use a mod-scoped contextual catalog. See [the localization notes](docs/LOCALIZATION.md) before adding or changing player-facing text.
