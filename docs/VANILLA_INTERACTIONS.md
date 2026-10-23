# Vanilla interaction ledger

2026-10-18 inventory; Group20 approved source fixes updated **2026-10-23**.
Target Bedrock **1.26.52** / Script API **2.8.0**.
Approved source implementation and offline verification; **native acceptance pending**.

The [Group20 inspection](PARITY_INSPECTION.md) records the concrete upgrade,
placement, trade-catalog/generator, instrument and internal-egg proposals.
Owner approved the fixes on2026-10-23. All six feature runners and four pack
combinations pass. Automatic orphan deletion remains undecided; no new game observations.

Follow the [shared interaction workflow](../../../.claude/skills/bedrock-modding/references/22-vanilla-interactions.md)
and [source/coverage report](../../../docs/vanilla-interactions-audit-2026-10-18.md).
The source report supplies canonical/archived Wiki URLs, inspected sections and
access/version limits. November 2025 archived pages are discovery evidence, not
proof of current engine behavior.

Every identifier below inherits the shared common prompts and its family row.
Linked block items, entity placers, projectiles and variants must be tested as
one feature. Existing notes establish only the interactions they actually
describe. **OPEN** means discovery/intent/implementation or game behavior remains
unresolved; no family below claims a completed all-interactions parity sweep.
For closure, expand the family row into individual interaction outcomes using
the shared row format and record test version/date.

## Family findings and decisions

| Group | Counterparts / existing evidence | Disposition and remaining interactions |
| --- | --- | --- |
| Machine | Iron block material, door-like paired ownership, custom shop function; `VANILLA_PARITY.md`, `LIFECYCLE.md`, `WATER.md`, `BLOCK_MATERIALS.md`, `INTERACTIONS.md` | **Intentional:** collectible by hand/any tool, blast resistance 1200, upper mining immunity, one owning-item lower part; preserve approved iron sounds. Crouch placement against upper head is owner-tested. **OPEN:** door/machine controlled explosion comparisons, native wind/projectile/piston/command/support changes, comparator/observer/sculk/spawn/suffocation and rain/map/attachment contexts to the exact existing test scope. |
| Trader | Villager/wandering trader/shulker analogue per role; actor JSON and shop scripts | Trade-backed UI, persistent actor and teardown implemented. Group20 records the exchange-fixture design: no biological villager/shulker jobs. Native prices/demand/XP/reload and physical actor behavior remain OPEN; individual outcomes below supersede the original broad discovery row. |
| Upgrade resources | Custom kit/core and the actual upgrade recipes/scripts | **OPEN:** acquisition and recipe consumers, stack/use/Creative/consumption, full-inventory return and automation. Do not infer shulker behavior from the core's name. |

A vending trade screen is not an inventory chest. Hopper insertion/extraction,
container break contents, comparator fullness and piglin container anger are
inapplicable to the documented exchange-without-stock design. Native actor and
block behavior still requires testing. Normal dropped-item/hopper transport applies to machine items
and kit/core, and cannot be dismissed with a blanket container n/a.

Group20 resolves these applicability questions through the documented
shop-fixture design: retain no stored-stock inventory and no biological villager/
shulker roles. The detailed reasons and remaining native actor tests are in the
inspection. These are role-based dispositions, not claims of tested native
immunity. Automatic orphan deletion remains undecided. The expanded rows below
and [final reconciliation](../../../docs/vanilla-interactions-final-2026-10-23.md)
retain unresolved supported paths and native acceptance.

## Group20 interaction outcomes

Membership: **Machine** means the15 enumerated block IDs below, both halves and
all upgraded/build-mode states; **Trader** means their15 exact paired entity IDs;
**Resources** means both enumerated item IDs. Profession-specific cases name
their member. Source/offline evidence updated2026-10-23, target1.26.52/API2.8.0.

| IDs / states | Interaction / counterpart aspect | Required outcome | Disposition | Evidence | Verification / next test |
| --- | --- | --- | --- | --- | --- |
| Machine, inventory forms; Resources | Acquisition, recipe station/unlock/count | Existing custom recipes, native book unlocks and stack limits | Implemented/native | All feature recipes; kit stack1/core64; recipe generators | Source/verify; craft/unlock/full inventory native checks pending |
| Machine, either half | Mining speed vs collection, Silk/Fortune | Preserve approved any-tool collection, mining8/pickaxe speed, upper immunity; one owning item | Intentional difference | BLOCK_MATERIALS/LIFECYCLE; owner2026-10-10; native lower loot | Existing regressions; native timing/tool/enchantment/drop checks pending |
| Machine, blasts/Creative break | Pair and trader teardown, native drops | One base loot route, no Creative refund; preserve blast1200 | Implemented/native | LIFECYCLE/VANILLA_PARITY; deferred blast settlement | Existing regressions; controlled door/machine blast comparison OPEN |
| Machine placement | Headroom/rejected placement/Creative | Reject before consumption; no extra item in Creative | Implemented/native hook | Core vm:machine beforeOnPlayerPlace on all15 definitions | placement suite passes; native ceiling/headroom/cancellation test pending |
| Machine placement | Upper-space obstruction, replacement, bounds, construction failure | Valid complete machine or owned cleanup and correct payment | Implemented/native hook + scoped cleanup | Bounded upper AABB query; failed spawn removes owned pair, Survival refund inventory then remainder | placement suite passes; native overlap/refund test pending; air-only/water policy retained |
| Machine use, upper half | Trade vs crouch attachment/reach/multiplayer | Preserve native placement handoff and standing-viewer priority | Intentional difference | INTERACTIONS and build_mode.js | Owner-tested crouch placement2026-10-05; other cases offline/native pending |
| Machine and Resources | Upgrade use/payment/Creative/repeat/failure | Exactly one Survival kit per first successful upgrade, none Creative | Implemented | Synchronous custom-item onUseOn; feedback isolated after payment | upgrades suite passes; native use/payment/retained progression pending |
| Trader/base/head | Upgrade display/progress persistence | Keep same actor and update only its matching intact pair | Implemented | Exact profession and half checks; unavailable/mismatched owners skipped, no deletion | matching/mismatched/missing/unloaded regressions pass; native reload pending |
| Trader profession tables | Trade tiers, XP, stock | Preserve five native progression tiers and all-offers machine policy; high stock | Intentional difference | Native economy component, singleton offer groups, max_uses9999999 | Prior trade evidence08-trading; XP/stock/reload/multiplayer engine checks pending |
| Wandering/cartographer Trader | Current offers/prices/maps and data functions | Current stable catalog with all-offers machine policy | Implemented | Current versioned sources;100 wandering candidates/six buybacks and ten map destinations; dimension restrictions retained | eight catalog tests pass; actual maps/metadata/native pricing pending |
| Librarian table generator | Repeated book generation | Same catalog after repeated invocation | Implemented | Replaces owned exact-book entries before adding current entries | repeated generation remains46 offers,36 books; catalog regression passes |
| All table variants | Pricing/discounts/demand | Retain established profession/custom shulker discounts; document extra-machine rule | Implemented documentation/policy | README corrected; basic wandering buybacks reduce payout while keeping native bucket/bottle quantities | catalog regressions pass; native demand/XP/reload behavior OPEN |
| Trader helper descriptions | Creative spawn eggs | Internal actors created by their machine scripts | Implemented | All15 is_spawnable:false; is_summonable retained; generators agree | catalog binding checks pass; native Creative menu pending |
| Trader actors | Biology, village POI, hostility, care, natural lifecycle | Stationary persistent exchange fixture, without living trader/shulker jobs | Inapplicable to fixture design | README, entity generator and role explanation in inspection | Recorded Group20 role disposition; native attackability/obstruction/caps still separate OPEN tests |
| Machine trade UI | Chest contents/hoppers/fullness/piglin opening | Exchange without stored stock | Inapplicable to exchange design | No inventory; trade economy and inspection role explanation | Recorded Group20 role disposition; item transport remains applicable |
| Machine and Resources as items | Hoppers/droppers, death, hazards, display/pick-block | Ordinary native item behavior and appropriate collection/stacking | Implemented/native, acceptance OPEN | Native item/block forms; no custom immunity/transport | Source; native transfer/full inventory/keepInventory/despawn/fire/lava/void/display checks pending |
| Machine environment | Waterlogging/flow/fire/pistons | Solid water-blocking, nonflammable, immovable fixture | Intentional difference | WATER/BLOCK_MATERIALS, liquid_detection, flammable:false, movable | Source/verify; states, underwater UI and slime/honey engine checks pending |
| Machine under note block | Iron material instrument | Native iron xylophone | Implemented/native | All15 definitions/generators/material policies use down:note.iron_xylophone | static/catalog checks pass; both-half/state sound test pending |
| Machine signals | Conduction/output/observer/sculk | Solid conductor; no invented trade-stock comparator | Implemented/native declaration; acceptance OPEN | redstone_conductivity:true; no inventory/producer | Source; native conduction/neighbor/state-event behavior pending |
| Machine geometry/environment | Collision/light/spawning/suffocation/grass/snow/rain/map/attachments | Solid fixture outcomes with explicit approved surfaces | Open | Full-block geometry, map_color and existing build-mode tests | No complete native comparison; retain exact OPEN cases |
| Machine/Trader | Command/clone/structure insertion/removal, orphan recovery | Explicit supported placement/cleanup policy | Open | Only player-place/break and explosion handlers; entityLoad migration | No new broad scanner; native multi-block alternative separately researched |
| Machine; Resources | Door opening/wind/hinges; beacon/golem body/iron unpacking; food/fuel/compost | Do not infer unrelated functions from paired shape, casing or resource name | Inapplicable | Aspect-specific counterparts and actual custom recipe consumers | Source/discovery; no new engine functionality proposed |

Inventory deduplicates identifiers across the four BPs, but lists every source
file. A policy resolves all variants only when definitions/scripts agree;
upgraded states, paired halves and multiplayer build-mode ownership are part
of the same review. Exact upper-only native door blast outcomes remain pending
in `VANILLA_PARITY.md`; an older Wiki archive does not resolve that ordering.

## Exact authored inventory

### Blocks (15)

| Identifier | Review group | Source |
| --- | --- | --- |
| `vm:machine_armorer` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_armorer.json) |
| `vm:machine_butcher` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_butcher.json) |
| `vm:machine_cartographer` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_cartographer.json) |
| `vm:machine_cleric` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_cleric.json) |
| `vm:machine_farmer` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_farmer.json) |
| `vm:machine_fisherman` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_fisherman.json) |
| `vm:machine_fletcher` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_fletcher.json) |
| `vm:machine_leather_worker` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_leather_worker.json) |
| `vm:machine_librarian` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_librarian.json) |
| `vm:machine_shepherd` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_shepherd.json) |
| `vm:machine_shulker` | Machine | [vending_shulker_bp](../vending_shulker_bp/blocks/machine_shulker.json) |
| `vm:machine_stone_mason` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_stone_mason.json) |
| `vm:machine_tool_smith` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_tool_smith.json) |
| `vm:machine_wandering_trader` | Machine | [vending_wandering_bp](../vending_wandering_bp/blocks/machine_wandering_trader.json) |
| `vm:machine_weapon_smith` | Machine | [vending_villagers_bp](../vending_villagers_bp/blocks/machine_weapon_smith.json) |

### Items (2)

| Identifier | Review group | Source |
| --- | --- | --- |
| `vm:shulker_core` | Upgrade resources | [vending_shulker_bp](../vending_shulker_bp/items/shulker_core.json) |
| `vm:upgrade_kit` | Upgrade resources | [vending_bp](../vending_bp/items/upgrade_kit.json) |

### Entities (15)

| Identifier | Review group | Source |
| --- | --- | --- |
| `vm:trader_armorer` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_armorer.json) |
| `vm:trader_butcher` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_butcher.json) |
| `vm:trader_cartographer` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_cartographer.json) |
| `vm:trader_cleric` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_cleric.json) |
| `vm:trader_farmer` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_farmer.json) |
| `vm:trader_fisherman` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_fisherman.json) |
| `vm:trader_fletcher` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_fletcher.json) |
| `vm:trader_leather_worker` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_leather_worker.json) |
| `vm:trader_librarian` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_librarian.json) |
| `vm:trader_shepherd` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_shepherd.json) |
| `vm:trader_shulker` | Trader | [vending_shulker_bp](../vending_shulker_bp/entities/trader_shulker.json) |
| `vm:trader_stone_mason` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_stone_mason.json) |
| `vm:trader_tool_smith` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_tool_smith.json) |
| `vm:trader_wandering_trader` | Trader | [vending_wandering_bp](../vending_wandering_bp/entities/trader_wandering_trader.json) |
| `vm:trader_weapon_smith` | Trader | [vending_villagers_bp](../vending_villagers_bp/entities/trader_weapon_smith.json) |

