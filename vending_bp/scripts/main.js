import { world, system, ItemStack, BlockPermutation } from "@minecraft/server";

// ---------------------------------------------------------------------------
// Vending machine: block + hidden trader
//
// A machine is one custom block occupying two positions -- vm:half 0 (solid,
// selectable, breakable) and vm:half 1 (solid, but selection_box:false so the
// crosshair passes through it) -- with an invisible vm:trader_<prof> entity
// standing inside the upper half. The entity owns the trade table; the block
// owns collision, placement and breaking.
//
// Progression is ENGINE-owned. The trader levels itself from the five tiers in
// its trade table, exactly like a villager. Script never reads or writes a
// tier -- it cannot, and it no longer needs to.
// ---------------------------------------------------------------------------

const BLOCK_PREFIX = "vm:machine_";
const TRADER_PREFIX = "vm:trader_";

function professionOf(blockTypeId) {
    return blockTypeId.substring(BLOCK_PREFIX.length);
}

// The trader stands at the centre of the UPPER half.
function traderSpot(baseBlock) {
    const l = baseBlock.location;
    return { x: l.x + 0.5, y: l.y + 1, z: l.z + 0.5 };
}

// The trader is hidden by an empty model, but the engine still draws a mob's
// ground shadow under it. Invisibility is the one thing that removes that
// shadow; it does not affect trading. The effect is re-applied every time the
// entity loads, so it never runs out on an old machine.
const INVISIBLE_TICKS = 20000000;

function hideShadow(trader) {
    trader.addEffect("invisibility", INVISIBLE_TICKS, { showParticles: false });
}

world.afterEvents.entityLoad.subscribe((e) => {
    const entity = e.entity;
    if (!entity.isValid || !entity.typeId.startsWith(TRADER_PREFIX)) return;
    hideShadow(entity);
    // Machines upgraded before the block had a vm:upgraded state catch up here.
    if (entity.getDynamicProperty("vm:upgraded") === true) {
        const l = entity.location;
        const base = entity.dimension.getBlock({ x: Math.floor(l.x), y: Math.floor(l.y) - 1, z: Math.floor(l.z) });
        if (base && base.typeId.startsWith(BLOCK_PREFIX)) showUpgraded(base);
    }
});

// The upgraded look (gold + emerald corners) is a block state on both halves.
// It is only ever set, never cleared: breaking the machine removes it anyway.
function showUpgraded(baseBlock) {
    for (const block of [baseBlock, baseBlock.above()]) {
        if (!block || block.typeId !== baseBlock.typeId) continue;
        if (block.permutation.getState("vm:upgraded") === true) continue;
        block.setPermutation(block.permutation.withState("vm:upgraded", true));
    }
}

// One-off burst of green villager sparkles over the whole machine.
function sparkle(baseBlock) {
    const l = baseBlock.location;
    for (let i = 0; i < 24; i++) {
        const spot = { x: l.x + Math.random(), y: l.y + Math.random() * 2.2, z: l.z + Math.random() };
        baseBlock.dimension.spawnParticle("minecraft:villager_happy", spot);
    }
}

function findTrader(dimension, baseBlock, profession) {
    const found = dimension.getEntities({
        type: TRADER_PREFIX + profession,
        location: traderSpot(baseBlock),
        maxDistance: 2,
    });
    return found.length > 0 ? found[0] : undefined;
}

// --- placement: raise the upper half and spawn the trader ------------------
world.afterEvents.playerPlaceBlock.subscribe((e) => {
    const block = e.block;
    if (!block.typeId.startsWith(BLOCK_PREFIX)) return;
    if (block.permutation.getState("vm:half") !== 0) return;

    const above = block.above();
    if (!above || !above.isAir) {
        // No headroom. Give the machine back rather than leaving half of one.
        const typeId = block.typeId;
        block.setType("minecraft:air");
        block.dimension.spawnItem(new ItemStack(typeId, 1), traderSpot(block));
        e.player.sendMessage("\u00a7cA vending machine needs two blocks of space.");
        return;
    }

    above.setPermutation(BlockPermutation.resolve(block.typeId, { "vm:half": 1 }));
    const trader = block.dimension.spawnEntity(TRADER_PREFIX + professionOf(block.typeId), traderSpot(block));
    hideShadow(trader);
});

// --- breaking: only the lower half is breakable, so this is the teardown ----
world.afterEvents.playerBreakBlock.subscribe((e) => {
    const typeId = e.brokenBlockPermutation.type.id;
    if (!typeId.startsWith(BLOCK_PREFIX)) return;

    const above = e.block.above();
    if (above && above.typeId === typeId) {
        above.setType("minecraft:air");
    }
    const trader = findTrader(e.dimension, e.block, professionOf(typeId));
    if (trader) trader.remove();
});

// --- the Upgrade Kit: right-click the base with it -------------------------
//
// One kit per machine. The flag lives on the trader as a dynamic property, so
// it travels with the thing it describes and dies with it.
system.beforeEvents.startup.subscribe((init) => {
    init.itemComponentRegistry.registerCustomComponent("vm:upgrade_kit", {
        onUseOn(event) {
            const block = event.block;
            const player = event.source;
            if (!block || !block.typeId.startsWith(BLOCK_PREFIX)) return;
            if (block.permutation.getState("vm:half") !== 0) return;

            system.run(() => {
                const profession = professionOf(block.typeId);
                const trader = findTrader(block.dimension, block, profession);
                if (!trader || !trader.isValid) return;

                if (trader.getDynamicProperty("vm:upgraded") === true) {
                    showUpgraded(block);
                    player.sendMessage("\u00a7eThis machine is already upgraded.");
                    return;
                }

                trader.triggerEvent("vm:apply_upgrade");
                trader.setDynamicProperty("vm:upgraded", true);
                showUpgraded(block);
                sparkle(block);
                block.dimension.playSound("random.anvil_use", traderSpot(block), { volume: 0.8, pitch: 1.2 });
                player.sendMessage("\u00a7aUpgraded \u2014 this machine now trades at a discount.");

                const equippable = player.getComponent("minecraft:equippable");
                const held = equippable ? equippable.getEquipment("Mainhand") : undefined;
                if (held && held.typeId === "vm:upgrade_kit") {
                    if (held.amount > 1) {
                        held.amount -= 1;
                        equippable.setEquipment("Mainhand", held);
                    } else {
                        equippable.setEquipment("Mainhand", undefined);
                    }
                }
            });
        },
    });
});
