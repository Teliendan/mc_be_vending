import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";

// Load the actual event wiring with a narrow Script API substitute. The build
// mode has its own suite; this suite exercises destruction and trader lookup.
const callbacks = {};
const deferred = [];
function flush() {
    while (deferred.length) deferred.shift()();
}
const subscriptions = new Proxy({}, { get: (_, name) => ({ subscribe(fn) { callbacks[name] = fn; } }) });
const api = {
    world: { afterEvents: subscriptions, beforeEvents: subscriptions },
    system: { beforeEvents: subscriptions, run: fn => deferred.push(fn) },
    ItemStack: class {}, BlockPermutation: {},
    message: () => "", createBuildModeController: () => ({}),
};
globalThis.__vendingLifecycle = api;
const source = await readFile(new URL("../vending_bp/scripts/main.js", import.meta.url), "utf8");
const withoutImports = source.replace(/^import .*;\r?\n/gm, "");
await import(`data:text/javascript;base64,${Buffer.from("const {world, system, ItemStack, BlockPermutation, message, createBuildModeController} = globalThis.__vendingLifecycle;\n" + withoutImports).toString("base64")}`);
delete globalThis.__vendingLifecycle;

const components = {};
const registry = { registerCustomComponent: (name, component) => { components[name] = component; } };
callbacks.startup({ blockComponentRegistry: registry, itemComponentRegistry: registry });
const machineComponent = components["vm:machine"];
const player = { typeId: "minecraft:player" };

const key = ({ x, y, z }) => `${x},${y},${z}`;
const permutation = (typeId, half) => ({ type: { id: typeId }, getState: name => name === "vm:half" ? half : undefined });

function scene() {
    const blocks = new Map(), traders = [], writes = [], commands = [];
    const dimension = {
        getBlock(location) {
            return blocks.get(key(location)) ?? { typeId: "minecraft:air", location, dimension };
        },
        getEntities(query) {
            return traders.filter(t => t.isValid && t.typeId === query.type && Math.hypot(
                t.location.x - query.location.x, t.location.y - query.location.y, t.location.z - query.location.z
            ) <= query.maxDistance);
        },
        runCommand(command) {
            commands.push(command);
            const match = /^setblock (-?\d+) (-?\d+) (-?\d+) air destroy$/.exec(command);
            assert.ok(match, "only native support-loss destruction is used");
            const location = { x: Number(match[1]), y: Number(match[2]), z: Number(match[3]) };
            const current = this.getBlock(location);
            assert.ok(current.typeId.startsWith("vm:machine_"), "never destroy a vanished or replacement base");
            const old = current.permutation;
            current.setType("minecraft:air");
            // `setblock ... destroy` fires the block's onBreak (d.ts); no actor.
            machineComponent.onBreak({ block: current, dimension, brokenBlockPermutation: old });
        },
    };
    function put(typeId, half, location) {
        const block = { typeId, location, dimension, permutation: permutation(typeId, half), setType(value) {
            writes.push({ location, value }); this.typeId = value;
            this.permutation = permutation(value); blocks.set(key(location), this);
        } };
        blocks.set(key(location), block); return block;
    }
    function trader(base, profession = "farmer") {
        const entity = {
            typeId: `vm:trader_${profession}`, location: { x: base.x + 0.5, y: base.y + 1, z: base.z + 0.5 },
            isValid: true, removals: 0, remove() { this.removals++; this.isValid = false; },
        };
        traders.push(entity); return entity;
    }
    function machine(base, profession = "farmer") {
        const type = `vm:machine_${profession}`;
        const lower = put(type, 0, base);
        const upper = put(type, 1, { ...base, y: base.y + 1 });
        return { lower, upper, trader: trader(base, profession) };
    }
    function destroy(block, { source, settle = true } = {}) {
        const old = block.permutation;
        blocks.delete(key(block.location));
        const event = { block: dimension.getBlock(block.location), dimension, brokenBlockPermutation: old, entitySource: source };
        machineComponent.onBreak(event);
        if (settle) flush();
        return event;
    }
    return { blocks, traders, writes, commands, dimension, put, trader, machine, destroy };
}

test("registration: no world-wide break or explosion subscription; machine component has both callbacks", () => {
    assert.equal(callbacks.playerBreakBlock, undefined);
    assert.equal(callbacks.blockExplode, undefined);
    assert.equal(typeof machineComponent.onBreak, "function");
    assert.equal(typeof machineComponent.beforeOnPlayerPlace, "function");
});

test("player breaks: either half removes its counterpart and trader, no command", () => {
    for (const half of ["lower", "upper"]) {
        const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
        const other = half === "lower" ? m.upper : m.lower;
        const event = s.destroy(m[half], { source: player });
        assert.equal(other.typeId, "minecraft:air");
        assert.equal(m.trader.removals, 1);
        assert.equal(s.commands.length, 0);
        assert.equal(s.writes.length, 1);
        machineComponent.onBreak(event);
        flush();
        assert.equal(s.writes.length, 1);
        assert.equal(m.trader.removals, 1);
    }
});

test("no actor: base destroyed removes head; head destroyed drops the base once, re-entry adds nothing", () => {
    {
        const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
        const event = s.destroy(m.lower);
        assert.equal(m.upper.typeId, "minecraft:air");
        assert.equal(s.commands.length, 0);
        assert.equal(m.trader.removals, 1);
        machineComponent.onBreak(event);
        flush();
        assert.equal(s.writes.length, 1);
        assert.equal(m.trader.removals, 1);
    }
    {
        const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
        const event = s.destroy(m.upper);
        assert.deepEqual(s.commands, ["setblock 0 0 0 air destroy"]);
        assert.equal(m.lower.typeId, "minecraft:air");
        assert.equal(m.trader.removals, 1);
        assert.equal(s.writes.length, 1, "the re-entrant base onBreak adds no write");
        machineComponent.onBreak(event);
        flush();
        assert.equal(s.commands.length, 1);
        assert.equal(s.writes.length, 1);
        assert.equal(m.trader.removals, 1);
    }
});

test("adjacent and vertically stacked machines keep their own traders", () => {
    const s = scene();
    const nearby = s.machine({ x: 1, y: 0, z: 0 }); // Insert first: old radius-two lookup chose this trader.
    const above = s.machine({ x: 0, y: 2, z: 0 });
    const target = s.machine({ x: 0, y: 0, z: 0 });
    s.destroy(target.upper);
    assert.equal(target.trader.removals, 1);
    for (const m of [nearby, above]) {
        assert.equal(m.trader.removals, 0);
        assert.ok(m.lower.typeId.startsWith("vm:machine_"));
        assert.ok(m.upper.typeId.startsWith("vm:machine_"));
    }
});

test("counterpart replacements and wrong-half blocks are preserved", () => {
    for (const [type, half] of [["minecraft:stone", undefined], ["vm:machine_farmer", 0], ["vm:machine_cleric", 1]]) {
        const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
        const replacement = s.put(type, half, m.upper.location);
        s.destroy(m.lower);
        assert.equal(replacement.typeId, type);
        assert.equal(s.writes.length, 0);
        assert.equal(m.trader.removals, 1);
    }
});

test("delayed event does not remove a new machine at the destroyed cell", () => {
    const s = scene(), old = s.machine({ x: 0, y: 0, z: 0 });
    const snapshot = old.lower.permutation;
    const replacement = s.machine({ x: 0, y: 0, z: 0 }, "cleric");
    machineComponent.onBreak({ block: replacement.lower, dimension: s.dimension, brokenBlockPermutation: snapshot });
    flush();
    assert.equal(s.writes.length, 0);
    assert.equal(s.commands.length, 0);
    assert.equal(replacement.trader.removals, 0);
});

test("one destroy of both halves (blast or fill) in either order cleans the trader without extra items", () => {
    for (const order of [[0, 1], [1, 0]]) {
        const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
        const events = [m.lower, m.upper].map(block => ({ block, dimension: s.dimension, brokenBlockPermutation: block.permutation }));
        s.blocks.clear();
        for (const index of order) machineComponent.onBreak(events[index]);
        flush();
        assert.equal(m.trader.removals, 1);
        assert.equal(s.writes.length, 0);
        assert.equal(s.commands.length, 0);
        // No spawnItem exists on this fixture: an accidental scripted refund fails.
    }
});

test("all 15 definitions keep unconditional any-tool base loot and explicit empty upper loot", async () => {
    let checked = 0;
    for (const pack of ["vending_villagers_bp", "vending_wandering_bp", "vending_shulker_bp"]) {
        const root = new URL(`../${pack}/`, import.meta.url);
        for (const file of await readdir(new URL("blocks/", root))) {
            if (!file.startsWith("machine_") || !file.endsWith(".json")) continue;
            const block = JSON.parse(await readFile(new URL(`blocks/${file}`, root), "utf8"))["minecraft:block"];
            const basePath = block.components["minecraft:loot"];
            const upper = block.permutations.find(p => p.condition === "q.block_state('vm:half') == 1");
            const base = JSON.parse(await readFile(new URL(basePath, root), "utf8"));
            assert.deepEqual(base, { pools: [{ rolls: 1, entries: [{ type: "item", name: block.description.identifier,
                functions: [{ function: "explosion_decay" }] }] }] });
            const empty = JSON.parse(await readFile(new URL(upper.components["minecraft:loot"], root), "utf8"));
            assert.deepEqual(empty, { pools: [{ rolls: 1, entries: [{ type: "empty" }] }] });
            checked++;
        }
    }
    assert.equal(checked, 15);
});

test("all matching orphan traders are removed; different professions stay", () => {
    const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
    const duplicate = s.trader(m.lower.location), other = s.trader(m.lower.location, "cleric");
    s.destroy(m.lower);
    assert.equal(m.trader.removals, 1); assert.equal(duplicate.removals, 1);
    assert.equal(other.removals, 0);
});

test("cleanup lets native destruction handle both halves before support-loss removal", () => {
    for (const order of [["upper", "lower"], ["lower", "upper"]]) {
        const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
        s.destroy(m[order[0]], { settle: false });
        assert.ok(m[order[1]].typeId.startsWith("vm:machine_"), "first event cannot intercept native destruction of the next half");
        assert.equal(s.commands.length, 0);
        assert.equal(s.writes.length, 0);
        assert.equal(m.trader.removals, 0);
        s.destroy(m[order[1]], { settle: false });
        flush();
        assert.equal(s.commands.length, 0, "no support-loss refund for an already exploded base");
        assert.equal(s.writes.length, 0);
        assert.equal(m.trader.removals, 1);
    }
});

test("upper-only destruction removes a genuinely surviving base exactly once after settling", () => {
    const s = scene(), m = s.machine({ x: -3, y: 9, z: 7 });
    s.destroy(m.upper, { settle: false });
    assert.equal(s.commands.length, 0);
    assert.equal(m.lower.typeId, "vm:machine_farmer");
    flush();
    assert.deepEqual(s.commands, ["setblock -3 9 7 air destroy"]);
    assert.equal(m.trader.removals, 1);
});

test("queued cleanup preserves a replacement placed before settlement", () => {
    const s = scene(), old = s.machine({ x: 0, y: 0, z: 0 });
    s.destroy(old.lower, { settle: false });
    const replacement = s.machine({ x: 0, y: 0, z: 0 }, "cleric");
    flush();
    assert.equal(s.writes.length, 0);
    assert.equal(s.commands.length, 0);
    assert.equal(replacement.lower.typeId, "vm:machine_cleric");
    assert.equal(replacement.upper.typeId, "vm:machine_cleric");
    assert.equal(replacement.trader.removals, 0);
});

test("queued cleanup captures event position without retaining a live block handle", () => {
    const s = scene(), m = s.machine({ x: 0, y: 0, z: 0 });
    const oldPermutation = m.upper.permutation;
    s.blocks.delete(key(m.upper.location));
    let expired = false;
    machineComponent.onBreak({ dimension: s.dimension, brokenBlockPermutation: oldPermutation,
        block: { get location() { assert.equal(expired, false, "event block access must happen inside its callback"); return m.upper.location; } } });
    expired = true;
    flush();
    assert.equal(s.commands.length, 1);
    assert.equal(m.trader.removals, 1);
});
