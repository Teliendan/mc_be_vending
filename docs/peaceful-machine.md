# Loot Machines (Peaceful resource machines)

## Owner decisions (2026-11-21, Bedrock 1.26.63)

The original design brief (written by ChatGPT, a starting point, not a spec) is in git history before commit
97052b9; these decisions override it.

- Neutral mobs: breedable = EASY, anything else = LIMITED (resolves the 2.5 / EASY-list conflict).
- Anything a villager or vending machine SELLS is excluded. Items villagers only buy are not priced from
  those buy offers (vanilla buy prices are far below sell value).
- Gates: several machines by progression stage are acceptable; each must take the Upgrade Kit like the others.
- Not enforced to Peaceful: anyone can craft and use it, in its own feature pack. Peaceful is only the motivation.
- Upgrade Kit works as on the other machines.
- Experimental-toggle content is left out.
- Peaceful facts (wiki, not tested in game): shulkers and the Ender Dragon stay but deal no damage, so
  shulker shells, Dragon's Breath and the egg stay normal End gameplay; piglins and Bedrock hoglins stay.
  See `bedrock-mobs` reference `spawning.md`, "Peaceful difficulty".
- Piglin bartering is a LIMITED source (does not exclude an item). Re-decide when a Piglin machine exists.
- The Wither cannot be summoned on Peaceful (owner, in game, 1.26.63, 2026-11-21): Nether Star and
  Wither Roses are candidates.
- Cobwebs are LIMITED (structure blocks); a recipe counts as EASY only when every ingredient is EASY.
- Prices are paid in emeralds only, never blocks; at most 128 (two wants slots of 64). The nether star
  is the most expensive item, at 128.
- All mob heads cost 16, the wither skeleton skull included (decorative only on Peaceful).
- Breeze rods cost the same as blaze rods. The trident is raised to 32 to stay rare.
- Trial spawners do not spawn mobs on Peaceful (owner): the machine sells trial keys and ominous trial keys
  in place of their rewards. The ominous bottle is sold (decorative use).
- Stages, one machine each: overworld, nether, trial, end. The proof each machine recipe needs:
  bone block, red nether bricks, trial key, shulker shell (proposals, final in Part 2).
- String is an owner exception: sold in the overworld machine, because its only early EASY source is killing cats.
- Wet sponge is excluded: its main source is monument sponge rooms; elder guardians cannot be farmed.
  Prismarine shards and crystals stay: ordinary guardians respawn.
- The reasons per item go into the player wiki in Part 2, generated from the rules file.

Part 2 decisions (owner, 2026-11-21, Bedrock 1.26.63):

- Player-facing name: "Loot Machine", in the existing "<X> Machine" pattern: Overworld / Nether / Trial / End
  Loot Machine. Internal IDs follow it: `vm:machine_loot_<stage>`, pack `vending_loot_bp`. "Peaceful" stays the
  design motivation and the name of the catalogue tools.
- One feature pack with all four machines; the same body as the other machines, only the glass item differs.
- Glass item: Overworld = bone, Nether = blaze rod, Trial = breeze rod, End = nether star.
- Recipe keeps the shared GTG / IWI / EEE shape. T points to what the machine sells and is not sold anywhere;
  W is the stage proof: Overworld T carved pumpkin, W bone block; Nether T magma block, W red nether bricks (nether wart block also grows in crimson forests, owner fix 2026-11-22);
  Trial T copper grate, W trial key (found in chamber chests and pots; the machine also sells keys);
  End T end crystal, W shulker shell.
- After the in-game check: the totem costs 32 (was 12; strong, rare, priced like the trident); the wither rose costs 16 (was 1; very hard to get normally); resin clumps are
  9 for 1 emerald, one block of resin (was 3 for 2; a building material needs several per block).
  Offers are sorted the same in every machine: ordinary loot first, cheapest first, then mob heads, then
  music discs; families (prismarine, trial keys, froglights) stay together at their cheapest member's price
  (`loot_offer_order`, `LOOT_FAMILIES` in `tools/gen_extra_machines.py`).
- Czech names keep the Bedrock term "zkušební komory" for Trial Chambers (owner, 2026-11-21).
- Verified in game (owner, 1.26.63, 2026-11-21): the nether star trade takes 64 emeralds in each of the two
  payment slots and charges both.

## Status and files (2026-11-21)

Done and accepted by the owner (2026-11-21, Bedrock 1.26.63): Part 1 catalogue `adf78bf`, Part 2 machines `97052b9`,
owner price follow-ups in the commit after it. Every offer, the upgrade, the nether star two-slot trade and
break/drop were checked in game.

- `tools/peaceful_rules.json`: hand-kept knowledge, every entry with reason and ref; the single source of truth.
  Prices change only here (`price_overrides`), then `python tools/build.py`.
- `tools/gen_peaceful_catalog.py` (+ `peaceful_sources.py`): reads the layered vanilla data, writes
  `tools/peaceful_catalog.json` and the audit [peaceful-catalog.md](peaceful-catalog.md); run by `build.py`,
  `--check` by suite `generated`. Rerun after a game update.
- `tools/gen_extra_machines.py`: the four machines (`LOOT_STAGES`), their trade tables from the catalogue and
  the offer order (`loot_offer_order`, `LOOT_FAMILIES`). Test: suite `catalogs`.
- `tools/gen_loot_wiki.py`: wiki features, behaviour and per-item reasons (`--check`); rerun after any change to
  the loot pack, the catalogue or the rules, then the wiki export.
- Citations behind the rules: [peaceful-research.md](peaceful-research.md).
