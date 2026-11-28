#!/usr/bin/env python3
"""Resolve duplicate module names in the vendor tree at their source.

The generated vendor/xiaomi/serenity/Android.bp derives module names from the
basename of each blob, so two blobs sharing a basename become two modules with
one name and Soong refuses to bootstrap. There are two shapes:

  symlink pair  the stock ROM stores the real file under a platform subdirectory
                (qogirl6/) and a symlink at the plain path. Extraction
                dereferenced the symlink, so both paths became real files and
                both became a module. Fix: drop the plain-path entry and declare
                it with SYMLINK= on the real file, which makes extract-utils
                emit an install_symlink module -- the stock layout, restored.

  real distinct genuinely different files that happen to share a basename
                (camera tuning blobs in separate directories). Fix:
                MAKE_COPY_RULE_ONLY, which turns them into PRODUCT_COPY_FILES
                entries instead of modules. Copy rules are keyed by their full
                destination, so they cannot collide.

Both fixes live in proprietary-files.txt so a regeneration reproduces them.

Run from anywhere. --dry-run reports without writing.
"""

import argparse
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEVICE = HERE.parent
BP = pathlib.Path(os.environ.get(
    'VENDOR_BP',
    '/home/farrizdesignpro/android/vendor/xiaomi/serenity/Android.bp',
))
LIST = DEVICE / 'proprietary-files.txt'
STOCK = pathlib.Path(os.environ.get(
    'STOCK',
    '/home/farrizdesignpro/Unduhan/MIO-KITCHEN-4.1.3-linux/supera17',
))

BP_BLOCK = re.compile(r'^\S.*\{$')
BP_NAME = re.compile(r'^\s*name:\s*"([^"]+)"', re.M)
BP_SRC = re.compile(r'^\s*src:\s*"([^"]+)"', re.M)
BP_SRCS = re.compile(r'^\s*srcs:\s*\[(.*?)\]', re.M | re.S)
BP_ITEM = re.compile(r'"([^"]+)"')


def parse_bp_duplicates(path):
    """Map duplicate module name -> the blob paths its modules read."""
    lines = path.read_text().splitlines()
    blocks, i = [], 0
    while i < len(lines):
        if lines[i] and not lines[i][0].isspace() and lines[i].rstrip().endswith('{'):
            depth, start = 0, i
            while i < len(lines):
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
                if depth == 0:
                    break
            blocks.append('\n'.join(lines[start:i]))
        else:
            i += 1

    by_name = {}
    for block in blocks:
        name = BP_NAME.search(block)
        if not name:
            continue
        srcs = BP_SRC.search(block)
        paths = [srcs.group(1)] if srcs else BP_ITEM.findall(BP_SRCS.search(block).group(1)) if BP_SRCS.search(block) else []
        by_name.setdefault(name.group(1), []).extend(paths)

    return {n: p for n, p in by_name.items() if len(p) > 1}


def classify(blob):
    """What stock holds at this path: 'symlink', 'real', or 'missing'."""
    p = STOCK / blob
    if p.is_symlink():
        return 'symlink', os.readlink(p)
    if p.exists():
        return 'real', None
    return 'missing', None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if not BP.exists():
        sys.exit(f'no vendor bp at {BP}')
    if not STOCK.is_dir():
        sys.exit(f'no stock dump at {STOCK}')

    dups = parse_bp_duplicates(BP)
    raw = LIST.read_text().splitlines()

    # blob path -> line index, for the entries that actually carry a blob
    index = {}
    for i, line in enumerate(raw):
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        index.setdefault(s.split(';')[0].lstrip('-').split('|')[0], i)

    plans = []           # (line_index, new_text) or (line_index, None) to drop
    report = []
    errors = []

    for name, srcs in sorted(dups.items()):
        blobs = [s[len('proprietary/'):] if s.startswith('proprietary/') else s
                 for s in srcs]
        rows = []
        for blob in blobs:
            if blob not in index:
                errors.append(f'{name}: no entry for {blob} in {LIST.name}')
                continue
            kind, target = classify(blob)
            rows.append((blob, index[blob], kind, target))

        if len(rows) != len(blobs):
            continue

        kinds = {r[2] for r in rows}

        if kinds == {'symlink'}:
            errors.append(f'{name}: every path is a symlink in stock, nothing to keep')
            continue

        if 'missing' in kinds:
            missing = [r[0] for r in rows if r[2] == 'missing']
            errors.append(f'{name}: absent from stock: {", ".join(missing)}')
            continue

        if 'symlink' in kinds:
            # symlink pair: keep the real file(s), declare the symlink path(s)
            real = [r for r in rows if r[2] == 'real']
            links = [r for r in rows if r[2] == 'symlink']
            for blob, i, _, target in links:
                resolved = os.path.normpath(
                    os.path.join(os.path.dirname(blob), target))
                if resolved not in {r[0] for r in real}:
                    errors.append(
                        f'{name}: {blob} -> {target} does not resolve to a kept file')
                plans.append((i, None))
            for blob, i, _, _ in real:
                existing = raw[i].strip()
                if 'SYMLINK=' in existing:
                    errors.append(f'{name}: {blob} already declares SYMLINK=')
                    continue
                linkspec = ','.join(r[0] for r in links)
                plans.append((i, f'{existing};SYMLINK={linkspec}'))
            report.append(('symlink', name,
                           [r[0] for r in real], [r[0] for r in links]))
        else:
            # genuinely distinct files sharing a basename
            for blob, i, _, _ in rows:
                existing = raw[i].strip()
                if 'MAKE_COPY_RULE_ONLY' in existing or 'SYMLINK=' in existing:
                    errors.append(f'{name}: {blob} already carries an install arg')
                    continue
                plans.append((i, f'{existing};MAKE_COPY_RULE_ONLY'))
            report.append(('copy-rule', name, [r[0] for r in rows], []))

    if errors:
        print('REFUSING TO WRITE:')
        for e in errors:
            print(f'  - {e}')
        return 1

    # A line must not be planned twice (two groups claiming one entry).
    seen = {}
    for i, _ in plans:
        if i in seen:
            errors.append(f'line {i + 1} claimed by two groups')
        seen[i] = True
    if errors:
        print('REFUSING TO WRITE:')
        for e in errors:
            print(f'  - {e}')
        return 1

    out = list(raw)
    for i, text in plans:
        if text is None:
            out[i] = None
        else:
            out[i] = text

    print(f'{len(dups)} duplicate module names, {len(plans)} line edits\n')
    for kind, name, real, links in report:
        if kind == 'symlink':
            print(f'  [symlink] {name}')
            print(f'            keep    {", ".join(real)}')
            print(f'            symlink {", ".join(links)}')
        else:
            print(f'  [copy]    {name}')
            for b in real:
                print(f'            {b}')
    print()

    if args.dry_run:
        print('dry run, nothing written')
        return 0

    kept = [l for l in out if l is not None]
    LIST.write_text('\n'.join(kept) + '\n')
    print(f'wrote {LIST} ({len(raw)} -> {len(kept)} lines)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
