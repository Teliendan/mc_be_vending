"""Regenerate every generated JSON file of the mod, in the one order that works.

    python tools/build.py          # the six JSON generators
    python tools/build.py --art    # also the texture and pack icon generators

Order matters: gen_machine_models.py rewrites three shared RP files with villager
entries only, and gen_extra_machines.py (wandering, shulker) reads the farmer
machine's generated block and entity files, so it must come after both.
"""
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

JSON_STEPS = [
    ['gen_machine_blocks.py', '--force'],
    ['gen_machine_entities.py', '--force'],
    ['gen_machine_recipes.py', '--force'],
    ['gen_machine_models.py', '--force'],
    ['gen_extra_machines.py'],
    ['gen_trade_tables.py', '--write'],
]
ART_STEPS = [
    ['make_machine_textures.py', '--force'],
    ['vm_make_upgraded_textures.py'],
    ['make_pack_icon.py'],
]


def main(argv):
    steps = JSON_STEPS + (ART_STEPS if '--art' in argv else [])
    for step in steps:
        print('build:', ' '.join(step), flush=True)
        subprocess.run([sys.executable, '-B', str(TOOLS / step[0]), *step[1:]], check=True)


if __name__ == '__main__':
    main(sys.argv[1:])
