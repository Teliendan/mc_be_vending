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

Run from anywhere; they locate the packs relative to this repo.

- `gen_machine_recipes.py` reproduces the 13 recipes byte for byte (`--out DIR` to compare first).
- `gen_trade_tables.py`, `gen_book_trades.py` (+ `enchantments.json`), `gen_extra_machines.py`.
- `gen_machine_blocks.py`, `gen_machine_entities.py`, `gen_machine_models.py` were never
  re-checked against the real files: generate into a temp folder and diff before trusting them.
- Art: `make_machine_textures.py`, `vm_make_upgraded_textures.py`, `make_pack_icon.py`.

Pricing rule: upgraded table = the real trader's price; base table dearer (~vanilla / 0.7).
