# vending: tag/family audit

2026-10-13; target Bedrock 1.26.52 / Script API 2.8.0. Source revision `7f3deb1`.

Status: source inventory and official-documentation review; proposals have not been applied. No new engine tests. Pack files were left unchanged. A reasoned omission is a valid audit result.

Scope: 15 block definitions, 15 entity definitions, across every `*_bp` pack in this mod. Relevant explicit item tags were cross-checked for the block/item distinction.

## Recommendations and effects

Keep all 15 hidden trader entities without type families. `tools/gen_machine_entities.py` deliberately omits them to avoid mob aggro. This is an existing design choice, not proof that every possible family attracts attackers. Do not add `mob`, `villager`, `wandering_trader`, `shulker` or `monster` merely because of their trade tables/appearance. All 15 machine blocks already have pickaxe speed tags; preserve the protected upper-half mining override and existing collection policy.

## Complete block inventory

Tags below are declared in root components. `omitted` and `[]` both mean no declared tags; they are retained by design unless a proposal above says otherwise. The material profile records the existing mining/harvest policy; a tag is not a harvest gate.

| Block | Declared tags | Profile / decision |
| --- | --- | --- |
| [vm:machine_shulker](../vending_shulker_bp/blocks/machine_shulker.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_armorer](../vending_villagers_bp/blocks/machine_armorer.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_butcher](../vending_villagers_bp/blocks/machine_butcher.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_cartographer](../vending_villagers_bp/blocks/machine_cartographer.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_cleric](../vending_villagers_bp/blocks/machine_cleric.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_farmer](../vending_villagers_bp/blocks/machine_farmer.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_fisherman](../vending_villagers_bp/blocks/machine_fisherman.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_fletcher](../vending_villagers_bp/blocks/machine_fletcher.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_leather_worker](../vending_villagers_bp/blocks/machine_leather_worker.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_librarian](../vending_villagers_bp/blocks/machine_librarian.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_shepherd](../vending_villagers_bp/blocks/machine_shepherd.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_stone_mason](../vending_villagers_bp/blocks/machine_stone_mason.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_tool_smith](../vending_villagers_bp/blocks/machine_tool_smith.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_weapon_smith](../vending_villagers_bp/blocks/machine_weapon_smith.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |
| [vm:machine_wandering_trader](../vending_wandering_bp/blocks/machine_wandering_trader.json) | `minecraft:is_pickaxe_item_destructible` | `metal_machine`; retain |

Inspected all block permutations: 0 tag-component overrides. Other components still vary by state; no all-state engine behavior is claimed.

## Complete entity inventory

| Entity | Base families | Group overrides / decision |
| --- | --- | --- |
| [vm:trader_shulker](../vending_shulker_bp/entities/trader_shulker.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_armorer](../vending_villagers_bp/entities/trader_armorer.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_butcher](../vending_villagers_bp/entities/trader_butcher.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_cartographer](../vending_villagers_bp/entities/trader_cartographer.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_cleric](../vending_villagers_bp/entities/trader_cleric.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_farmer](../vending_villagers_bp/entities/trader_farmer.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_fisherman](../vending_villagers_bp/entities/trader_fisherman.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_fletcher](../vending_villagers_bp/entities/trader_fletcher.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_leather_worker](../vending_villagers_bp/entities/trader_leather_worker.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_librarian](../vending_villagers_bp/entities/trader_librarian.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_shepherd](../vending_villagers_bp/entities/trader_shepherd.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_stone_mason](../vending_villagers_bp/entities/trader_stone_mason.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_tool_smith](../vending_villagers_bp/entities/trader_tool_smith.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_weapon_smith](../vending_villagers_bp/entities/trader_weapon_smith.json) | omitted | Retain deliberate omission; stationary trade helper |
| [vm:trader_wandering_trader](../vending_wandering_bp/entities/trader_wandering_trader.json) | omitted | Retain deliberate omission; stationary trade helper |

## Related explicit item tags

These are item-component tags, not block tags. This is a cross-check, not a request to classify every inventory item.

| Item | Tags |
| --- | --- |
| None declared | Omission alone is not an error |

## Evidence and follow-up

- Shared decision rules and primary sources: [tags and families](../../../.claude/skills/bedrock-modding/references/14-tags.md).
- Cross-mod findings and verification status: [workspace audit](../../../docs/tag-audit-2026-10-13.md).
- Existing runtime quest/hostility/debug tags are separate from these families. No new runtime tags or cleanup mechanisms are proposed.
- If accepted, update any responsible generator, run `mods verify <mod>`, deploy and confirm `in sync`, then record relevant engine observations here.
