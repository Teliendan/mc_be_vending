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
  Existing centre-crop/placement remains; icons larger than the window are cropped
  without scaling. Leather's greyscale source gets a baked brown tint (160,101,64)
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
