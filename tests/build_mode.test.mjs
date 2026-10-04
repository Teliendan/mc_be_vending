import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../vending_bp/scripts/build_mode.js", import.meta.url), "utf8");
const { createBuildModeController, rayBoxEntry } = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);

function scene() {
    const dimensions = { id: "minecraft:overworld", getEntities: () => [trader], getBlock: () => head };
    const permutation = (states) => ({
        getState: (name) => states[name],
        withState: (name, value) => permutation({ ...states, [name]: value }),
    });
    const head = {
        typeId: "vm:machine_farmer", location: { x: 0, y: 1, z: 0 }, dimension: dimensions,
        permutation: permutation({ "vm:half": 1, "vm:build_mode": false, "vm:upgraded": true }),
        writes: 0,
        setPermutation(value) { this.permutation = value; this.writes++; },
    };
    const trader = { typeId: "vm:trader_farmer", isValid: true, dimension: dimensions, location: { x: 0.5, y: 1, z: 0.5 } };
    const player = {
        isValid: true, isSneaking: true, dimension: dimensions,
        direction: { x: 0, y: 0, z: 1 }, obstruction: undefined,
        getHeadLocation: () => ({ x: 0.5, y: 1.5, z: -2 }),
        getViewDirection() { return this.direction; },
        getBlockFromViewDirection() { return this.obstruction; },
    };
    const world = { players: [player], getAllPlayers() { return this.players; } };
    return { head, trader, player, world, controller: createBuildModeController(world) };
}

const enabled = (s) => s.head.permutation.getState("vm:build_mode");

test("all 15 machine definitions expose only the head and keep it unmineable", async () => {
    let machines = 0;
    for (const pack of ["vending_villagers_bp", "vending_wandering_bp", "vending_shulker_bp"]) {
        const directory = new URL(`../${pack}/blocks/`, import.meta.url);
        for (const file of await readdir(directory)) {
            if (!file.startsWith("machine_") || !file.endsWith(".json")) continue;
            const block = JSON.parse(await readFile(new URL(file, directory), "utf8"))["minecraft:block"];
            assert.deepEqual(block.description.states["vm:build_mode"], [false, true]);
            const upper = block.permutations.find(p => p.condition === "q.block_state('vm:half') == 1");
            const build = block.permutations.find(p => p.condition === "q.block_state('vm:half') == 1 && q.block_state('vm:build_mode')");
            assert.equal(upper.components["minecraft:selection_box"], false);
            assert.equal(upper.components["minecraft:destructible_by_mining"], false);
            assert.deepEqual(build.components, { "minecraft:selection_box": { origin: [-8, 0, -8], size: [16, 16, 16] } });
            assert.ok(block.permutations.indexOf(build) > block.permutations.indexOf(upper));
            machines++;
        }
    }
    assert.equal(machines, 15);
});

test("whole-head ray handles top, side, parallel miss and reach limit", () => {
    const corner = { x: 0, y: 1, z: 0 };
    assert.equal(rayBoxEntry({ x: 0.5, y: 4, z: 0.5 }, { x: 0, y: -1, z: 0 }, corner), 2);
    assert.equal(rayBoxEntry({ x: -2, y: 1.5, z: 0.5 }, { x: 1, y: 0, z: 0 }, corner), 2);
    assert.equal(rayBoxEntry({ x: -0.01, y: 1.5, z: -2 }, { x: 0, y: 0, z: 1 }, corner), undefined);
    assert.equal(rayBoxEntry({ x: 0.5, y: 1.5, z: -7 }, { x: 0, y: 0, z: 1 }, corner), undefined);
});

test("crouching exposes the head; standing restores trade and preserves upgrade", () => {
    const s = scene(); s.controller.update();
    assert.equal(enabled(s), true);
    assert.equal(s.head.permutation.getState("vm:upgraded"), true);
    s.player.isSneaking = false; s.controller.update();
    assert.equal(enabled(s), false);
});

test("mode stays open when native raycast starts hitting the selectable head", () => {
    const s = scene(); s.controller.update();
    s.player.obstruction = { block: s.head, faceLocation: { x: 0.5, y: 0.5, z: 0 } };
    s.controller.update();
    assert.equal(enabled(s), true);
    assert.equal(s.head.writes, 1);
});

test("looking away closes the head", () => {
    const s = scene(); s.controller.update();
    s.player.direction = { x: 0, y: 0, z: -1 }; s.controller.update();
    assert.equal(enabled(s), false);
});

test("disconnecting the last builder closes the head", () => {
    const s = scene(); s.controller.update();
    s.world.players = []; s.controller.update();
    assert.equal(enabled(s), false);
});

test("an intervening native block hit prevents building through walls", () => {
    const s = scene();
    s.player.obstruction = { block: { location: { x: 0, y: 1, z: -1 } }, faceLocation: { x: 0.5, y: 0.5, z: 0 } };
    s.controller.update();
    assert.equal(enabled(s), false);
});

test("standing viewer has priority regardless of player iteration order", () => {
    for (const standingFirst of [false, true]) {
        const s = scene();
        const standing = { ...s.player, isSneaking: false };
        s.world.players = standingFirst ? [standing, s.player] : [s.player, standing];
        s.controller.update(); assert.equal(enabled(s), false);
        s.world.players = [s.player]; s.controller.update(); assert.equal(enabled(s), true);
    }
});

test("unloaded head reset is deferred and retried", () => {
    const s = scene(); s.controller.update(); s.world.players = [];
    s.head.dimension.getBlock = () => { const error = new Error(); error.name = "LocationInUnloadedChunkError"; throw error; };
    s.controller.update(); assert.equal(enabled(s), true);
    s.head.dimension.getBlock = () => s.head;
    s.controller.update(); assert.equal(enabled(s), false);
});

test("entity reload clears a saved temporary mode", () => {
    const s = scene(); s.controller.update();
    s.controller.resetTrader(s.trader); assert.equal(enabled(s), false);
});

test("a base or mismatched trader is never made selectable as a head", () => {
    const s = scene();
    s.head.permutation = s.head.permutation.withState("vm:half", 0);
    s.controller.update(); assert.equal(s.head.writes, 0);
    s.head.permutation = s.head.permutation.withState("vm:half", 1);
    s.trader.typeId = "vm:trader_butcher";
    s.controller.update(); assert.equal(s.head.writes, 0);
});
