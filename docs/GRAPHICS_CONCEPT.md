# Final vending graphics

Owner accepted the current-layout graphical-manual pass on 2026-10-05 and
approved the following display goods and matching crafting ingredients.
Commit name: `Finalize vending graphics and signature ingredients`.

| Machine | Display and recipe signature ingredient |
|---|---|
| Armorer | Iron Chestplate |
| Butcher | Cooked Porkchop |
| Cartographer | Empty Map (plain, aux 0) |
| Cleric | Ender Pearl |
| Farmer | Bread |
| Fisherman | Fishing Rod |
| Fletcher | Arrow (plain, aux 0) |
| Leatherworker | Leather Tunic |
| Librarian | Book |
| Shepherd | White Wool (chosen for the unspecified wool colour) |
| Stone Mason | Brick |
| Toolsmith | Iron Pickaxe |
| Weaponsmith | Iron Sword |

## Final design and generation

- Existing two full blocks, 16x16 textures, display window, control buttons,
  collection tray, crown light and three-pixel upgrade corner markers retained.
- Cool steel hue-shifted ramps, coherent plate facets and brushed highlights;
  warm gold shadows and pale glints; faceted emerald buttons; shaded display
  recesses. Top-left lighting, no random noise, no texture resampling.
- Display goods use the vanilla item sprite (white wool uses the block texture).
  Icons larger than the window are centre-cropped without scaling. Fitted sprites
  use whole-pixel positions balancing their bounds and alpha-weighted silhouette;
  half-texel ties go right/down. Leather's greyscale source gets a baked brown tint (160,101,64)
  to show leather rather than an iron-looking tunic. Exact in-game tint matching
  has not been separately verified.
- `tools/machine_catalog.py` defines each profession's recipe item, sprite and
  workstation. `make_machine_textures.py` generates standard textures;
  `vm_make_upgraded_textures.py` applies the existing marker shape using the same
  ramps. Only the accepted style is generated.
- The shaped recipe remains `GTG / IWI / EEE`: two gold blocks, two iron blocks,
  three emerald blocks, the profession workstation and its listed signature
  ingredient. Workstation unlocks remain. Display choices do not change trade tables.
- Wandering Trader and Shulker retain their goods/recipes and share the new surfaces.

## Validation

2026-10-05, local vanilla reference 1.26.52: software-reviewed final 13-machine
standard/upgraded sheet. One-time checks passed for all recipe signatures,
plain map/arrow variants, and every visible opaque item texel against the source
sprite (after the deliberate leather tint). Shared body/top textures match the
accepted comparison pixel-for-pixel. Shared verifier passed every pack with zero
errors and warnings. Rendering/performance and recipes await the owner's in-game
check. Iteration drafts are cleaned up after acceptance; git holds final history.

2026-10-05 follow-up: owner observed the second-from-right display column hiding
item pixels. The head mask reused the body panel's two-column right edge, leaving
only 13 product columns despite centring goods in a 14-column window. Head rows
now use one frame column on each side, exposing interior column 14. Generation
asserts a full 14x14 opening and that every opaque displayed product texel survives
frame painting. Commit name: `Restore full-width vending item displays`.
All 30 before/after head textures compared: the 162 changed pixels are confined
to interior column 14, rows 1-14. Enlarged armorer/book/wool comparisons reviewed.
Shared verification passed with zero errors/warnings; deployed and in sync.
Corrected rendering awaits in-game confirmation.

2026-10-05 centring: reviewed every display after the owner's arrow/pearl feedback.
The former floor division biased odd-sized sprites top-left. `display_position()`
now searches the positions that keep the fitted sprite fully inside the window,
balancing its bounds and alpha-weighted silhouette (bounds weight 1, mass 0.5).
Equal scores favour right/down; no scaling or new clipping is introduced.
Armorer, Fletcher, Leatherworker, Toolsmith, Wandering Trader and Shulker move
down one texel; Cleric moves right and down one. The other eight positions are
already optimal within these constraints. Before/after 1x/2x and enlarged sheets
reviewed; all 15 fitted sprites preserve their opaque pixels, and all 30 outer
frames and upgrade markers remain unchanged. Shared verifier: zero errors and
warnings. Software-reviewed with reference 1.26.52; awaits in-game confirmation.
Commit name: `Balance vending goods within display windows`.
