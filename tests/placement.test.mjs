import assert from 'node:assert/strict';
import test from 'node:test';
import {runtime, scene, permutation} from './support/runtime.mjs';

function place(r, base) {
    const event = {block: base, permutationToPlace: permutation('vm:machine_farmer', {'vm:half': 0})};
    r.components.block['vm:machine'].beforeOnPlayerPlace(event);
    return !event.cancel;
}

test('occupied headroom cancels before native consumption', async () => {
    const r = await runtime(), s = scene();
    s.block('minecraft:stone', {}, {x: 0, y: 11, z: 0});
    assert.equal(place(r, s.block('minecraft:air', {}, {x: 0, y: 10, z: 0})), false);
    assert.equal(s.writes.length, 0);
});
test('world ceiling cancels placement', async () => {
    const r = await runtime(), s = scene();
    assert.equal(place(r, s.block('minecraft:air', {}, {x: 0, y: 11, z: 0})), false);
});
test('an actor in the upper cell blocks placement', async () => {
    const r = await runtime(), s = scene();
    s.blockers = [{typeId: 'minecraft:villager_v2', getComponent: () => undefined}];
    assert.equal(place(r, s.block('minecraft:air', {}, {x: 0, y: 10, z: 0})), false);
});
test('dropped items, projectiles and spectators do not obstruct upper placement', async () => {
    for (const typeId of ['minecraft:item', 'minecraft:arrow', 'minecraft:player']) {
        const r = await runtime(), s = scene();
        s.blockers = [{typeId, getComponent: () => typeId === 'minecraft:arrow' ? {} : undefined, getGameMode: () => 'Spectator'}];
        assert.equal(place(r, s.block('minecraft:air', {}, {x: 0, y: 10, z: 0})), true);
    }
});

test('neighbouring hidden traders do not prevent side-by-side or diagonal machines', async () => {
    for (const location of [{x: 1.5, y: 11, z: 0.5}, {x: 1.5, y: 11, z: 1.5}]) {
        const r = await runtime(), s = scene();
        // The engine's volume query can return the adjacent machine's helper.
        s.blockers = [{typeId: 'vm:trader_farmer', location, getComponent: () => undefined}];
        assert.equal(place(r, s.block('minecraft:air', {}, {x: 0, y: 10, z: 0})), true);
    }
});

test('a hidden trader does not hide a real mob obstructing the new head', async () => {
    const r = await runtime(), s = scene();
    s.blockers = ['vm:trader_farmer', 'minecraft:cow'].map(typeId => ({typeId, getComponent: () => undefined}));
    assert.equal(place(r, s.block('minecraft:air', {}, {x: 0, y: 10, z: 0})), false);
});
test('placement raises the upper half and spawns one trader', async () => {
    const r = await runtime(), s = scene();
    const base = s.block('vm:machine_farmer', {'vm:half': 0}, {x: 0, y: 10, z: 0});
    r.callbacks.playerPlaceBlock({block: base, player: s.player});
    assert.equal(base.above().permutation.getState('vm:half'), 1);
    assert.equal(s.actors.length, 1);
    assert.deepEqual(s.actors[0].location, {x: 0.5, y: 11, z: 0.5});
});

test('Creative Sneak input bypasses the trader during the transition to building', async () => {
    const r = await runtime(), s = scene({mode: 'Creative'});
    const target = {typeId: 'vm:trader_farmer'};
    s.sneakButton = 'Pressed';
    const building = {player: s.player, target};
    r.callbacks.playerInteractWithEntity(building);
    assert.equal(building.cancel, true);
    s.sneakButton = 'Released';
    const trading = {player: s.player, target};
    r.callbacks.playerInteractWithEntity(trading);
    assert.notEqual(trading.cancel, true);
});
