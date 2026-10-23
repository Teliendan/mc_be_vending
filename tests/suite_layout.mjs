import assert from 'node:assert/strict';
import {readFileSync, readdirSync} from 'node:fs';
const manifest = JSON.parse(readFileSync(new URL('./suites.json', import.meta.url), 'utf8'));
const runners = new Set(Object.values(manifest.suites).flat());
for (const file of readdirSync(new URL('./', import.meta.url)).filter(name => /\.(mjs|js|py)$/.test(name))) {
    assert.ok(file === 'run.mjs' || runners.has(file) || file in manifest.support_files, `${file}: register runner`);
    if (!runners.has(file)) continue;
    const source = readFileSync(new URL(file, import.meta.url), 'utf8');
    for (const [, dependency] of source.matchAll(/(?:from\s*|import\s*(?:\(\s*)?)["']\.\/([^"']+)["']/g)) {
        assert.ok(!runners.has(dependency) && dependency !== 'run.mjs', `${file}: do not import another suite`);
    }
}
assert.equal(runners.has('run.mjs'), false);
console.log(`ok   ${runners.size} independent registered runners`);
