// WORKAROUND: API 2.8 has no native entity-use-to-block-use forwarding.
// Temporarily expose the head as a native placement target. The block owns the
// collision/attachment surface; Minecraft owns placement, orientation and costs.
const MACHINE = "vm:machine_";
const TRADER = "vm:trader_";
const REACH = 6;

function loadedBlock(dimension, location) {
    try {
        return dimension.getBlock(location);
    } catch (error) {
        if (error.name === "LocationInUnloadedChunkError" || error.name === "LocationOutOfWorldBoundariesError") return undefined;
        throw error;
    }
}

export function rayBoxEntry(origin, direction, corner, reach = REACH) {
    let near = 0;
    let far = reach;
    for (const axis of ["x", "y", "z"]) {
        const delta = direction[axis];
        if (Math.abs(delta) < 1e-8) {
            if (origin[axis] < corner[axis] || origin[axis] > corner[axis] + 1) return undefined;
            continue;
        }
        const a = (corner[axis] - origin[axis]) / delta;
        const b = (corner[axis] + 1 - origin[axis]) / delta;
        near = Math.max(near, Math.min(a, b));
        far = Math.min(far, Math.max(a, b));
        if (near > far) return undefined;
    }
    return near;
}

export function traderHead(trader) {
    const location = trader.location;
    const block = loadedBlock(trader.dimension, {
        x: Math.floor(location.x), y: Math.floor(location.y), z: Math.floor(location.z),
    });
    if (!block || block.typeId !== MACHINE + trader.typeId.slice(TRADER.length)) return undefined;
    return block.permutation.getState("vm:half") === 1 ? block : undefined;
}

export function aimedHead(player) {
    const origin = player.getHeadLocation();
    const direction = player.getViewDirection();
    let nearest;
    let nearestDistance = REACH + 1;
    // Test the whole head, including its edges, while it is unselectable. This
    // also works once its full selection box hides the small trader hitbox.
    for (const trader of player.dimension.getEntities({ location: origin, maxDistance: REACH + 2 })) {
        if (!trader.isValid || !trader.typeId.startsWith(TRADER)) continue;
        const head = traderHead(trader);
        if (!head) continue;
        const distance = rayBoxEntry(origin, direction, head.location);
        if (distance !== undefined && distance < nearestDistance) {
            nearest = head;
            nearestDistance = distance;
        }
    }
    if (!nearest) return undefined;
    // Keep vanilla raycast shape/occlusion handling: do not select a machine
    // through a wall or an intervening full/partial block.
    const hit = player.getBlockFromViewDirection({ maxDistance: REACH, includeLiquidBlocks: true });
    if (hit) {
        const b = hit.block.location;
        const f = hit.faceLocation;
        const distance = Math.hypot(b.x + f.x - origin.x, b.y + f.y - origin.y, b.z + f.z - origin.z);
        if (distance + 1e-5 < nearestDistance) return undefined;
    }
    return nearest;
}

function headKey(block) {
    const { x, y, z } = block.location;
    return `${block.dimension.id}:${x},${y},${z}`;
}

function setBuildMode(block, enabled) {
    if (!block || !block.typeId.startsWith(MACHINE) || block.permutation.getState("vm:half") !== 1) return;
    if (block.permutation.getState("vm:build_mode") === enabled) return;
    block.setPermutation(block.permutation.withState("vm:build_mode", enabled));
}

export function createBuildModeController(world) {
    const active = new Map();
    return {
        resetTrader(trader) {
            const head = traderHead(trader);
            if (head) setBuildMode(head, false);
        },
        update() {
            const desired = new Map();
            const trading = new Set();
            for (const player of world.getAllPlayers()) {
                if (!player.isValid) continue;
                const head = aimedHead(player);
                if (!head) continue;
                const key = headKey(head);
                if (player.isSneaking) desired.set(key, head);
                else trading.add(key);
            }
            // Selection boxes are shared world state. A standing player aiming
            // at the same head keeps trade access; building resumes afterwards.
            for (const key of trading) desired.delete(key);
            for (const [key, previous] of active) {
                if (desired.has(key)) continue;
                const block = loadedBlock(previous.dimension, previous.location);
                if (!block) continue; // restore when the chunk is available again
                setBuildMode(block, false);
                active.delete(key);
            }
            for (const [key, head] of desired) {
                setBuildMode(head, true);
                active.set(key, { dimension: head.dimension, location: { ...head.location } });
            }
        },
    };
}
