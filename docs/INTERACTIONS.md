# Crouch placement against the head

Owner requested native block and torch placement against the entity-backed upper
block on 2026-10-05. Commit name:
`Allow crouch placement against vending heads and flatten lower panels`.

WORKAROUND: `scripts/build_mode.js` detects a player's view ray entering a trader's matching
upper block within six blocks, checking for intervening blocks. Once per tick,
crouching exposes a full native selection box using `vm:build_mode`. Standing,
looking away or disconnecting restores the hidden selection box for trading.
Loaded traders reset saved temporary state; unloaded resets are retried.
The upper block remains unmineable and retains full collision in both modes.
Both standard and upgraded machines, including wandering/shulker, share this rule.

Minecraft handles placement, attachment faces, orientation and item consumption.
The script cancels crouching trader interactions during the brief transition;
an immediate click can therefore need repeating after the head becomes selectable.
There is no scripted block placement or manual item consumption.

Selection state is shared. A standing player aiming at the same head takes
priority over a crouching builder so the standing player can still trade.

Owner confirmed crouch placement in game on 2026-10-05 (commit `d3c2dbb`). Multiplayer
priority and unload/reload cleanup are covered by `tests/build_mode.test.mjs` only.
