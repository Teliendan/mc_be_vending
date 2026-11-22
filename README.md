# Vending Machines for Minecraft Bedrock

Craftable machines that trade like villagers and the wandering trader, or sell shulker boxes and mob loot. No trading hall needed. Place one and trade with it like with a villager; its stock never runs out.

> **Status: Test version.** Things may still change before the public release, so back up any world you care about. Download: [Releases page](https://github.com/Teliendan/mc_be_vending/releases).

**Project page:** [teliendan.com](https://teliendan.com/mods/vending/?utm_source=github&utm_medium=referral&utm_campaign=profile&utm_content=readme) · **Wiki:** [every machine, recipe and trade](https://teliendan.com/wiki/vending/?utm_source=github&utm_medium=referral&utm_campaign=profile&utm_content=readme)

## Features

- **Villager machines:** one for each profession: Armorer, Butcher, Cartographer, Cleric, Farmer, Fisherman, Fletcher, Leather Worker, Librarian, Shepherd, Stone Mason, Tool Smith and Weapon Smith. They charge vanilla prices and keep vanilla's five trade levels. Every trade a villager of that profession can offer is there, with unlimited stock. The Librarian sells one book at the highest level of each enchantment that is not a curse.
- **Wandering Trader machine:** keeps every wandering trader offer available all the time, so you no longer wait for him to show up. It charges more than vanilla until you upgrade it.
- **Shulker machine:** sells shulker shells and shulker boxes. There is no shortcut to it: its Shulker Core is crafted from nine shulker shells, so you need to fight shulkers first.
- **Loot machines:** four of them (Overworld, Nether, Trial and End) sell mob loot such as bone, blaze rods and nether stars. They are made for Peaceful worlds, where those mobs never appear, and also save you from farming mobs. Anyone can craft and use them on any difficulty.
- **Upgrade Kit:** use one on the lower block of a machine to cut its prices by 30%. A machine that is already upgraded says so and keeps your kit untouched. Craft it from two blaze powder, two gold ingots, a golden apple, two emeralds and a fermented spider eye.
- **Crafting:** each machine takes three emerald blocks, two iron blocks, two gold blocks and two items of its own; a villager machine uses its profession's workstation and the good it shows in its window.
- **Building around it:** a machine is two blocks tall. Crouch and aim at the upper block to place blocks or attach torches to it; stand up to trade. In Survival, any tool or your hand breaks it and gives the machine back.
- **Pick your packs:** Core plus one small pack per machine family (Villagers, Wandering Trader, Shulker, Loot). Turn on only the ones you want.
- **Languages:** English, Czech, German, French, Polish, Spanish (Spain and Mexico) and Portuguese (Portugal and Brazil). The translations are AI drafts; corrections are welcome.

## Install

1. Download the `.mcaddon` from the [Releases page](https://github.com/Teliendan/mc_be_vending/releases).
2. Open the file with Minecraft on Windows, Android or iPhone/iPad; it imports all the packs.
3. In the world's Behavior Packs settings, turn on **Vending Machines — Core** plus the machine packs you want. Turning on Core also turns on the resource pack. Each machine pack needs Core, but none needs another.

Xbox, PlayStation and Switch can't import add-on files directly, but console players can join a world that already has them.

Requirements: tested on Minecraft Bedrock 1.26.63. No experimental toggles are needed. It works on its own and needs none of my other add-ons.

## Known issues

- A machine needs empty air above it. Unlike a door, it cannot be placed where the upper block holds grass or a snow layer.
- Machines trade directly: they have no storage and do not work with hoppers.
- Leather armour is sold undyed.
- If you crouch and click the upper block at once, the click may need repeating.

## Feedback

Found a bug or have an idea? Tell me through the [report form](https://teliendan.com/contact/?project=vending&utm_source=github&utm_medium=referral&utm_campaign=profile&utm_content=readme#report).

## Credits

Made by [Teliendan](https://teliendan.com/?utm_source=github&utm_medium=referral&utm_campaign=profile&utm_content=readme).

- Code written with AI coding agents, directed and tested by Teliendan.
- The machine textures are drawn by scripts written for this mod. The goods in each display window are Minecraft's own item sprites.
- Trades are generated from Minecraft's own villager and wandering trader trade data.

## Disclaimer

Unofficial add-on for Minecraft. Not affiliated with or endorsed by Mojang Studios or Microsoft. "Minecraft" is a trademark of Mojang Studios / Microsoft. Anything derived from vanilla Minecraft files remains Mojang's.

## Licence

See [LICENSE.md](LICENSE.md).

## For developers

Pack layout, generators, tests and design notes: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## What's new

See [CHANGELOG.md](CHANGELOG.md) and the [Releases page](https://github.com/Teliendan/mc_be_vending/releases).
