import { message } from "./messages.js";
import { world, system, BlockPermutation } from "@minecraft/server";
import { createBuildModeController } from "./build_mode.js";

// ---------------------------------------------------------------------------
// Vending machine: block + hidden trader
//
// A machine is one custom block occupying two positions -- vm:half 0 (solid,
// selectable, breakable) and vm:half 1 (solid, normally selection_box:false so
// clicks reach the trader; selectable while crouching to build against it) --
// with an invisible vm:trader_<prof> entity
// standing inside the upper half. The entity owns the trade table; the block
// owns collision, placement and breaking.
//
// Progression is ENGINE-owned. The trader levels itself from the five tiers in
// its trade table, exactly like a villager. Script never reads or writes a
// tier -- it cannot, and it no longer needs to.
// ---------------------------------------------------------------------------

const BLOCK_PREFIX = "vm:machine_";
const TRADER_PREFIX = "vm:trader_";
const buildMode = createBuildModeController(world);

world.afterEvents.worldLoad.subscribe(() => {
    for (const id of ["overworld", "nether", "the_end"]) {
        for (const trader of world.getDimension(id).getEntities()) {
            if (trader.isValid && trader.typeId.startsWith(TRADER_PREFIX)) buildMode.resetTrader(trader);
        }
    }
    system.runInterval(() => buildMode.update(), 1);
});

// Suppress trading during the tick in which crouching starts, before the
// selectable head state reaches the client. Subsequent use is native placement.
world.beforeEvents.playerInteractWithEntity.subscribe((event) => {
    if (event.player.isSneaking && event.target.typeId.startsWith(TRADER_PREFIX)) event.cancel = true;
});

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

world.afterEvents.entityLoad.subscribe(({ entity }) => {
    if (!entity.typeId.startsWith(TRADER_PREFIX)) return;
    // Owner 2026-10-23: a trader whose block is not its machine's head is an
    // orphan. Only a block actually read can condemn it.
    const l = entity.location;
    const head = entity.dimension.getBlock({ x: Math.floor(l.x), y: Math.floor(l.y), z: Math.floor(l.z) });
    if (!head) return;
    if (head.typeId !== BLOCK_PREFIX + entity.typeId.slice(TRADER_PREFIX.length) || head.permutation.getState("vm:half") !== 1) {
        entity.remove();
        return;
    }
    hideShadow(entity);
    buildMode.resetTrader(entity);
    // Machines upgraded before the block had a vm:upgraded state catch up here.
    if (entity.getDynamicProperty("vm:upgraded") === true) showUpgraded(head);
});

// The upgraded look (gold + emerald corners) is a block state on both halves.
// It is only ever set, never cleared: breaking the machine removes it anyway.
function showUpgraded(head) {
    for (const block of [head.below(), head]) {
        if (block.typeId !== head.typeId || block.permutation.getState("vm:upgraded") === true) continue;
        block.setPermutation(block.permutation.withState("vm:upgraded", true));
    }
}

// Machine headroom: the upper block, unless the base is at the build ceiling.
function blockAbove(block) {
    try {
        return block.above();
    } catch (error) {
        if (error.name === "LocationOutOfWorldBoundariesError") return undefined;
        throw error;
    }
}

// Native placement checks the base cell; this checks the upper cell. It must be
// air (owner policy) with no actor standing in it.
function headroom(base) {
    const head = blockAbove(base);
    if (!head?.isAir) return undefined;
    const blocked = base.dimension.getEntities({ location: head.location, volume: { x: 1, y: 1, z: 1 } })
        .some(entity => entity.typeId !== "minecraft:item" && entity.typeId !== "minecraft:xp_orb" &&
            !entity.getComponent("minecraft:projectile") &&
            !(entity.typeId === "minecraft:player" && entity.getGameMode() === "Spectator"));
    return blocked ? undefined : head;
}

// One-off burst of green villager sparkles over the whole machine.
function sparkle(baseBlock) {
    const l = baseBlock.location;
    for (let i = 0; i < 24; i++) {
        const spot = { x: l.x + Math.random(), y: l.y + Math.random() * 2.2, z: l.z + Math.random() };
        baseBlock.dimension.spawnParticle("minecraft:villager_happy", spot);
    }
}

function tradersAt(dimension, baseBlock, profession) {
    // Traders have no movement/physics components. A neighbouring machine can
    // be only one block away, so the former radius of two was ambiguous.
    return dimension.getEntities({
        type: TRADER_PREFIX + profession,
        location: traderSpot(baseBlock),
        maxDistance: 0.1,
    });
}

// --- placement: raise the upper half and spawn the trader ------------------
// vm:machine beforeOnPlayerPlace already cancelled placement without headroom
// in this tick, and an item always places the base (vm:half 0).
world.afterEvents.playerPlaceBlock.subscribe(({ block }) => {
    if (!block.typeId.startsWith(BLOCK_PREFIX)) return;
    block.above().setPermutation(BlockPermutation.resolve(block.typeId, { "vm:half": 1 }));
    hideShadow(block.dimension.spawnEntity(TRADER_PREFIX + professionOf(block.typeId), traderSpot(block)));
});

// --- destruction: either half can be destroyed by Creative or an explosion --
function removeMachine(dimension, location, oldPermutation, { dropBase = false } = {}) {
    const typeId = oldPermutation.type.id;
    if (!typeId.startsWith(BLOCK_PREFIX)) return;
    const half = oldPermutation.getState("vm:half");
    if (half !== 0 && half !== 1) return;
    const base = { location: { ...location, y: location.y - half } };
    const counterpartLocation = { ...location, y: location.y + (half === 0 ? 1 : -1) };
    try {
        // A preceding handler may already have placed another machine here.
        // Its trader belongs to the new machine, not to this destruction event.
        const current = dimension.getBlock(location);
        if (current?.typeId.startsWith(BLOCK_PREFIX)) return;
        const counterpart = dimension.getBlock(counterpartLocation);
        if (counterpart?.typeId === typeId && counterpart.permutation.getState("vm:half") === 1 - half) {
            if (half === 1 && dropBase) {
                // The upper half has no loot. Its surviving base falls as a
                // native support-loss drop, outside the original blast context.
                const { x, y, z } = counterpartLocation;
                dimension.runCommand(`setblock ${x} ${y} ${z} air destroy`);
            } else {
                counterpart.setType("minecraft:air");
            }
        }
    } catch (error) {
        if (error.name !== "LocationInUnloadedChunkError" && error.name !== "LocationOutOfWorldBoundariesError") throw error;
    }
    for (const trader of tradersAt(dimension, base, professionOf(typeId))) {
        if (trader.isValid) trader.remove();
    }
}

world.afterEvents.playerBreakBlock.subscribe((e) => {
    removeMachine(e.dimension, e.block.location, e.brokenBlockPermutation, {
        dropBase: e.player.getGameMode() !== "Creative",
    });
});
world.afterEvents.blockExplode.subscribe((e) => {
    const oldPermutation = e.explodedBlockPermutation;
    if (!oldPermutation.type.id.startsWith(BLOCK_PREFIX)) return;
    const dimension = e.dimension;
    const location = { ...e.block.location };
    // Let native destruction finish before treating the other half as a
    // support-loss survivor. It may also be directly impacted by this blast.
    // Capture values now; the event's block handle may be invalid by then.
    system.run(() => removeMachine(dimension, location, oldPermutation, { dropBase: true }));
});

// --- the Upgrade Kit: right-click the base with it -------------------------
//
// One kit per machine. The flag lives on the trader as a dynamic property, so
// it travels with the thing it describes and dies with it.
system.beforeEvents.startup.subscribe((init) => {
    init.blockComponentRegistry.registerCustomComponent("vm:machine", {
        beforeOnPlayerPlace(event) {
            if (!headroom(event.block)) event.cancel = true;
        },
    });
    init.itemComponentRegistry.registerCustomComponent("vm:upgrade_kit", {
        // Custom item onUseOn is privileged: finish in this callback.
        onUseOn(event) {
            const block = event.block;
            const player = event.source;
            // Only the base: the head is selectable only while building against it.
            if (!block.typeId.startsWith(BLOCK_PREFIX) || block.permutation.getState("vm:half") !== 0) return;
            const head = block.above();
            const trader = tradersAt(block.dimension, block, professionOf(block.typeId))[0];
            if (!trader) return;

            if (trader.getDynamicProperty("vm:upgraded") === true) {
                showUpgraded(head);
                player.sendMessage(message("upgraded"));
                return;
            }

            trader.triggerEvent("vm:apply_upgrade");
            trader.setDynamicProperty("vm:upgraded", true);
            // The kit is the used item; it does not stack and has no off-hand use.
            if (player.getGameMode() !== "Creative") player.getComponent("minecraft:equippable").setEquipment("Mainhand");
            showUpgraded(head);
            sparkle(block);
            block.dimension.playSound("random.anvil_use", traderSpot(block), { volume: 0.8, pitch: 1.2 });
            player.sendMessage(message("upgrade"));
        },
    });
});
