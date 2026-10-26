# Crouch placement against the head

Owner requested native block and torch placement against the entity-backed upper
block on 2026-10-05. Commit name:
`Allow crouch placement against vending heads and flatten lower panels`.

WORKAROUND: `scripts/build_mode.js` detects a player's view ray entering a trader's matching
upper block within six blocks, checking for intervening blocks. Once per tick,
crouching exposes a full native selection box using `vm:build_mode`. Creative flight
also accepts the held Sneak input even if `isSneaking` does not report crouch posture. Standing,
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

## Creative crouch-build follow-up, 2026-10-25

Owner reports crouch-placement succeeds in Survival but not Creative. Both the
selection controller and the immediate trader-interaction cancellation now use the
same `hasSneakIntent`: actual crouch posture OR raw Sneak button pressed. This covers
Creative descent input while preserving grounded and touch/toggle crouching after a
raw touch button releases. No game-mode restriction is imposed; placement and item
cost remain native. The input-state difference is a source diagnosis, not a reproduced
engine result. Retest Creative both on the ground and flying (also Sneak + Jump to
hold altitude), plus Survival and ordinary standing trade.

API 2.8.0 declares `InputInfo.getButtonState`; official [InputButton documentation](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/inputbutton?view=minecraft-bedrock-stable)
notes touch Sneak input may release after one tick. [Minecraft controls](https://www.minecraft.net/en-us/article/minecraft-controls)
uses Sneak for flying downward in Creative. No matching 26.50/26.52 changelog fix was
identified in this review. Offline regressions cover raw-input and posture paths,
release restoration and the trader-interaction transition; engine retest is pending.
