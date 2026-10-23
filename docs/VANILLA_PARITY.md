# Vending: design, vanilla parity and open checks

Target Bedrock 1.26.52 / Script API 2.8.0. Final design only; history is in git
(review and implementation: workspace commits `288b0f7`, `5029b4e`; mod `a5bd9bb`).
Crouch placement against the head: [INTERACTIONS.md](INTERACTIONS.md).

## Machine block

One custom block in two positions: `vm:half` 0 (base: selectable, mineable, owns
the loot) and `vm:half` 1 (head: holds the trader, selection box only while
crouch-building). Counterparts: Block of Iron for material, door for paired
ownership, villager for trading. All 15 machines share `gen_machine_blocks.py`;
`gen_extra_machines.py` clones the farmer machine for wandering trader and shulker.

- Material: pickaxe speed, mining 8, blast resistance 1200 (vanilla iron 5/6),
  head not mineable on its own, nonflammable, immovable, solid conductor, iron
  RP sounds, `instrument_sound {"up": "note.iron_xylophone"}` (a note block placed
  on the machine plays iron xylophone, as on Block of Iron; vanilla data uses
  `up`). Policies with reasons: each BP's `block_materials.json`.
- Water: both halves are solid and block water (`liquid_detection` blocking), no
  waterlogging, like solid workstations.
- Placement: Core's `vm:machine` `beforeOnPlayerPlace` cancels before the item is
  used when the head cell is not air, is above the build limit, or holds an actor
  (dropped items, XP, projectiles and spectators do not count). The after-place
  handler then sets the head and spawns the trader with no fallback path.
- Loot: only the base drops one machine item (native `explosion_decay`); the head
  has an empty table. Breaking either half removes the other half and the trader.
  If only the head is lost, the base is removed with `setblock ... destroy`
  (support-loss drop). Creative breaks drop nothing. Blast cleanup runs one tick
  later (`system.run`) with captured position/permutation so native blast
  destruction of the base happens first.

## Trader and upgrade

The trader (`vm:trader_<profession>`) is an invisible, persistent, damage-immune
exchange fixture: no families, no biological villager/shulker behaviour, no
stored stock (no hopper/comparator/chest logic). Spawn eggs hidden
(`is_spawnable:false`, still summonable). Invisibility removes the mob shadow and
is re-applied on every load.

- Upgrade Kit (stack 1): use on the base. The item callback is privileged, so the
  upgrade (`vm:apply_upgrade`, dynamic property, `vm:upgraded` block state on both
  halves) and the Survival payment happen in that callback. Creative keeps the kit;
  an already-upgraded machine costs nothing.
- On `entityLoad` a trader whose head block is not its own machine is removed
  (orphan); otherwise its shadow and build mode are reset and an old upgrade's
  block state is restored.

## Trades

`tools/gen_trade_tables.py` owns all 30 tables. Villager tables keep vanilla's five
tiers and XP thresholds, sell every "choice" and `random_aux_value` variant once,
permanent stock, XP on. `_cured` = upgraded: every wants quantity -30% (floor 1).
Librarian: random book replaced by one max-level book per non-curse game
enchantment (`enchantments.json` = level/treasure/tier policy). Wandering trader:
every native offer in one tier; upgraded = vanilla prices, basic = dearer sales and
-30% buyback payouts (minimum 1, bucket/bottle inputs stay native). Shulker:
custom 12/24 basic, 8/16 upgraded. Cartographer keeps `in_overworld`, drops
`is_mark_variant` (the fixture has no biome variant).

### How to update trades

After a game update, run `tools\refresh_vanilla_ref.ps1`, then
`python mods\vending\tools\gen_trade_tables.py` (report only) and
`... --write --report temp\vending-trade-diff.md` to regenerate. It reads each
profession's newest vanilla trade file and the game's enchantment list, rebuilds
every table, and prints what changed per machine level. Flags to read: a
binary-only source (MCB) is read from the same version slice in an old launcher
install (item IDs verified) or falls back to an older slice (FALLBACK: missing
trades); a NEW enchantment is sold at level 1 on tier 4 until `enchantments.json`
gets its values. `node tests/run.mjs --suite catalogs` checks the shipped tables
equal the generator output.

## Owner decisions

- 2026-10-05: crouch-build against the head; standing traders win shared selection.
- 2026-10-05: display goods and recipe ingredients ([GRAPHICS_CONCEPT.md](GRAPHICS_CONCEPT.md)).
- 2026-10-10: any tool or hand collects a machine; mining 8 / blast 1200 kept.
- 2026-10-23: placement checked before payment; synchronous kit upgrade; hidden eggs.
- 2026-10-23: orphan traders are removed on load (minimal check, no scanning).
- 2026-10-23: trades follow current vanilla via the regenerating generator, new enchantments included.

## Known limits

- Head must be pure air (owner policy); vanilla doors also accept replaceable plants/snow.
- Actor check uses the head cell only: a wide mob standing in a neighbouring column is not detected.
- Basic wandering 1-emerald buybacks pay the same as upgraded (minimum 1).
- Leather worker armour keeps vanilla `random_dye`: a random colour per purchase.
- Commands/structures that place or clear blocks bypass the pair logic; an actorless machine is not repaired.

## In-game checks still worth doing

- Placement under a block, at the build limit and with a mob in the head cell: no item used.
- Kit: Survival pays once, Creative keeps it, second use is free; upgrade survives reload.
- Note block on top of a machine plays iron xylophone.
- `/setblock` a machine's head to air, leave and re-enter: the trader is gone.
- New offers: suspicious stew 0-5, bed/banner colours, librarian candles and the four new books.
- Controlled strong blast on a machine vs an iron door: drops match one item.
