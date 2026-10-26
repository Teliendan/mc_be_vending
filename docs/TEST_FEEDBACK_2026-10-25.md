# Owner test feedback, 2026-10-25

Source: workspace `temp/testing_feedback.md`, checklist `docs/game-checks.md`.
Target: Bedrock 1.26.52 / Script API 2.8.0.

| Item | Owner result | Disposition |
| --- | --- | --- |
| Adjacent/diagonal placement | Cannot place machines close together | Fixed in source: invisible `vm:trader_` helpers are ignored by the upper-cell actor check. Their solid owning machine blocks already enforce occupancy. In-game retest pending. |
| Creative crouch-building follow-up | Works in Survival, fails in Creative | Candidate fix implemented: shared posture-or-Sneak-input handling controls both head selection and immediate trading cancellation. Ground/flying Creative engine retest pending. |
| V1 placement cancellation | OK | Owner pass recorded; real-mob blocking retained and regression tested. |
| V2 upgrades | OK | Owner pass recorded; no upgrade changes. |
| V3 new offers | OK except only two candle colours noted; other professions not all checked | Resolved/no defect for candles: current native librarian sells only red and yellow candles. Owner follow-up reports the remaining checks OK; no separate new-offer check remains open. |
| V4 note block/orphan cleanup | OK | Owner pass recorded; no change. |
| V5 TNT cannot destroy machines | Acceptable | Accepted owner behavior; keep existing blast resistance 1200. |

## Candle catalogue evidence

The installed newest librarian source is
`reference/vanilla/current/behavior_packs/vanilla_1.26.10/trading/economy_trades/librarian_trades.json`.
Master offers are red candle repeated three times as weighting, and yellow candle once.
The native master tier has one group with `num_to_select: 1`, so a villager selects
one fixed-colour offer: red with 3/4 weighting, yellow with 1/4 weighting. It does
not roll two random colours from all sixteen. The fixed machine catalogue deliberately
emits each unique offer once, so it sells both red and yellow; each gives one candle.
The generator/catalogue suite checks all 30 shipped tables against their current native
sources, choice expansion, colour variants and book rules. No catalogue changes are needed.
The [Minecraft Wiki Librarian page](https://minecraft.wiki/w/Librarian) and
[Trading table](https://minecraft.wiki/w/Trading) corroborate the two-colour catalogue
(reviewed 2026-10-25; native source is the primary evidence).

## Validation

`mods verify vending --suite placement --suite catalogs` passed: all four behavior
packs, 0 errors/warnings. Placement regressions cover adjacent/diagonal helper results
and a helper plus a real obstruction. Engine placement acceptance still requires retest.
Parent agent owns final commit, wiki export and deployment status.

Follow-up validation: `mods verify vending --suite build-mode --suite placement --suite upgrades --suite lifecycle` passed all four BPs with 0 errors/warnings. Source review found no explicit game-mode gate on crouch building; raw Sneak input now complements posture rather than assuming a confirmed Creative-only engine cause.

## Read-only cross-mod scope review

The new report establishes a vending Creative placement problem. Source review of
Starstone and Torchlight found no crouch-placement mode gate: Starstone generator
interaction is a native custom-component callback; its Creative checks concern
harvest, tool wear and XP. Torchlight has no script crouch/use routing. Lothlorien
wood controls use native custom `onPlayerInteract` callbacks with no explicit
Creative-only rejection. Their callback/engine routing has not been reproduced in
Creative, so this pass makes no speculative cross-mod changes or claims of engine
parity. Lothlorien rope/cloak `isSneaking` checks implement posture mechanics rather
than place-vs-interact bypass. Parent agent coordinates any later cross-mod action.
