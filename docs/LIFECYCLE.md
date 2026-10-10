# Machine destruction

2026-10-10, Script API 2.8.0 / target Bedrock 1.26.52. Source audit and mocked
event regressions; not separately confirmed in game.

Both player breaks (including a Creative break of the upper half) and
`blockExplode` use the destroyed permutation's `vm:half` to find the base.
Explosion cleanup captures the old permutation and position, then defers through
`system.run` so a base can finish native blast destruction before survivor
cleanup considers a separate support-loss drop. It does not retain a live event
block handle. Player-break cleanup remains immediate.
Only the matching opposite half is removed. Replacements and neighbouring
machines are preserved; a new machine already placed at the destroyed cell
causes the stale event to be ignored. All same-profession traders at that
machine's stationary anchor are removed, rather than the first trader within
two blocks. Upgrade lookup uses the same precise anchor.

Only the base owns one native machine-item loot entry with `explosion_decay`;
the upper half has an explicit empty table. When just the upper half is lost,
its matching surviving base is removed with native `setblock ... air destroy`
to produce a support-loss drop. A directly exploded base keeps the native blast
context; a base removed because its head was lost uses support-loss context and
has no original explosion decay. No scripted item is spawned. If both halves
are already gone there is no support-loss command or extra refund. Creative
player destruction removes the pair without a support-loss drop. Both machine
generators preserve these routes. Blast resistance 1200 remains unchanged.
Commands that silently replace a machine are outside these event handlers.

Owner confirmed 2026-10-10: hand and every tool can collect a machine; there is
no required collection tool. The native loot entry remains unconditional.

Validation: `node tests/run.mjs` (30 passing tests), plus all four pack pairs
pass `.\mods.cmd verify vending` with zero errors/warnings.
The lifecycle suite covers either destroyed half, both explosion event orders,
repeat delivery, adjacent and stacked machines, replacements, and duplicate
orphan traders, Creative suppression, native destruction before settlement,
replacement during settlement, captured event position and all 15 block/table
routes. API source:
`reference/server-2.8.0.d.ts`, `BlockExplodeAfterEvent.explodedBlockPermutation`.
Native drop counts and strong-blast ordering still need in-game acceptance.

Native multi-blocks are now available for vertical format 1.26.40+, per the
[official multi-block guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/multi-blocks?view=minecraft-bedrock-stable).
Migrating existing `vm:half` machines would also change placement, item/state
representation, selection and destruction event semantics. That migration was
not needed for this fix and has not been implemented or tested.

The upper-only support-loss result is not established as a vanilla parity bug.
Sources, limits and the focused remaining comparison are in
[VANILLA_PARITY.md](VANILLA_PARITY.md).
