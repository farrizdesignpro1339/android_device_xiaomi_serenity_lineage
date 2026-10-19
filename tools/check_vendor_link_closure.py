#!/usr/bin/env python3
"""Is every library the vendor blobs need still satisfied after the removals?

For every DT_NEEDED edge of every ELF we ship: shipped means a file in the
vendor repo, platform means present in the stock system image, MISSING means
neither, which is the only case that breaks at runtime.

Usage: check_vendor_link_closure.py [--needed /path/to/needed.tsv]
"""

import os
import re
import subprocess
import sys

# Paths come from the environment so the same script works on any checkout.
#   SERENITY_TREE        this device tree, the parent of tools/
#   SERENITY_VENDOR_REPO the vendor repo, the parent of proprietary/
TREE = os.environ.get('SERENITY_TREE') or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
VENDOR_REPO = os.environ.get('SERENITY_VENDOR_REPO') or os.path.join(
    os.environ.get('ANDROID_BUILD_TOP', os.path.join(TREE, '..')),
    'vendor/xiaomi/serenity')

# An extracted stock tree, for the blobs the vendor repo does not carry
STOCK_SYSTEM = os.environ.get('SERENITY_STOCK') or '/path/to/extracted/stock/tree'
DEFAULT_NEEDED = '/tmp/needed.tsv'


def vendored_libs():
    """Basenames of every ELF we install into the vendor image."""
    out = set()
    for root, _, files in os.walk(f'{VENDOR_REPO}/proprietary'):
        for f in files:
            if '.so' in f or '/' in f:
                pass
        for f in files:
            p = os.path.join(root, f)
            if not (f.endswith('.so') or '.so.' in f):
                continue
            try:
                with open(p, 'rb') as fh:
                    if fh.read(4) != b'\x7fELF':
                        continue
            except OSError:
                continue
            out.add(f)
    return out


def stock_libs():
    out = set()
    for root, _, files in os.walk(STOCK_SYSTEM):
        for f in files:
            if f.endswith('.so') or '.so.' in f:
                out.add(f)
    return out


def needed_edges(path):
    if os.path.exists(path):
        edges = []
        for line in open(path):
            if line.startswith('#'):
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) == 2:
                edges.append(tuple(parts))
        return edges, 'cached readelf'
    edges = []
    for root, _, files in os.walk(f'{VENDOR_REPO}/proprietary'):
        for f in files:
            p = os.path.join(root, f)
            if not (f.endswith('.so') or '.so.' in f):
                continue
            r = subprocess.run(['readelf', '-d', p], capture_output=True, text=True)
            if r.returncode != 0:
                continue
            for line in r.stdout.splitlines():
                if 'NEEDED' in line and '[' in line:
                    edges.append((p, line.split('[')[1].split(']')[0]))
    return edges, 'fresh readelf'


def main():
    needed_path = DEFAULT_NEEDED
    if '--needed' in sys.argv:
        needed_path = sys.argv[sys.argv.index('--needed') + 1]

    edges, how = needed_edges(needed_path)
    vendor = vendored_libs()
    platform = stock_libs()

    live = 0
    shipped = platform_hit = 0
    missing = {}
    for src, dep in edges:
        # the cached table stores paths relative to the vendor repo
        if not os.path.isabs(src):
            src = os.path.join(VENDOR_REPO, src)
        if not os.path.exists(src):
            continue  # one of the removed blobs
        live += 1
        if dep in vendor:
            shipped += 1
        elif dep in platform:
            platform_hit += 1
        else:
            missing.setdefault(dep, set()).add(os.path.basename(src))

    print(f'needed edges      : {len(edges)} ({how})')
    print(f'live edges        : {live} (from files still on disk)')
    print(f'satisfied in vendor: {shipped}')
    print(f'satisfied in stock system image: {platform_hit}')
    print(f'unresolved        : {len(missing)}')
    for dep in sorted(missing):
        who = sorted(missing[dep])[:4]
        print(f'  MISSING {dep}   needed by {", ".join(who)}')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
