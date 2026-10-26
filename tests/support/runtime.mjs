import {readFile} from 'node:fs/promises';
let serial = 0;
export async function runtime() {
    const callbacks = {}, deferred = [], components = {block: {}, item: {}};
    const events = new Proxy({}, {get: (_, key) => ({subscribe(fn) {callbacks[key] = fn;}})});
    const buildSource = await readFile(new URL('../../vending_bp/scripts/build_mode.js', import.meta.url), 'utf8');
    const {hasSneakIntent} = await import(`data:text/javascript;base64,${Buffer.from(buildSource).toString('base64')}`);
    const api = {
        world: {afterEvents: events, beforeEvents: events},
        system: {beforeEvents: events, run: fn => deferred.push(fn)},
        BlockPermutation: {resolve: permutation}, message: key => key,
        createBuildModeController: () => ({resetTrader() {}}), hasSneakIntent,
    };
    globalThis.__vendingTestRuntime = api;
    const source = (await readFile(new URL('../../vending_bp/scripts/main.js', import.meta.url), 'utf8')).replace(/^import .*;\r?\n/gm, '');
    await import(`data:text/javascript;base64,${Buffer.from(`const {world, system, BlockPermutation, message, createBuildModeController, hasSneakIntent} = globalThis.__vendingTestRuntime;\n// instance ${serial++}\n` + source).toString('base64')}`);
    delete globalThis.__vendingTestRuntime;
    callbacks.startup({blockComponentRegistry: {registerCustomComponent(id, value) {components.block[id] = value;}},
        itemComponentRegistry: {registerCustomComponent(id, value) {components.item[id] = value;}}});
    return {callbacks, deferred, components};
}
export function permutation(id, states = {}) {
    return {type: {id}, getState: key => states[key], withState: (key, value) => permutation(id, {...states, [key]: value})};
}
export function scene({mode = 'Survival'} = {}) {
    const result = {blocks: new Map(), actors: [], writes: [], events: [], held: {typeId: 'vm:upgrade_kit', amount: 1}};
    const key = l => `${l.x},${l.y},${l.z}`;
    const dimension = {
        getBlock(l) {
            if (l.y > 11) {const e = new Error(); e.name = 'LocationOutOfWorldBoundariesError'; throw e;}
            return result.blocks.get(key(l)) ?? block('minecraft:air', {}, l);
        },
        getEntities(query) {
            if (query.type) return result.actors.filter(actor => actor.isValid && actor.typeId === query.type && Math.hypot(
                actor.location.x - query.location.x, actor.location.y - query.location.y, actor.location.z - query.location.z) <= query.maxDistance);
            return result.blockers ?? [];
        },
        spawnEntity: (id, location) => actor(id, location),
        spawnParticle() {},
        playSound() {},
    };
    function block(id, states, location) {
        const value = {typeId: id, location, dimension, permutation: permutation(id, states), get isAir() {return this.typeId === 'minecraft:air';},
            above() {return dimension.getBlock({...location, y: location.y + 1});},
            below() {return dimension.getBlock({...location, y: location.y - 1});},
            setType(typeId) {this.setPermutation(permutation(typeId));},
            setPermutation(p) {
                this.permutation = p; this.typeId = p.type.id; result.blocks.set(key(location), this); result.writes.push(p.type.id);},
        };
        result.blocks.set(key(location), value); return value;
    }
    function actor(id = 'vm:trader_farmer', location = {x: 0.5, y: 11, z: 0.5}) {
        const properties = new Map();
        const value = {typeId: id, location, dimension, isValid: true,
            addEffect() {},
            getDynamicProperty: key => properties.get(key), setDynamicProperty: (key, v) => properties.set(key, v),
            triggerEvent: id => result.events.push(id), remove() {this.isValid = false;},
        };
        result.actors.push(value); return value;
    }
    const player = {getGameMode: () => mode, sendMessage() {}, isSneaking: false,
        inputInfo: {getButtonState: () => result.sneakButton ?? 'Released'},
        getComponent(id) {
            if (id === 'minecraft:equippable') return {getEquipment: () => result.held && {...result.held}, setEquipment: (_, item) => {result.held = item;}};
        }};
    function machine(profession = 'farmer') {
        const id = 'vm:machine_' + profession;
        const base = block(id, {'vm:half': 0}, {x: 0, y: 10, z: 0});
        const head = block(id, {'vm:half': 1}, {x: 0, y: 11, z: 0});
        return {base, head, trader: actor('vm:trader_' + profession)};
    }
    return Object.assign(result, {dimension, player, block, actor, machine});
}
