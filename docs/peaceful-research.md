# Peaceful machine: research notes

Researcher, 2026-11-21, game 1.26.63 (data pack vanilla_1.26.60). Bedrock Edition only.
Sources: Minecraft Wiki (minecraft.wiki, read 2026-11-21) and vanilla packs on disk (`reference/vanilla/current`,
layered, newest wins). Labels: **[disk]** read from vanilla data; **[wiki]** wiki only, not tested in game;
**[inference]**; **[owner]** owner tested in game.

These are the citations behind `tools/peaceful_rules.json`. Proposals in sections 4-7 are the researcher's
first pass; the owner decisions in [peaceful-machine.md](peaceful-machine.md) and the `decisions` /
`price_overrides` in the rules file supersede them. Current result: [peaceful-catalog.md](peaceful-catalog.md).

## 1. Peaceful facts (Bedrock)

- **Hostile mobs** despawn instantly on Peaceful (natural, spawner, egg, command) [wiki "Difficulty", Peaceful].
- **Stay / spawn**: Ender Dragon (no damage), piglins, shulkers, hoglins (Bedrock only; Java opposite). Sulfur cube
  (passive, released 26.30; preview 26.30.28 "can now spawn in Peaceful") [wiki "Sulfur Cube"].
- **Neither despawn nor spawn naturally** (Bedrock): camel husks, skeleton horses, zombie horses -> treated as absent
  (no Peaceful way to get new ones; they cannot breed). Zombie nautilus spawns on its own only in Java (MC-304858);
  on Bedrock it comes with drowned riders -> listed LIMITED, only drops rotten flesh, no effect. Phantoms "partially"
  despawn on Bedrock (MCPE-55270) and never spawn -> absent. Creaking despawns. [wiki "Difficulty" table + refs]
- **Raids**: a Raid Omen ends without a raid (raiders cannot spawn) [wiki "Difficulty"]. So no raid drops and no
  Hero of the Village. Hero-of-the-Village gifts are **Java only** [wiki "Hero of the Village"] -> no Bedrock item is lost.
- **Sculk shriekers** give no Darkness (no wardens) [wiki]: ancient cities are safe chest runs on Peaceful.
- **Trial spawners**: wiki says they do not activate on Peaceful, tagged "verify for Bedrock Edition"; MC-278006
  (Java) [wiki "Trial Spawner"]. Bedrock unverified -> owner test (section 6). Vault behaviour on Peaceful: not on the wiki.
- **Wither** cannot be summoned [owner, in game, 1.26.63]. The wiki adds: dispensers cannot place wither skulls on Peaceful.
- **Equipment drops**: held items drop at 8.5 % on Bedrock (drowned trident lowered from 25 % in 1.21.120) [wiki "Drowned"
  History]. `slot_drop_chance` 1.0 overrides it (drowned off-hand nautilus shell) [disk].
- **Breeding** [wiki "Breeding"]: armadillo breeds with **spider eyes** (a candidate: armadillo breeding needs the machine;
  scutes come from shedding anyway), frog with slime balls (sold by the wandering trader), nautilus (tame with
  pufferfish, then any fish), trader llama (Bedrock re-enabled 1.19.0). Cannot breed: mule (bred from horse+donkey, so
  renewable: listed breedable), polar bear, dolphin (Bedrock), parrot, bat, squid, fish, happy ghast, sulfur cube
  (splits on death), copper/iron/snow golems (built; their drops are EASY anyway). Allay duplicates (listed breedable).
- **Piglin bartering** gives dried ghasts (a ghast-tear block) and ender pearls; class LIMITED (owner).

## 2. Mobs on Peaceful (as filled in `peaceful_mobs`)

- absent: the owner's list + camel_husk, skeleton_horse, zombie_horse (see above).
- present_breedable (EASY): allay (duplication), armadillo, axolotl, bee, camel, cat, chicken, cow, donkey, fox, frog,
  goat, hoglin, horse, llama, mooshroom, mule (product of breeding), nautilus, ocelot, panda, pig, rabbit, sheep,
  sniffer, strider, trader_llama, turtle, villager, villager_v2, wolf.
- present_limited: bat, cod, copper_golem, dolphin, ender_dragon, fishing_hook (the fishing loot entity), glow_squid,
  happy_ghast, iron_golem, parrot, piglin, polar_bear, pufferfish, salmon, shulker, snow_golem, squid, sulfur_cube,
  tadpole, tropicalfish, wandering_trader, zombie_nautilus.

## 3. Yields per attempt (no Looting) and disagreements

From disk unless noted. Engine computes loot expected values itself; overrides only where it cannot.

| Item | Mechanic / attempt | Yield | Note |
|---|---|---|---|
| blaze rod | blaze kill (0-1, by player/pet) | 0.5 | wiki agrees |
| ghast tear | ghast kill (0-1) | 0.5 | |
| breeze rod | breeze kill (1-2) | 1.5 | |
| spider eye | spider / cave spider kill (0-1 by player) | 0.5 | witch 0.29 |
| phantom membrane | phantom kill (0-1 by player) | 0.5 | wiki agrees |
| bone | skeleton kill (0-2) | 1.0 | fish mobs 25 % (LIMITED) |
| rotten flesh | zombie (0-2) | 1.0 | override: engine would pick camel husk 2.5 |
| prismarine shard | guardian (0-2) | 1.0 | wiki agrees |
| prismarine crystals | guardian 40 % (0-1) | 0.4 | elder 0.33; wiki agrees |
| wet sponge | elder guardian (by player) | 1.0 | |
| tide trim | elder guardian 20 % | 0.2 | |
| totem | evoker | 1.0 | wiki agrees |
| ominous bottle | pillager/vindicator captain (by player) | 1.0 | |
| nether star | wither | 1.0 | data id `netherStar` |
| wither skeleton skull | wither skeleton 2.5 % (by player) | 0.025 | wiki gives no Bedrock number |
| trident | **override 0.085** per drowned holding one | 0.085 | 6.25 % spawn with it x 8.5 % = 0.0053 per random drowned |
| nautilus shell | drowned off-hand 8 % | 0.08 | override (equipment) ; sold anyway |
| creeper discs (12) | **override 1.0** per creeper shot by a skeleton type | 1.0 | data: one of 12 per kill; the buyer chooses |
| lava chicken disc | baby zombie/husk on a chicken, by player | 1.0 | override documents the attempt |
| tears disc | ghast killed by its reflected fireball | 1.0 | |
| trial key | completed trial spawner | 0.5 | wiki 50 %; spawner config is not in loot data |
| ominous trial key | completed ominous spawner | 0.3 | wiki 30 % |
| heads (skeleton, zombie, creeper, piglin) | mob killed by a charged-creeper explosion | 1.0 | Bedrock: no one-head-per-explosion limit (Java only) [wiki "Head"] |
| froglights (3) | tiny magma cube eaten by a frog (ochre=temperate, verdant=cold, pearlescent=warm) | 1.0 | data `entities/frog.json` |
| resin clump | one hit on a creaking at night (2-3 placed) | 2.5 | [wiki "Resin Clump"] |
| wither rose | one mob killed by the Wither | 1.0 | [wiki "Wither Rose"] |

Trial chamber numbers [disk]: entrance chest trial key 6.9 %, corridor pot 2.8 %; normal vault (reward_unique) trident
~2.1 %/opening, ominous bottle ~22 %, emeralds 1.42; ominous vault heavy core ~7.5 %/opening, ominous bottle ~15 %,
emeralds 5.13 + 0.14 blocks. [wiki "Vault"]: each player opens each vault once.

## 4. Per item: sources and proposal

Included (38): see `docs/peaceful-catalog.md` table. Notes per group:

- **Overworld common**: bone (fish 25 %, fishing junk, chests: all LIMITED; needed to tame wolves), rotten flesh
  (cat gifts, fishing, chests; low value, proposal include at 4 for 1 em via a zombie-yield override, owner may drop it), spider eye (desert pyramid
  chests; also armadillo breeding), phantom membrane (cat gifts 2/62), resin clump (natural creaking hearts 1-3, mansion
  chests 17.2 %).
- **Ocean**: prismarine shard (no other source at all), crystals (buried treasure 53 %, natural sea lanterns),
  wet sponge (monument sponge rooms ~30 each, LIMITED), tide trim (elder only; duplicable with diamonds once owned),
  trident (normal vault ~2 %).
- **Heads**: skeleton skull (also placed in ancient cities, LIMITED), zombie head, creeper head (overworld), piglin
  head (nether; piglins remain but no charged creepers). Wither skeleton skull: review (price).
- **Discs**: 11, 13, blocks, cat, chirp, far, mall, mellohi, stal, strad, wait, ward (creeper; 13 and cat also in
  chests: brief's dual-source rule includes them), lava chicken (zombie jockey), tears (ghast). Chest/vault/archaeology-
  only discs excluded: otherside, pigstep, relic, precipice, creator, creator music box, bounce, plus disc fragment 5.
- **Nether**: blaze rod, ghast tear (unlocks dried ghast -> happy ghast, end crystals, regeneration), froglights x3,
  tears disc, piglin head. Magma cream is crafted (blaze powder + slime ball) -> excluded automatically.
- **Deep**: breeze rod (mace, wind charges), ominous bottle, totem (evokers: mansions/raids only), trial keys (review).
- **End boss**: nether star, wither rose.

Excluded with reasons (65): sold (ender pearl cleric, gunpowder/slime ball/nautilus shell/glowstone/red mushroom/name tag
wandering trader, saddle leatherworker, arrows/bow/crossbow fletcher, iron gear, emerald, book, banner...), EASY
(carrot/potato farming, glowstone dust mining, sculk catalyst Silk-Touch mining of natural catalysts, rabbit foot and
string from breedable rabbits / cats / striders), crafted (coal/iron/gold/copper from ores, golden gear, magma cream,
sugar from honey, glass bottle, stick, stone sword, warped fungus on a stick), decisions (raw fish x4: their own
mechanic works; heavy core: sell the ominous key, the ominous vault still works; echo shard, disc fragment: chest only;
Dragon's Breath, dragon egg, elytra: owner). String: cobwebs are LIMITED (owner), but cats and striders (breedable)
drop string, so still excluded.

Not items / nothing lost: zombie sieges, raids (all their items covered: totem, saddle, emeralds, ominous bottle,
ominous banner), witch huts (all witch drops are EASY or sold), monster spawners, Hero gifts (Java only), Bad Omen.
**Ominous banner**: raid/patrol captains only, plus banners placed in pillager outpost watchtowers (LIMITED); not
craftable on Bedrock [wiki "Ominous Banner"]. It shares `minecraft:banner` with ordinary banners in the data, so the
engine excludes "banner" as sold. Left out: decorative, and a trade table cannot obviously give the ominous variant
(Part 2 question if the owner wants it).

## 5. Progression and stages

Unlocks: blaze rod -> blaze powder -> brewing stand, eyes of ender (with cleric ender pearls) -> End; magma cream;
copper bulb; end rod. Ghast tear -> end crystal (dragon respawn), dried ghast (happy ghast), regeneration. Breeze rod
-> mace (with heavy core from the ominous vault), wind charges. Spider eye -> fermented spider eye potions, armadillo
breeding. Phantom membrane -> slow falling, elytra repair. Prismarine -> sea lanterns, conduit frame. Wet sponge ->
sponge. Nether star -> beacon. Trial keys -> vault loot (trident, bolt/flow trims, precipice/creator, heavy core).

Stages (kept the four names) and proposed stage-proof core ingredient (obtainable on Peaceful without any machine):

| Stage | Items | Proof (core) | Why |
|---|---|---|---|
| overworld | common overworld + ocean drops, heads, discs, resin | bone block | composter bone meal or fossils; thematic |
| nether | blaze rod, ghast tear, froglights, tears, piglin head, wither skull | nether wart block | wart grows only in fortresses/bastions; no blaze item, so no circularity |
| deep | breeze rod, trial keys, ominous bottle, totem | echo shard | ancient city chests, safe on Peaceful; alternative: a trial key from pots/entrance chests (chancy) |
| end_boss | nether star, wither rose | shulker shell | End city, only after the dragon; alternatives dragon head, Dragon's Breath |

Open: trial chambers usually come before the Nether in normal play; gating keys behind ancient cities delays the
mace. If the owner prefers, split `trial` (proof: trial key from pots/entrance chests) from `deep`.

## 6. Pricing

Anchors (vanilla SELL offers, `trade_sources.load_trade_source`, game data 1.26.60), emeralds per kill = price/qty x drop:
cleric ender pearl 5 em/1 x 0.5 = 2.5; wandering gunpowder 1 em/4 x 1.0 = 0.25; fletcher arrows 1 em/16 x 1.0 = 0.06;
wandering slime ball 4 em/1 x 1.0 = 4 (trader premium); wandering nautilus shell 5 em x 0.08 = 0.4; leatherworker saddle
6 em x 1 (ravager) = 6; cleric redstone 1 em/2 x 6 (witch) = 3; this mod's Shulker machine 12 em x 0.5 = 6.

Classes B (emeralds per attempt): junk_drop 0.25, common_mob 1, nether_mob 2, trial_mob 2, trial_reward 3,
rare_mob 8, music_disc 8, boss_byproduct 0.5, boss 32. Stage M: overworld 1, nether 1.25, deep 1.5, end_boss 2.

Resulting prices: bone 1, rotten flesh 4/1 em, spider eye 2, membrane 2, shard 1, crystals 3, wet sponge 8, tide trim 40,
trident 12, heads 8 (piglin 10), discs 8 (tears 10), resin 3/2 em, blaze rod 5, ghast tear 5, froglight 3, breeze rod 2,
ominous bottle 2, totem 12, trial key 9, ominous key 15, nether star 64, wither rose 1.
Silly spots: wither skeleton skull 100 em (12 emerald blocks) at 2.5 % -> review; trident at the random-drowned rate
would be ~189 em -> override to per-holder 0.085 (12 em); creeper discs at 1/12 would be 96 em -> override 1.0.
Vault check: trial key 9 em > 1.4 emeralds a normal vault returns; ominous key 15 em > 6.4 an ominous vault returns,
so buying keys never makes emeralds.

## 7. Review items and owner tests

1. **trial_key, ominous_trial_key** (and heavy core exclusion): Peaceful survival world, enter a trial chamber and stand
   in a trial spawner's range (about 14 blocks). Watch: does the spawner light up / spawn / eject a reward? Then drink an
   ominous bottle there (Trial Omen?) and repeat. Also try a vault with a key (found in a pot or given by command). If
   spawners stay idle: include both keys (proposal). If a spawner ejects rewards on Peaceful: exclude them. If vaults do
   not open on Peaceful: the keys are useless there and the heavy core needs re-deciding.
2. **wither skeleton skull price**: 100 emeralds by the formula; keep or override (e.g. 32).
3. Owner choices without tests: rotten flesh include (low value), stage proofs, B/M values, `trial` stage split.

## 8. Bedrock surprises (how solid)

- Hero of the Village gifts are Java only [wiki].
- Drowned trident drop is 8.5 % since 1.21.120 (was 25 %) [wiki History]; spawn chance 6.25 % [disk].
- Charged-creeper heads: the one-head-per-explosion limit is Java only [wiki "Head"].
- Sulfur cubes spawn on Peaceful (26.30.28) and do not breed [wiki].
- Camel husks / skeleton horses / zombie horses never spawn on Bedrock Peaceful but stay if present [wiki].
- Armadillos breed with spider eyes, so Peaceful players cannot breed them until spider eyes are available [wiki].
- Creeper disc loot has one pool per killer type (skeleton, stray, bogged, parched) [disk].
- Witch redstone on Bedrock is a separate guaranteed 4-8 pool [disk].
- Trial spawners on Peaceful: Java does not activate; Bedrock unverified [wiki].
