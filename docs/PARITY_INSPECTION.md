# Vending parity inspection

2026-10-22; source baseline `7b48b27`, target Bedrock **1.26.52**, Script API
**2.8.0**. Group20 of the workspace review. Approved source fixes implemented
2026-10-23; native acceptance remains pending. Torchlight's optional seed-override
test remains pending independently. The original findings below describe the
pre-fix build; the current result and scope follow here.

## Approved implementation, 2026-10-23

Owner approved placement, catalog/generator refresh, iron instrument, hidden eggs,
and upgrade feedback/Creative corrections; questioned practical hand switching
and requested an explanation of ownership. The old upgrade really scheduled a
continuation, but its simulated hand switch is not evidence of a native exploit.
Removed that unnecessary deferral: privileged item use now completes upgrade
and one Survival payment synchronously, with no inventory snapshots/late guards.
Creative keeps its kit. Optional texture/particle/sound/chat errors cannot
prevent payment. Existing actor/tier progress remains on the same entity.

Placement uses a registered Core block hook on all15 machines. It cancels before
native consumption when upper space is occupied/unavailable/out of bounds;
solid/water/air-only policy retained. Upper AABB obstruction checks ignore items,
XP, projectiles and spectators. Failed after-place construction removes only
its owned pair and refunds Survival into inventory, dropping a remainder at the
cleared base when full; Creative gets no refund. Cosmetic shadow failure leaves
a successfully constructed machine intact. No retry, timer or scan was added.

Trade generation now resolves the newest applicable installed versioned source,
with no silent old-install fallback. Selected outputs are built/preflighted
before writes. Wandering tables contain100 offers, including all six buybacks,
current prices/counts, potion metadata and native enchanted-pickaxe functions.
Cartographer exposes all ten map destinations, retaining Overworld restrictions
and removing villager biome-variant filters. Librarian regeneration is idempotent
at46 offers/36 exact books. Other profession catalogs/prices and the custom
shulker balance were preserved. Basic wandering buybacks keep native input
quantities and reduce emerald payout (minimum1); this avoids impossible stacks
of filled buckets/bottles. README now distinguishes these pricing policies.

All15 machine blocks/generators/material checks use native iron xylophone below
a note block. All15 hidden trader descriptions/generators have no spawn egg;
script creation and diagnostic summon remain. Ownership here is **trader-to-block
association**, not player permissions: only an intact pair of the same profession
under that actor can receive load-time upgrade visuals. Unavailable/missing/
mismatched owners are skipped. **No automatic orphan deletion was implemented**;
that proposed policy still needs an owner decision. No actorless command/clone/
structure recovery was added.

Six independent test runners pass: original30 tests retained,18 new Node cases,
eight catalog tests and the suite-layout guard. New fixture helpers do not import
other suites. Shared verifier now resolves component registrations from exact
declared sibling script dependencies; malformed/unrelated/wrong-version providers
do not satisfy registration. Its1599 regression assertions pass. Four BP/RP
combinations and localization pass with0 errors/0 warnings/0 exceptions.
Managed deploy2026-10-23 copied1 Core,3 Shulker,29 Villager and5 Wandering files,
removed0; RP already matched. `mods status vending` confirms **all five packs
in sync**. Re-enter the world to load changes; no new world required. No new
native observations. Current game checks: failed/obstructed/ceiling placement and
full-inventory refunds; Survival/Creative/repeated kit uses; all ten generated map
targets in valid dimensions; wandering buybacks/metadata outputs; retained trade
XP/reload/upgrade behavior; hidden egg menu and both-half instrument sounds.

Scope: all15 machines, their15 hidden traders, both standalone items, ordinary
and upgraded tables, paired halves, build-mode states, recipes and generators.
Exact membership is in [the inventory](VANILLA_INTERACTIONS.md).

## Original findings and evidence (pre-fix build)

1. **Make upgrades and payment agree.** `vending_bp/scripts/main.js` defers kit
   use through `system.run`, applies the trader event/property and both textures,
   plays particles/sound/chat, and only then examines the *current* main hand.
   Production-handler substitution reproduced:
   - Switch from kit to stick before the queued callback: machine upgrades,
     stick stays, no kit is charged.
   - Throw from the particle call: machine upgrades, kit remains; callback exits
     before consumption. This is an injected failure path, not an observed
     native particle failure or a claimed engine failure rate.
   - Creative use: the kit is removed just as in Survival.
   Proposed: complete the action synchronously in this privileged item callback
   if supported by the pinned hook, avoiding the unnecessary scheduling gap;
   otherwise use an explicit deferred transaction for the accepted kit and
   target. Validate the matching base/head/trader before committing. Charge
   exactly one kit in Survival and none in Creative; repeated/already-upgraded
   uses cost nothing. Keep optional feedback outside successful payment/state
   settlement. Do not add arbitrary delayed movement conditions or artificial
   synchronous player-race guards. Preserve the same trader and its progress.

2. **Reject impossible placement before payment.** The current after-place
   handler only accepts `above.isAir`, removes the base when blocked, then spawns
   a refund item in every game mode. The Creative blocked-headroom route
   reproduced one extra dropped machine. Survival refunds are dropped into the
   world even when inventory space exists. API2.8's cancellable
   `beforeOnPlayerPlace` is available for the headroom/bounds check. Proposed:
   use that native cancellation path so the original item is never consumed on
   rejection. Keep the existing solid/water policy; replaceable vegetation,
   entity obstruction and world-ceiling handling need explicit placement checks.
   Also settle failures after construction begins: injected `spawnEntity`
   failure currently leaves both blocks and no trader/refund. Roll back only
   this placement's owned parts, with a Survival-only refund if native payment
   has already happened. This conditional cleanup is not evidence that spawning
   would succeed on a later attempt; no retry or ongoing checker is proposed.
   Native multi-block migration is a separate compatibility change, not needed
   just to add a cancellable check to existing machines.

3. **Refresh the trade catalog from current versioned vanilla sources.**
   The wandering generator hardcodes an older68-offer catalog; current readable
   `vanilla_1.26.50/trading/economy_trades/wandering_trader_trades.json` contains
   100 candidate offers before vanilla selection. Missing are all six buyback
   routes and many wares. Concrete upgraded-price mismatches:

   | Ware | Current vanilla | Upgraded machine |
   | --- | --- | --- |
   | Gunpowder | 4 for1 emerald | 1 for1 |
   | Packed ice | 1 for1 emerald | 1 for3 |
   | Tropical/pufferfish bucket | 1 for3 emeralds | 1 for5 |

   Cartographer's shipped table has only monument/mansion map destinations.
   The readable1.21.70 table has ten: those two, trial chambers, five village
   biomes, swamp hut and jungle temple. The seven biome maps and wandering
   buybacks/updated prices are **stable**, released from the trade experiment
   in official1.21.70. Current26.50 also releases poplar/shelf-mushroom content.
   Proposed: keep the machine's all-offers policy, tiers, kit and custom shulker
   balance; import current stable wares/functions/prices and all applicable map
   destinations. Retain dimension restrictions, but adapt villager biome filters
   deliberately: these fixture actors have no authored biome variant. Merely
   copying `is_mark_variant` filters would hide parts of the catalog. Verify
   metadata aliases, enchanted pickaxe/potion outputs, full-stack prices and
   map destinations; no experimental trade rebalance is required.

   Correct the generation pipeline at the same time. The old generator searches
   the base directory or an older launcher install, missing readable *versioned*
   overrides. Do not regenerate from that fallback and call the result current.
   In-memory invocation of `gen_book_trades._patch` on the shipped librarian
   table increases46 offers to82:36 exact book trades are appended again.
   Make the standalone book patch idempotent and test repeated generation.

   Pricing documentation also needs scope correction: README says upgraded
   prices equal vanilla and base prices are dearer; the13 profession generator
   actually keeps its source prices as base and reduces upgraded wants30%.
   Example: wheat20 ->14 for one emerald. That reduction is documented in the
   generator and longstanding kit behavior. Recommend retaining it and describing
   the distinct villager/extra-machine rules accurately, without a general
   villager-price rebalance in this batch. Keep existing multipliers unless a
   separate fixed-price decision is made; demand behavior needs native testing.

4. **Use the iron note-block instrument.** All15 block definitions omit
   `minecraft:instrument_sound`. The iron-material counterpart uses
   `note.iron_xylophone` below a note block; omission defaults to harp.
   Proposed: add native `down: note.iron_xylophone` consistently in the main
   generator, generated blocks, extra-machine routes and material expectations.
   Keep `up` behavior at its default. This component is stable since26.40;
   Learn's remaining experimental warning is stale. No API upgrade or experiment
   is needed. Both halves and upgraded/build-mode states need a game sound test.

5. **Hide internal trader spawn eggs.** All15 entities have
   `is_spawnable:true`, although these are invisible, persistent, damage-immune
   fixture actors intended to be created with their blocks. That exposes a
   separate way to create a trader without a machine or normal block teardown.
   Proposed: `is_spawnable:false` in the generator/templates, retain script
   creation and intentional diagnostic summon support. Validate matching machine
   ownership when a trader loads before applying the old-upgrade visual migration;
   the current migration accepts any machine prefix below the actor, including
   a different profession. Delete only demonstrably orphaned internal actors,
   preserve valid/temporarily unavailable owners. Do not claim this supplies
   automatic recovery for command-created blocks with no actor.

## Counterpart applicability and continuing coverage

The machine is a solid shop fixture. Iron is its material analogue; doors supply
paired ownership/failed-placement comparisons; villagers supply trade mechanics.
The invisible actors are not living villagers, wandering visitors or shulkers.
Their names and goods do not imply breeding, beds, workstation claims, village
population, raids, infection, bell schedules, golem summoning, leads, name-tag
care, natural wandering/despawn, dyeable shells, teleportation, bullets,
duplication or combat loot. Those biological roles are inapplicable to this
documented fixture design. Do not add villager/shulker/monster families merely
for the trade UI. Missing families alone are not proof that every native mob
will ignore the actor; attack/selection/obstruction remain separate engine tests.

Likewise, a trade screen is an exchange, without stored stock. Recommend retaining
no chest inventory, hopper insertion/extraction, fullness comparator or chest
opening/piglin anger. This does not exclude normal hopper/dropper transport of
the *dropped/inventory items*, or observer/sculk events from placement and state
changes. Shulker-machine chest input does not make the fixture a shulker box.
The core is a crafted nine-shell resource consumed by the custom machine recipe;
it has no biological shulker role or inferred food/compost/fuel use.

Preserve approved any-tool collection, mining8, blast1200, upper mining immunity,
iron sounds, solid water exclusion, immovability, build-mode trade priority and
base-only native loot. Keep existing machine-owned progress/upgrade lifetime;
no new portable progress preservation is proposed. Ordinary resources use native
item stack/lifetime/transport behavior; recipes and unlocks are defined, not
newly confirmed in game. The optional packs all depend on Core.

Remaining OPEN engine/compatibility cases: upper-only controlled door/machine
blast comparison; actual placement cancellation/refunds and collision at upper
space; underwater trade; both-part attachments; piston/slime/honey refusal;
redstone conduction, observers/sculk, spawn/suffocation/grass/light/rain/snow/map
effects; native trade XP, reload/upgrade retention and randomly enchanted offer
rerolls; full-inventory trade delivery and multi-player UI ownership; egg/summon
visibility and item hazards/gamerules. Silent commands, clone/structure placement
and removal can bypass player/explosion wiring; actorless blocks and stale
actors need a separately specified supported command/structure policy. Avoid a
world scan or continuous crop-style checker as an assumed solution. Door opening,
wind-charge opening and door-specific hinges are not machine functions. Beacon
base, golem-body and iron-ingot unpacking recipes are not implied by metal casing.

## Evidence and validation

All15 actor definitions share the inspected component layout; all15 block IDs
share the generator policy. Main, build-mode and message scripts, recipes,
trade generators, table destinations and the existing lifecycle tests were read.
`node tests/run.mjs`: **30/30 pass**. `mods verify vending`: localization and
all four BP/RP combinations pass with **0 errors, 0 warnings, 0 exceptions**.
These existing suites do not cover the newly identified paths. Reproductions
load actual production handlers with a narrow API substitute; hand switching
happens across the real queued callback, not inside a fake synchronous getter.
Initial inspection scratch was in `temp/vending-inspection/`; production
regressions now preserve the relevant cases. Workspace inspection/handoff
commit: `288b0f7`; shared implementation/verifier handoff: `5029b4e`.
Vending implementation and mod documents remain uncommitted.

Sources retrieved2026-10-22:

- Local API2.8: `BlockComponentPlayerPlaceBeforeEvent.cancel`, item-use callback
  and `Dimension.spawnEntity`; current readable wandering1.26.50/cartographer
  1.21.70 JSON. Older unversioned binary files are not the entire vanilla source.
- Official [1.21.70 release](https://feedback.minecraft.net/hc/en-us/articles/35256043330189-Minecraft-Bedrock-Edition-1-21-70-Spring-to-Life):
  stable cartographer/wandering changes, distinct from remaining experiments.
- Official [26.40](https://feedback.minecraft.net/hc/en-us/articles/47787720931213-Minecraft-Bedrock-Edition-26-40):
  released instrument component. [26.50](https://feedback.minecraft.net/hc/en-us/articles/48826825649933-Minecraft-Bedrock-Edition-26-50-Changelog-Wilderness-Bound),
  [26.51](https://feedback.minecraft.net/hc/en-us/articles/48915928859789-Minecraft-Bedrock-Edition-26-51-Hotfix-Changelog)
  and [26.52](https://feedback.minecraft.net/hc/en-us/articles/49175370527501-Minecraft-Bedrock-Edition-26-52-Hotfix-Changelog)
  checked for later relevant changes; no announced repair replaces these
  authored kit/placement checks. Current26.50 poplar trades corroborate source.
- Creator [trade schema](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/tradetablereference/examples/tradetablecomponents/tradesingle?view=minecraft-bedrock-stable):
  item metadata suffixes, default multiplier0.05, use limits and separate player/
  trader XP. [Instrument](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/blockreference/examples/blockcomponents/minecraftblock_instrument_sound?view=minecraft-bedrock-stable):
  `down` instrument/default harp; experimental notice superseded by release.
  [Native multi-block guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/multi-blocks?view=minecraft-bedrock-stable):
  available alternative, with different states/selection/destruction semantics.
- Canonical Wiki pages: [Block of Iron](https://minecraft.wiki/w/Block_of_Iron),
  [Door](https://minecraft.wiki/w/Door), [Trading](https://minecraft.wiki/w/Trading),
  [Villager](https://minecraft.wiki/w/Villager), [Wandering Trader](https://minecraft.wiki/w/Wandering_Trader),
  [Shulker](https://minecraft.wiki/w/Shulker). Direct current trader fetch was
  robots-blocked; read corresponding **November2025** archive pages at
  `https://wiki.ronlab.site/content/minecraftwiki_en_all_maxi_2025-11/<Page>`.
  Inspected obtaining/material uses/instrument, paired placement/behavior,
  trade progression/stock/prices, villager jobs, wandering spawn/trades and
  shulker behavior/damage/usable dye. No revision ID/current-Wiki claim. These
  sections supply discovery and archetype exclusions; later changelogs/local
  data take precedence. All linked peripheral native cases are not thereby
  certified; the OPEN rows above remain pending.
