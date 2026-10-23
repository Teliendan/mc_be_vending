import assert from 'node:assert/strict';
import test from 'node:test';
import {runtime, scene} from './support/runtime.mjs';

test('upgrade and one kit payment finish synchronously on the same trader', async () => {
    const r = await runtime(), s = scene(), m = s.machine();
    r.components.item['vm:upgrade_kit'].onUseOn({block: m.base, source: s.player});
    assert.equal(r.deferred.length, 0);
    assert.equal(m.trader.getDynamicProperty('vm:upgraded'), true);
    assert.equal(s.held, undefined);
    assert.equal(s.actors.length, 1);
    assert.deepEqual(s.events, ['vm:apply_upgrade']);
    for (const block of [m.base, m.head]) assert.equal(block.permutation.getState('vm:upgraded'), true);
    s.held = {typeId: 'vm:upgrade_kit', amount: 1};
    r.components.item['vm:upgrade_kit'].onUseOn({block: m.base, source: s.player});
    assert.equal(s.held.amount, 1);
    assert.equal(s.events.length, 1);
});
test('Creative does not consume a kit', async () => {
    const r = await runtime(), s = scene({mode: 'Creative'}), m = s.machine();
    r.components.item['vm:upgrade_kit'].onUseOn({block: m.base, source: s.player});
    assert.equal(s.held.amount, 1);
    assert.equal(m.trader.getDynamicProperty('vm:upgraded'), true);
});
test('using the kit on the upper half does not upgrade', async () => {
    const r = await runtime(), s = scene(), m = s.machine();
    r.components.item['vm:upgrade_kit'].onUseOn({block: m.head, source: s.player});
    assert.equal(s.events.length, 0); assert.equal(s.held.amount, 1);
});
test('a loaded upgraded trader recolours its machine', async () => {
    const r = await runtime(), s = scene(), m = s.machine();
    m.trader.setDynamicProperty('vm:upgraded', true);
    r.callbacks.entityLoad({entity: m.trader});
    for (const block of [m.base, m.head]) assert.equal(block.permutation.getState('vm:upgraded'), true);
    assert.equal(m.trader.isValid, true);
});
test('a loaded trader without its machine block is removed', async () => {
    const r = await runtime(), s = scene(), m = s.machine();
    m.head.setType('minecraft:air');
    r.callbacks.entityLoad({entity: m.trader});
    assert.equal(m.trader.isValid, false);
});
