import assert from 'node:assert/strict';
import test from 'node:test';
import {runtime, scene, permutation} from './support/runtime.mjs';

for (const mode of ['Survival', 'Creative']) {
    test(`${mode}: occupied headroom cancels before native consumption without a refund`, async () => {
        const r = await runtime(), s = scene({mode});
        const base = s.block('minecraft:air', {}, {x: 0, y: 10, z: 0});
        s.block('minecraft:stone', {}, {x: 0, y: 11, z: 0});
        const event = {block: base, player: s.player, permutationToPlace: permutation('vm:machine_farmer', {'vm:half': 0})};
        r.components.block['vm:machine'].beforeOnPlayerPlace(event);
        assert.equal(event.cancel, true);
        assert.equal(s.writes.length + s.refunds.length + s.drops.length, 0);
    });
    for (const full of [false, true]) {
        test(`${mode}, full=${full}: failed construction removes owned pair and refunds Survival once`, async () => {
            const r = await runtime(), s = scene({mode, full});
            const base = s.block('vm:machine_farmer', {'vm:half': 0}, {x: 0, y: 10, z: 0});
            s.spawnFails = true;
            r.callbacks.playerPlaceBlock({block: base, player: s.player});
            assert.equal(base.typeId, 'minecraft:air');
            assert.equal(s.dimension.getBlock({x: 0, y: 11, z: 0}).typeId, 'minecraft:air');
            assert.equal(s.refunds.length, mode === 'Survival' && !full ? 1 : 0);
            assert.equal(s.drops.length, mode === 'Survival' && full ? 1 : 0);
            r.callbacks.playerPlaceBlock({block: base, player: s.player});
            assert.equal(s.refunds.length + s.drops.length, mode === 'Survival' ? 1 : 0);
        });
    }
}
test('world ceiling and unavailable upper block cancel placement', async () => {
    for (const unloaded of [false, true]) {
        const r = await runtime(), s = scene(); s.unloaded = unloaded;
        const base = s.block('minecraft:air', {}, {x: 0, y: unloaded ? 10 : 11, z: 0});
        const event = {block: base, permutationToPlace: permutation('vm:machine_farmer', {'vm:half': 0})};
        r.components.block['vm:machine'].beforeOnPlayerPlace(event);
        assert.equal(event.cancel, true); assert.equal(s.writes.length, 0);
    }
});
test('upper actor intersection blocks placement; contact at its edge does not', async () => {
    for (const x of [0.5, 1.5]) {
        const r = await runtime(), s = scene();
        const base = s.block('minecraft:air', {}, {x: 0, y: 10, z: 0});
        s.blockers = [{typeId: 'minecraft:villager_v2', getAABB: () => ({center: {x, y: 11.5, z: 0.5}, extent: {x: 0.5, y: 0.5, z: 0.5}})}];
        const event = {block: base, permutationToPlace: permutation('vm:machine_farmer', {'vm:half': 0})};
        r.components.block['vm:machine'].beforeOnPlayerPlace(event);
        assert.equal(!!event.cancel, x === 0.5);
    }
});
test('successful placement creates one pair/trader; shadow feedback failure leaves it intact', async () => {
    const r = await runtime(), s = scene(); s.shadowFails = true;
    const base = s.block('vm:machine_farmer', {'vm:half': 0}, {x: 0, y: 10, z: 0});
    r.callbacks.playerPlaceBlock({block: base, player: s.player});
    assert.equal(base.typeId, 'vm:machine_farmer');
    assert.equal(base.above().permutation.getState('vm:half'), 1);
    assert.equal(s.actors.length, 1); assert.equal(s.refunds.length + s.drops.length, 0);
});
test('dropped items, projectiles and spectators do not obstruct upper placement', async () => {
    for (const typeId of ['minecraft:item', 'minecraft:arrow', 'minecraft:player']) {
        const r = await runtime(), s = scene();
        const base = s.block('minecraft:air', {}, {x: 0, y: 10, z: 0});
        s.blockers = [{typeId, getComponent: () => typeId === 'minecraft:arrow' ? {} : undefined,
            getGameMode: () => 'Spectator', getAABB: () => {throw new Error('ignored actors need no bounds');}}];
        const event = {block: base, permutationToPlace: permutation('vm:machine_farmer', {'vm:half': 0})};
        r.components.block['vm:machine'].beforeOnPlayerPlace(event);
        assert.equal(!!event.cancel, false);
    }
});
