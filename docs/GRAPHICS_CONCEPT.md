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
  crown light and three-pixel upgrade corner markers retained. Lower panels are
  flush following the owner's final request to remove the simulated recesses.
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

2026-10-05, local vanilla reference 1.26.52: owner accepted the final graphics and
confirmed the deployed crouch-placement feature works in game. All recipe
signatures and plain map/arrow variants were checked offline. Generation asserts
a full 14x14 display opening and preservation of opaque product pixels. All 15
goods and both machine tiers were reviewed in software; shared verification
passed every pack with zero errors/warnings. Recipes and performance have no
separate in-game test record. Iteration scratch is removed; git retains history.

The owner requested the entire display width to remain live and every item to be
centred as well as the pixel grid allows. `display_position()` balances bounds
(weight 1) and alpha-weighted silhouette (weight 0.5); equal scores favour
right/down. The owner also requested removing the lower block's inner right
shadow strip and both broad horizontal recesses. Those areas now continue the
steel panel, preserving the outer frame, gold rails and emerald controls.

| Commit | Final decision |
|---|---|
| `cdda0b3` Finalize vending graphics and signature ingredients | Accepted manual shading, vanilla goods and matching recipes |
| `55f3a3a` Restore full-width vending item displays | Full 14-column display opening |
| `827dfb7` Balance vending goods within display windows | Centre every fitted item |
| `d3c2dbb` Allow crouch placement against vending heads and flatten lower panels | Native crouch placement; remove lower simulated recesses |

## Pack icon

2026-10-07: owner requested distinct machines for the feature packs and a shared
group photo for Core and Resources. `tools/make_pack_icon.py` generates 256x256 icons directly
from the accepted textures, using integer pixel projections:

| Pack | Icon | Background |
|---|---|---|
| Core | Librarian in front, Wandering Trader and Shulker behind | Green |
| Resources | Same group photo as Core | Green |
| Villagers | Librarian machine | Green |
| Wandering Trader | Wandering Trader machine | Blue |
| Shulker | Shulker machine | Purple |

Single-machine icons retain the vanilla emerald beside the machine. Group
members are projected at their own integer sizes without resampling textures.
The generator checks opaque 16x16 faces, unclipped machine bounds, matching
Core/Resources pixels and three distinct feature icons. `--review PATH` creates a labelled sheet at
256, 64 and 32 pixels; `--preview PATH --pack PACK` writes a single preview
without changing pack files, with an optional `--head` override.

Reviewed all three sizes offline; shared verification passed all packs with
zero errors/warnings. Deployed for local vanilla reference 1.26.52; the updated
icons have not yet been checked in Minecraft or accepted by the owner. Review
scratch remains in `temp/vending-pack-icon/` until acceptance. Implementation commit: `Give vending packs distinct machine icons`.
