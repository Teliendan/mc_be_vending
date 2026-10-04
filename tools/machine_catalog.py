"""Owner's signature goods: recipe ingredient, vanilla icon, and workstation.

Approved 2026-10-05. These describe the machine, not its full trade table.
"""
VILLAGER_MACHINES = {
    # profession: (item ID without namespace, texture folder, sprite, workstation)
    "armorer": ("iron_chestplate", "items", "iron_chestplate", "blast_furnace"),
    "butcher": ("cooked_porkchop", "items", "porkchop_cooked", "smoker"),
    "cartographer": ("empty_map", "items", "map_empty", "cartography_table"),
    "cleric": ("ender_pearl", "items", "ender_pearl", "brewing_stand"),
    "farmer": ("bread", "items", "bread", "composter"),
    "fisherman": ("fishing_rod", "items", "fishing_rod_uncast", "barrel"),
    "fletcher": ("arrow", "items", "arrow", "fletching_table"),
    "leather_worker": ("leather_chestplate", "items", "leather_chestplate", "cauldron"),
    "librarian": ("book", "items", "book_normal", "lectern"),
    "shepherd": ("white_wool", "blocks", "wool_colored_white", "loom"),
    "stone_mason": ("brick", "items", "brick", "stonecutter_block"),
    "tool_smith": ("iron_pickaxe", "items", "iron_pickaxe", "smithing_table"),
    "weapon_smith": ("iron_sword", "items", "iron_sword", "grindstone"),
}

# Source armour texture is greyscale. Bake a brown leather tint into its display.
DISPLAY_TINTS = {"leather_chestplate": (160, 101, 64)}
