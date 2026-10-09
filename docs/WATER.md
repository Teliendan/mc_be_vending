# Water decisions

2026-10-09, Bedrock 1.26.52. All machines are solid blocks: survive, block water,
and do not waterlog, like solid workstation blocks. Both machine halves inherit the
same explicit native `minecraft:liquid_detection` rule; upgraded/build-mode states
do not override it. The block generator declares the policy and extra machines clone it.

This applies to every `vm:` block:

- `machine_armorer`, `machine_butcher`, `machine_cartographer`, `machine_cleric`
- `machine_farmer`, `machine_fisherman`, `machine_fletcher`, `machine_leather_worker`
- `machine_librarian`, `machine_shepherd`, `machine_stone_mason`, `machine_tool_smith`
- `machine_weapon_smith`, `machine_shulker`, `machine_wandering_trader`

Static verification covers all four BPs. Pending in game: water exclusion for both
halves, upgraded states and crouching build mode, plus underwater trading interaction.
No script behavior was changed.
