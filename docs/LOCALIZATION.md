# Localization

2026-10-04; target Bedrock 1.26.52 / Script API 2.8.0.
Commit: `Localize vending with contextual catalogs and nine locales`.

Owner approved English, Czech, Spanish Spain/Mexico, Portuguese Portugal/Brazil, German, French and Polish, with context and localization required during future development. Catalogs are mod-scoped.

Source of truth: `localization/catalog.json` (45 entries across all packs). It includes meaning, UI location, trigger, tone, grammar, constraints, typed argument meanings, locale wording, freshness and review status. English is the source; eight target locales are AI-authored contextual drafts. No native-language review or game testing of this localization pass is claimed. Explicit compatibility aliases en_GB=en_US and fr_CA=fr_FR are generated.

All core and optional feature-pack descriptions are included. Block and hidden trader names match. Profession terms use Mojang Bedrock labels. Upgrade Kit means discounted prices, not villager tier progression. Generators preserve catalog wording.

Workflow for every future change: read the workspace `docs/localization.md`, add complete context and all locale wording in this mod's catalog, calculate fingerprints only after reviewing changed wording, run `.\mods localize build vending`, `.\mods verify vending`, then `.\mods deploy vending` and confirm in-sync status. Do not edit generated language files. Changing source/context/arguments/glossary invalidates target translations. Console logging and unshipped tools/dev_scripts stay developer English.

Offline verification: shared add-on verifier, project regression tests where configured, ten localization workflow tests and actual message-helper checks across all nine locales. Final deployment status is checked with the workspace tool. No mechanics/worldgen changes were intended; existing worlds can reload the packs by leaving and re-entering.

Remaining in-game review: pack descriptions/settings, inventory/block/entity names, interaction prompts, chat/action bars, mixed-language multiplayer, language switching and new item lore where applicable. Target review states remain `ai-draft`; use named-reviewer evidence before marking `language-reviewed`, and version/date/test evidence for `game-tested`.

Vanilla terminology: Mojang bedrock-samples commit `46ba6ea985fb5a92d79a9419198f10dda14c199d`, documented not verified in game. Shared selected terms: workspace `docs/localization-terminology.json`.
