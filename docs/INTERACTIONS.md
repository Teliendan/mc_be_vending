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

Validation: 2026-10-05, Script API 2.8.0, local reference 1.26.52. Eleven Node
regression tests pass for ray geometry, occlusion, state transitions, multiplayer
priority, unload/reload cleanup, and all 15 block definitions. Shared verifier
passes every pack with zero errors/warnings. The texture comparison was reviewed
in software. Native placement and trading transitions still require an in-game
check; the tests do not simulate the engine's input handling or rendering.
