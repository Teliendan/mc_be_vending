import { readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const files = readdirSync(new URL(".", import.meta.url)).filter(name => name.endsWith(".test.mjs")).sort();
const result = spawnSync(process.execPath, ["--test", ...files.map(name => `tests/${name}`)], {
    cwd: fileURLToPath(new URL("..", import.meta.url)), stdio: "inherit", timeout: 30000,
});
if (result.error) console.error(result.error.message);
process.exitCode = result.status ?? 1;
