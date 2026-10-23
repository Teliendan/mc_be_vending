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
for (const failure of ['particleFails', 'soundFails', 'chatFails', 'visualFails']) {
    test(`${failure}: feedback cannot prevent upgrade payment or cause a repeated charge`, async () => {
        const r = await runtime(), s = scene(), m = s.machine(); s[failure] = true;
        r.components.item['vm:upgrade_kit'].onUseOn({block: m.base, source: s.player});
        assert.equal(s.held, undefined);
        assert.equal(m.trader.getDynamicProperty('vm:upgraded'), true);
        s[failure] = false; s.held = {typeId: 'vm:upgrade_kit', amount: 1};
        r.components.item['vm:upgrade_kit'].onUseOn({block: m.base, source: s.player});
        assert.equal(s.held.amount, 1);
    });
}
test('wrong held item, head use and incomplete pair do not upgrade', async () => {
    for (const kind of ['item', 'head', 'missing']) {
        const r = await runtime(), s = scene(), m = s.machine();
        if (kind === 'item') s.held = {typeId: 'minecraft:stick', amount: 1};
        if (kind === 'missing') m.head.setType('minecraft:air');
        r.components.item['vm:upgrade_kit'].onUseOn({block: kind === 'head' ? m.head : m.base, source: s.player});
        assert.equal(s.events.length, 0); assert.equal(s.held.amount, 1);
    }
});
test('loaded upgraded trader recolors only an intact matching profession pair', async () => {
    for (const kind of ['matching', 'different', 'wrong-half', 'absent', 'unavailable']) {
        const r = await runtime(), s = scene(), m = s.machine();
        m.trader.setDynamicProperty('vm:upgraded', true);
        if (kind === 'different') m.trader.typeId = 'vm:trader_butcher';
        if (kind === 'wrong-half') m.head.setPermutation(m.head.permutation.withState('vm:half', 0));
        if (kind === 'absent') m.base.setType('minecraft:air');
        if (kind === 'unavailable') s.unloaded = true;
        s.writes.length = 0;
        r.callbacks.entityLoad({entity: m.trader});
        assert.equal(s.writes.length, kind === 'matching' ? 2 : 0);
        assert.equal(m.trader.isValid, true, 'ownership check never deletes a trader');
    }
});
