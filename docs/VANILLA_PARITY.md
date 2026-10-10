# Paired machine loot and vanilla comparison

2026-10-10, target Bedrock 1.26.52 / Script API 2.8.0. Source/documentation
review and mocked regressions only; no new engine test or deploy by this agent.

Owner confirmed machines need **no required collection tool**. Hand and any
tool retain the existing unconditional one-item base loot. Pickaxe efficiency,
mining 8, blast resistance 1200, upper mining immunity and approved iron sounds
remain. This is an explicit machine design choice rather than a pending question.

## Closest vanilla behavior and evidence

Iron block remains the material/sound comparison; a two-block door is the closer
comparison for paired item ownership and teardown. These are separate aspects.
The installed vanilla reference contains door recipes and assets, but no
inspectable native door loot/destruction implementation. Do not infer Bedrock
engine blast ordering from Java door source or another server implementation.

[Bedrock 1.21.20](https://feedback.minecraft.net/hc/en-us/articles/29110275666957-Minecraft-1-21-20-Bedrock)
fixed Creative breaks of a door's upper block dropping an item. Our Creative
cleanup deliberately emits no support-loss refund, matching that current rule.
[Bedrock 1.21.50](https://www.minecraft.net/en-us/article/minecraft-1-21-50-bedrock-changelog)
made iron/copper doors collectible with any tool and explains their connection
to support-loss drops. Older references requiring pickaxes for those doors are
obsolete. This supports keeping tool effectiveness separate from collection.

The current Minecraft Wiki Door article could not be inspected this time:
the web reader returned an error, and ordinary HTTPS returned 403 even with a
browser user-agent. The searchable older Fandom Door article describes upper
halves with no item and lower halves owning the door, but does not establish
current Bedrock upper-only explosion decay. It is a lead, not proof of an exact
blast probability or ordering. No claim of current wiki revision/game testing
is made. The 26.50/26.52 official release notes inspected here supply no new
door blast-loot rule resolving that detail.

Conclusion: **the lack of original explosion context on a surviving base's
support-loss drop is not a demonstrated vanilla discrepancy**. A base already
destroyed by the blast uses its own native loot context; a base surviving the
blast but losing its paired upper block is removed separately. There is no
supported evidence to apply invented extra decay to the latter or to refund a
second item for the empty upper half. Exact vanilla upper-only blast behavior
remains an engine comparison, not a new owner design question.

## Implemented timing correction

Per-block destruction must not eagerly turn a still-present base into a
support-loss drop before native processing has had a chance to destroy it with
the original blast. The prior handler performed this work synchronously inside
the upper blockExplode callback. The API does not promise a relative processing
order for different impacted block callbacks, so relying on that order is
unnecessary. This is a defensive correction to a concrete ordering dependency,
not a claim that a duplicate or altered decay was reproduced in game.

The handler now captures old permutation, dimension and position immediately,
then schedules live-state cleanup through `system.run`. This follows the
[official scheduling guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/scripting/system-run-guide?view=minecraft-bedrock-stable).
It promises deferred work, not an exact wall-clock delay. If native processing
has removed both halves, no destroy command/refund runs. If only the upper is
gone, the matching still-live base is removed natively with support-loss context.
Replacement/neighbor guards and once-only trader removal still apply. The block
handle itself is not accessed after the event callback. No scripted random
decay, unsupported loot parameter, new tool predicate or native multi-block
migration was introduced.

`node tests/run.mjs`: **30 passing tests**. Four new regressions cover both
native half-processing orders before settlement, upper-only survivor removal
once, replacement before settlement and expired event block handles. The
existing suite asserts unconditional loot for all 15 machines, Creative no-drop,
both already-gone blast event orders, repeated delivery and adjacent traders.
These tests validate our ordering/ownership logic, not native drop probabilities.

## Remaining engine comparison

Compare an iron or wooden door with a machine under direct lower-only,
upper-only and both-part destruction, separately with TNT decay false, TNT decay
true and a mob explosion. Record direct-blast items separately from a surviving
partner's support-loss item. Ordinary TNT will normally leave resistance-1200
machines intact; use a controlled sufficiently powerful explosion for machine
teardown, with a separately comparable native-door scenario. Do not lower the
approved machine resistance merely to make this test convenient. Creative upper
breaks should yield no item, and Survival hand/pickaxe/other-tool base collection
should each yield one. Native multi-block migration and silent command orphan
recovery remain separate work, outside this parity correction.
