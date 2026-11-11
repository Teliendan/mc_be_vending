# Localization

Workflow and checks: workspace `docs/localization.md`.

2026-10-04; target Bedrock 1.26.52 / Script API 2.8.0.
Commit: `Localize vending with contextual catalogs and nine locales`.

Owner approved (2026-10-04) English, Czech, Spanish Spain/Mexico, Portuguese Portugal/Brazil, German, French and Polish, with context and localization required during future development. Catalogs are mod-scoped (`localization/catalog.json`); en_GB=en_US and fr_CA=fr_FR are compatibility aliases.

Review status: eight target locales are AI-authored contextual drafts (`ai-draft`). No native-language review or game testing of this localization pass is claimed.

Vanilla terminology: Mojang bedrock-samples commit `46ba6ea985fb5a92d79a9419198f10dda14c199d`, documented not verified in game. Shared terms: workspace `docs/localization-terminology.json`.

## Mod-specific rules

All core and optional feature-pack descriptions are included. Block and hidden trader names match. Profession terms use Mojang Bedrock labels. Upgrade Kit means discounted prices, not villager tier progression. Generators preserve catalog wording.

2026-10-04 RawMessage repair (target 1.26.52 / API 2.8.0): omit `with` for translations without arguments. The same helper pattern caused Torchlight's owner-reported `RawMessageError`; see workspace `docs/localization.md`. Offline payload regressions cover this case; in-game confirmation of the corrected helper is pending. Commit: `Omit empty translation arguments in vending messages`.
