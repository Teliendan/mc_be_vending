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

Run from anywhere; generators locate packs relative to this repo. Generators
with a `--force` option require it to overwrite existing files. The extra-machine
generator updates its own outputs directly. Catalog sources are versioned and
checked; do not substitute an old install when a current source is binary.

- `gen_trade_tables.py` - the 13 profession tables (+ `_cured`, 30% cheaper) from the
  newest matching vanilla override under `C:\mcmods\reference\vanilla\current`.
  Select only changed professions with `--profession cartographer` (repeatable).
  An explicit readable `--vanilla-root` is supported; binary sources fail before
  any selected table is written. Vanilla "choice" trades are split
  so the machine sells every variant. `gen_book_trades.py` adds the librarian's
  enchanted books from `enchantments.json`.
- `gen_machine_blocks.py`, `gen_machine_entities.py`, `gen_machine_recipes.py` - the
  13 villager machines (blocks carry the `vm:upgraded` state for the Upgrade Kit).
- `gen_machine_models.py` - their RP side: the empty trader model, client entities,
  `blocks.json`, atlases and lang. It rewrites those shared files with the villager
  entries only, so run `gen_extra_machines.py` after it.
- `gen_extra_machines.py` - the non-villager feature packs (wandering trader, shulker),
  built from the villager templates; a new feature is an entry in its MACHINES.
  `--blocks-only` refreshes block definitions without rewriting trades or recipes.
- Art: `make_machine_textures.py`, `vm_make_upgraded_textures.py`, `make_pack_icon.py`.
- `machine_catalog.py` is the shared source for the 13 villager machines' displayed
  goods and recipe signature ingredients. Accepted art and item choices:
  [graphics notes](docs/GRAPHICS_CONCEPT.md).

Profession machines retain their source base prices and a30% kit discount.
Wandering machines use current vanilla prices/counts when upgraded, dearer buying
prices when basic, and reduced emerald payouts for basic buybacks (minimum1).
Input bucket/bottle quantities stay native. Shulker prices retain the custom
12/24 basic and8/16 upgraded balance. Native price multipliers remain.

Tests: `node tests/run.mjs`; named selections include `--suite upgrades`,
`--suite placement`, `--suite catalogs`, `--suite lifecycle` and `--suite build-mode`.
See [the completed source batch and pending game checks](docs/PARITY_INSPECTION.md).

## Localization

Nine locales use a mod-scoped contextual catalog. See [the localization notes](docs/LOCALIZATION.md) before adding or changing player-facing text.
