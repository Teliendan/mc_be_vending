# Block materials

2026-10-09, target Bedrock 1.26.52. Each block-owning BP records its policies in
`block_materials.json`. Machines use the iron-block material comparison and
native pickaxe effectiveness. Existing protection deliberately overrides vanilla
5/6 with mining 8 / blast resistance 1200; upper-half mining remains false.
All explicitly nonflammable. Reasons and exact upper-half conditions are
recorded so the verifier checks exceptions without permitting unexplained drift.

Existing paired block/trader removal and drop logic remain; pickaxe speed does
not add a new harvest restriction. In-game tool timing and TNT/trader cleanup
still need acceptance. Resistance 1200 is not unconditional explosion immunity.
Standard: `C:/mcmods/.claude/skills/bedrock-blocks/references/materials.md`.
