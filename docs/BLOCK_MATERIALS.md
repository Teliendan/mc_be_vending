# Block materials

2026-10-09, target Bedrock 1.26.52. Each block-owning BP records its policies in
`block_materials.json`. Machines use the iron-block material comparison and
native pickaxe effectiveness. Existing protection deliberately overrides vanilla
5/6 with mining 8 / blast resistance 1200; upper-half mining remains false.
All explicitly nonflammable. Reasons and exact upper-half conditions are
recorded so the verifier checks exceptions without permitting unexplained drift.

Owner confirmed 2026-10-10: machines collect with any tool or hand; no required
collection tool. Native pickaxe speed remains independent of that choice.
In-game tool timing and TNT/trader cleanup
still need acceptance. Resistance 1200 is not unconditional explosion immunity.
Standard: `C:/mcmods/.claude/skills/bedrock-blocks/references/materials.md`.

Remaining-property batch, 2026-10-10 / target 1.26.52: all 15 machine RP sounds
now match current native iron block (`iron`, not the obsolete `metal` group or
previous stone). Source: installed `vanilla_1.21.60/blocks.json`, overriding the
older base vanilla entry. Both RP generators retain iron sounds; each owning
BP material policy records an enforceable `RP:sound` counterpart check. The
core BP contains no blocks/policy; all three block-owning variants share this RP.
Protection, paired-half lifecycle and immovability retain their existing rules.
Static checks pass; actual break/step/place sounds and trader cleanup still need
game acceptance after reload. No new owner question arose for these matches.
