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

## Generators (`tools/`)

Run from anywhere; they locate the packs relative to this repo. All of them were
checked on 2026-09-29 to reproduce the shipped files byte for byte, so regenerating
is safe (they refuse to overwrite without `--force`).

- `gen_trade_tables.py` - the 13 profession tables (+ `_cured`, 30% cheaper) from the
  vanilla reference at `C:\mcmods\reference\vanilla\current` (1.26 ships those files as
  binary, so it falls back to the newest launcher install with plain JSON, or
  `--vanilla-root`); vanilla "choice" trades are split
  so the machine sells every variant. `gen_book_trades.py` adds the librarian's
  enchanted books from `enchantments.json`.
- `gen_machine_blocks.py`, `gen_machine_entities.py`, `gen_machine_recipes.py` - the
  13 villager machines (blocks carry the `vm:upgraded` state for the Upgrade Kit).
- `gen_machine_models.py` - their RP side: the empty trader model, client entities,
  `blocks.json`, atlases and lang. It rewrites those shared files with the villager
  entries only, so run `gen_extra_machines.py` after it.
- `gen_extra_machines.py` - the non-villager feature packs (wandering trader, shulker),
  built from the villager templates; a new feature is an entry in its MACHINES.
- Art: `make_machine_textures.py`, `vm_make_upgraded_textures.py`, `make_pack_icon.py`.

Pricing rule: upgraded table = the real trader's price; base table dearer (~vanilla / 0.7).
