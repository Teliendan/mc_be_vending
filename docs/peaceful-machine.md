# Vending Machines — Peaceful Mode Resource Machine

## Owner decisions (2026-11-21, Bedrock 1.26.63)

The brief below is a starting point written by ChatGPT, not a literal spec. These decisions override it.

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
  bone block, nether wart block, trial key, shulker shell (proposals, final in Part 2).
- String is an owner exception: sold in the overworld machine, because its only early EASY source is killing cats.
- Wet sponge is excluded: its main source is monument sponge rooms; elder guardians cannot be farmed.
  Prismarine shards and crystals stay: ordinary guardians respawn.
- The reasons per item go into the player wiki in Part 2, generated from the rules file.

## Status and files (2026-11-21)

Part 1, the catalogue, is done; Part 2 builds the machines from it.

- `tools/peaceful_rules.json`: hand-kept knowledge, every entry with reason and ref; the single source of truth.
- `tools/gen_peaceful_catalog.py` (+ `peaceful_sources.py`): reads the layered vanilla data, writes
  `tools/peaceful_catalog.json` (for Part 2) and the audit [peaceful-catalog.md](peaceful-catalog.md).
  `--check` fails when the outputs are stale. Rerun after a game update or a rules change.
- Citations behind the rules: [peaceful-research.md](peaceful-research.md).
- Part 2 to verify in game: a trade with emeralds in both wants slots (nether star 64 + 64).

## Design & Implementation Brief

### 1. Objective

Add a new vending machine category dedicated to players playing Minecraft Bedrock in Peaceful difficulty.

The purpose is to restore access to resources whose normal acquisition methods depend on hostile mobs or mechanics unavailable in Peaceful mode.

The machine should:

* Remove the need to build mob farms or rely on unavailable mob interactions.

* Preserve the normal Minecraft resource economy and progression.

* Preserve the rarity of resources as much as possible.

* Avoid selling resources that are already reasonably accessible through ordinary Peaceful gameplay or existing vending machines.

* Allow players to progress through the game normally, including reaching the Nether and End.

This is not a general-purpose convenience shop. It is a replacement for missing resource acquisition mechanics.

### 2. Core design principles

**2.1. Preserve normal-mode rarity**

If an item is rare in normal gameplay, it must remain rare when obtained through the Peaceful machine.

The machine replaces unavailable acquisition methods; it must not make rare resources abundant.

Pricing and trade quantities should reflect the expected yield of the original normal-mode acquisition method.

**2.2. Evaluate acquisition methods, not just item categories**

An item should not automatically qualify simply because its primary source is a hostile mob.

Evaluate all meaningful ways to obtain it in Peaceful mode, including:

* Mob drops.

* Block drops and harvesting.

* Crafting recipes.

* Villager trades.

* Existing vending machines.

* Fishing.

* Cat gifts.

* Structure loot.

* Trial chamber rewards.

* Special environmental interactions.

* Other renewable or non-renewable sources.

**2.3. Crafting from accessible materials makes an item accessible**

If an item can be crafted from materials that are reasonably obtainable in Peaceful mode, it should not be sold separately.

This includes materials obtainable through any existing vending machine, including the new Peaceful machine itself.

Apply this rule recursively through crafting dependencies.

For example, if Blaze Rods become available through the Peaceful machine, Blaze Powder becomes obtainable through crafting and should not need its own trade.

Likewise, if all ingredients for Magma Cream are accessible, Magma Cream should be excluded.

**2.4. Existing vending machines count as accessible sources**

The following are considered accessible:

* Villager trades.

* Wandering Trader trades.

* Shulker trades, once the player has access to the End and can obtain initial shells.

* Piglin barter trades once the dedicated Piglin machine exists.

Do not duplicate resources already covered by these machines.

**2.5. Neutral and breedable animals**

Drops from neutral mobs that spawn in Peaceful are considered limited, unless they are breedable.

Breedable animals are considered easy sources.

Do not sell their drops merely because obtaining them might be less convenient than building a mob farm.

### 3. Source classification

Every relevant acquisition source should receive one of the following classifications.

| Classification | Meaning                                                                   |
| -------------- | ------------------------------------------------------------------------- |
| EASY           | Reasonably obtainable through ordinary Peaceful gameplay                  |
| LIMITED        | Technically obtainable, but uncommon, inconvenient or dependent on chance |
| UNAVAILABLE    | Requires a mob or mechanic that cannot operate in Peaceful                |
| SPECIAL        | Explicitly approved exception with its own rules                          |

#### EASY sources

Examples:

* Mining and ordinary harvesting.

* Drops from neutral mobs that spawn in Peaceful.

* Ordinary crafting from accessible ingredients.

* Villager trades.

* Wandering Trader trades.

* Existing vending machines.

* Normal renewable environmental sources.

An item with an EASY acquisition path should normally be excluded.

#### LIMITED sources

These are valid sources in Peaceful, but should not automatically disqualify an item.

Examples:

* Fishing.

* Cat gifts.

* Rare structure chest loot.

* Trial chamber vault rewards.

* Rare environmental interactions.

* Neutral nonbreedable mobs.

An item obtainable only through LIMITED sources remains eligible for the machine if its intended normal acquisition method is an unavailable drop or mechanic.

This is deliberate: finding one item in a rare chest is not equivalent to having a practical way to obtain it.

#### UNAVAILABLE sources

Examples:

* Drops from hostile mobs that do not spawn in Peaceful.

* Drops from bosses that cannot be fought.

* Rewards from mechanics requiring unavailable hostile entities.

* Special interactions that depend on hostile mobs.

These are the primary candidates for the machine.

#### SPECIAL sources

Some resources are not ordinary mob drops but are still closely tied to mechanics unavailable in Peaceful.

Maintain explicit exceptions for these resources.

Examples include:

* Froglights: frogs eating magma cubes.

* Dragon's Breath: collecting dragon fireball clouds.

* Wither Roses: the Wither killing another mob.

* Trial Keys and Ominous Trial Keys: completing trial spawner encounters.

* Resin Clumps: Creaking-related interactions.

Special exceptions must still respect alternative-source and progression rules.

### 4. Eligibility rules

An item qualifies for the Peaceful machine when:

1. It is normally obtained through a loot/drop mechanic or an explicitly approved special mechanic.
2. Its intended normal acquisition method is unavailable or disproportionately difficult in Peaceful.
3. It has no EASY alternative acquisition path.
4. It cannot be crafted from easily accessible ingredients.
5. It is not already covered by another vending machine.
6. It is not an End resource that becomes accessible through normal End exploration after the player unlocks the End.

An item with only LIMITED alternatives can qualify.

An item with an EASY alternative should be excluded, even if its primary normal-mode source is unavailable.

#### Important music disc exception

Music discs require special consideration.

If a music disc can be obtained both:

* From a structure chest, and

* Through a mob drop or special mob interaction,

include it in the Peaceful machine if that drop method is unavailable.

The chest source does not disqualify it.

However, if a disc is obtainable only through structure chests in normal gameplay, do not add it to the machine. Preserve its normal acquisition method.

This distinction is important because the machine should replace missing acquisition mechanics, not duplicate ordinary structure loot.

### 5. Explicit exclusions and special decisions

**Dragon Egg**

Do not sell the Dragon Egg.

The Ender Dragon can be killed in Peaceful, so the egg remains obtainable through normal gameplay.

It is not a missing Peaceful resource.

**End resources**

Do not sell resources that become reasonably accessible after reaching the End.

This includes:

* Shulker Shells.

* Elytra.

* Chorus Fruit.

* End-exclusive building resources.

* Other normally obtainable End resources.

The machine should provide the missing resources necessary to reach the End, not bypass End exploration.

The existing Shulker vending machine remains responsible for Shulker Shell trades.

**Sea Lanterns**

Do not sell Sea Lantern blocks.

Evaluate their crafting ingredients separately. Resources required for crafting Sea Lanterns may qualify if their normal acquisition methods are unavailable and no EASY alternative exists.

**Trial Keys**

Trial Keys and Ominous Trial Keys should be considered candidates because their intended acquisition requires completing trial spawner encounters.

Rare structure-loot alternatives do not automatically disqualify them.

**Mob heads**

Include eligible mob heads when their normal acquisition requires a mechanic unavailable in Peaceful, such as a charged creeper killing the relevant mob.

**Music discs**

Apply the specific dual-source rule described above.

### 6. End progression

The Peaceful machine must make normal End progression possible.

Blaze Rods are particularly important because they unlock Blaze Powder, Eyes of Ender and ultimately access to the End.

Blaze Rod availability must therefore be gated by progression, but it must not depend on already possessing Blaze Rods or another resource that requires them.

As the player can reach the End, resources normally obtainable there are considered accessible and should not be sold by the Peaceful machine.

The machine should not replace the exploration and resource acquisition gameplay of the End.

### 7. Pricing principles

Pricing must preserve normal-mode rarity.

Do not assign arbitrary prices manually to every item.

Base the price on the expected yield of the original normal-mode acquisition method.

Examples:

* Guaranteed one item per kill: expected yield 1.

* 50% chance of one item: expected yield 0.5.

* 25% chance of one item: expected yield 0.25.

* Guaranteed two items: expected yield 2.

For mob drops, use the baseline drop probabilities without Looting enchantments.

For other mechanics, define a consistent acquisition attempt:

* Mob drop: one mob killed.

* Block drop: one block harvested using the intended tool.

* Special interaction: one successful interaction.

* Structure loot: one relevant chest opened.

* Trial reward: one completed trial spawner reward.

For weighted loot tables, calculate expected quantities across all possible outcomes.

A conceptual pricing model:

P = B × M\_source × M\_progression / E\_yield

Where:

* B = base emerald value of one standard acquisition attempt.

* M\_source = source difficulty multiplier.

* M\_progression = progression multiplier.

* E\_yield = expected item quantity per acquisition attempt.

The coefficients should be calibrated against representative normal-mode resources rather than selected independently for every item.

Avoid making rare resources disproportionately cheap simply because their Peaceful alternative is inconvenient.

Craftable derivatives should not receive separate trades when their ingredients are already available.

### 8. Progression and availability gates

Use a small number of coherent progression tiers rather than individually inventing a progression system for every item.

Suggested conceptual tiers:

| Tier | Progression          | Typical resources                             |
| ---- | -------------------- | --------------------------------------------- |
| 0    | Early Overworld      | Basic missing drops                           |
| 1    | Advanced Overworld   | More specialized drops and mob heads          |
| 2    | Nether access        | Blaze Rods, Ghast Tears and related resources |
| 3    | Advanced progression | Trial-related and other difficult resources   |
| 4    | Endgame exceptions   | Remaining special-mechanic resources          |

These tiers should be refined according to actual gameplay dependencies.

Important requirements:

* No circular progression dependencies.

* Blaze Rods must be obtainable before End access.

* End resources must remain the result of End exploration.

* Special and exceptionally valuable resources may require additional gates.

* Gates should preserve the intended normal progression as closely as possible.

### 9. Exceptions and future maintenance

Maintain explicit exceptions for mechanics that cannot be reliably classified from item and loot data alone.

Examples:

* Frogs eating magma cubes.

* Dragon's Breath collection.

* Wither Rose generation.

* Charged creeper mob-head drops.

* Creaking and Resin interactions.

* Trial spawner rewards.

* Shulker spawning and duplication.

* Other unusual interactions discovered in future updates.

Exceptions should contain:

* The affected item.

* Its normal acquisition mechanic.

* Why the mechanic is unavailable or difficult in Peaceful.

* Alternative sources and their classifications.

* Eligibility decision.

* Progression tier.

* Any special pricing or quantity rules.

* Explanation of the decision.

Unknown mechanics must be flagged for review rather than silently classified.

### 10. Minecraft update review

The system must support repeated analysis after Minecraft updates.

When a new Bedrock version is available:

1. Identify newly introduced items and changed existing items.
2. Identify changed loot sources, recipes, trades and acquisition mechanics.
3. Re-evaluate affected items using the established eligibility rules.
4. Identify new or changed Peaceful-specific exceptions.
5. Recalculate affected prices where normal acquisition yields have changed.
6. Identify progression dependencies that may have changed.
7. Produce a review report explaining proposed catalogue changes.

Use the existing Bedrock knowledgebase as the primary source of mechanics and item information.

LLM-assisted analysis is expected and encouraged, particularly for:

* Unusual gameplay mechanics.

* Newly introduced mobs and their drops.

* New resource acquisition methods.

* Changes to Peaceful behaviour.

* Ambiguous alternative sources.

* Special exceptions.

The LLM should propose and explain decisions, not silently approve uncertain classifications.

### 11. Explainability and auditability

Every evaluated item should have a recorded classification and reasoning.

The system should be able to answer:

* Why is this item included?

* Why is this item excluded?

* Which normal-mode acquisition method does it replace?

* What alternative Peaceful sources exist?

* Why are those alternatives considered easy or limited?

* Is it craftable from accessible ingredients?

* Which vending machine already provides it?

* What determines its price?

* What progression gate applies?

Preserve this reasoning in generated catalogue data or an accompanying audit report.

A human-readable explanation is an important output, not merely debugging information.

### 12. Expected outcome

The finished system should produce:

1. A Peaceful machine catalogue containing eligible items, trade quantities, prices and progression gates.
2. A complete evaluation of relevant items, including excluded items and their reasons.
3. A maintained set of special mechanic exceptions.
4. A human-readable audit report.
5. A repeatable update review process.
6. Clear identification of uncertain or manually reviewable decisions.

The result should be a maintainable, explainable system that can be re-evaluated whenever Minecraft Bedrock receives an update.

**Final design principle: Restore what Peaceful removes, preserve what Peaceful still offers, and never make a rare resource common just because its original acquisition method is unavailable.**
