"""Shipped equals generated: run tools/build.py on a scratch copy and fail on any difference."""
import filecmp
import os
from pathlib import Path
import shutil
import subprocess
import sys

MOD = Path(__file__).resolve().parents[1]
WORKSPACE = MOD.parents[1]
SCRATCH = WORKSPACE / 'temp/vending-generated'
COPIED = sorted(p.name for p in MOD.iterdir() if p.is_dir() and (p.name.endswith(('_bp', '_rp')) or p.name == 'localization'))


def diff(a, b, found):
    cmp = filecmp.dircmp(a, b, ignore=['__pycache__'])
    found += [str(Path(a, n).relative_to(MOD)) + ' (missing after build)' for n in cmp.left_only]
    found += [str(Path(b, n).relative_to(SCRATCH / 'mods/vending')) + ' (new after build)' for n in cmp.right_only]
    for name in cmp.common_files:
        if not filecmp.cmp(Path(a, name), Path(b, name), shallow=False):
            found.append(str(Path(a, name).relative_to(MOD)) + ' (differs)')
    for sub in cmp.common_dirs:
        diff(Path(a, sub), Path(b, sub), found)


def main():
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    copy = SCRATCH / 'mods/vending'
    try:
        ignore = shutil.ignore_patterns('__pycache__')
        for name in COPIED + ['tools']:
            shutil.copytree(MOD / name, copy / name, ignore=ignore)
        # tools/localization_support.py imports the workspace tools/localization.py by relative position.
        (SCRATCH / 'tools').mkdir()
        shutil.copy2(WORKSPACE / 'tools/localization.py', SCRATCH / 'tools/localization.py')
        run = subprocess.run([sys.executable, '-B', str(copy / 'tools/build.py')], capture_output=True, text=True)
        if run.returncode:
            print('build.py failed:')
            print(os.linesep.join((run.stdout + run.stderr).splitlines()[-15:]))
            return 1
        found = []
        for name in COPIED:
            diff(MOD / name, copy / name, found)
        if found:
            print('Generated files differ from the shipped ones (run tools/build.py):')
            print('\n'.join('  ' + f for f in found))
            return 1
        print('shipped files equal generated files')
        return 0
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
        try:
            SCRATCH.parent.rmdir()
        except OSError:
            pass


if __name__ == '__main__':
    sys.exit(main())
