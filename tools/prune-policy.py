#!/usr/bin/env python3
"""Drop the declarations the platform already provides.

The sepolicy in this tree was generated from the stock policy without a
platform checkout at hand, so every type the platform declares was declared
here as well. The build refuses that:

    type hal_audio_default, domain
        already declared by the platform

This removes our declaration of anything the platform already has and keeps
the rules that go with it. The domain is not touched when the platform does
not have it, and the init_daemon_domain call goes away together with the
type, because the platform brings its own.

Usage:
    ./tools/prune-policy.py [--dry-run]
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402

TREE = config.TREE
POLICY = os.path.join(TREE, 'sepolicy', 'vendor')

# type X, a, b;      attribute X;      typeattribute X Y;
DECL = re.compile(r'^\s*(type|attribute|typeattribute)\s+([A-Za-z0-9_]+)')
DAEMON = re.compile(r'^\s*init_daemon_domain\(\s*([A-Za-z0-9_]+)')
DOMAIN = re.compile(r'^\s*type\s+([A-Za-z0-9_]+)\s*,\s*[^;]*\bdomain\b')


def platform_types():
    """Every type and attribute the platform declares, and its domains."""
    names, domains = set(), set()
    if not config.AOSP_POLICY:
        return names, domains

    roots = [os.path.join(config.AOSP_POLICY, 'vendor'),
             os.path.join(config.AOSP_POLICY, 'private'),
             os.path.join(config.AOSP_POLICY, 'public')]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                if not name.endswith('.te'):
                    continue
                with open(os.path.join(dirpath, name), encoding='utf-8',
                          errors='ignore') as handle:
                    for line in handle:
                        match = DECL.match(line)
                        if match:
                            names.add(match.group(2))
                        match = DOMAIN.match(line)
                        if match:
                            domains.add(match.group(1))

    # the stable API the vendor may use, one directory per level
    api = os.path.join(config.AOSP_POLICY, 'prebuilts', 'api')
    if os.path.isdir(api):
        levels = sorted(os.listdir(api))
        for level in levels:
            for name in sorted(os.listdir(os.path.join(api, level))):
                if not name.endswith('.cil'):
                    continue
                with open(os.path.join(api, level, name), encoding='utf-8',
                          errors='ignore') as handle:
                    for line in handle:
                        match = re.match(
                            r'\((?:type|typeattribute)\s+([A-Za-z0-9_]+)', line)
                        if match:
                            names.add(match.group(1).split('_')[0] if
                                      re.match(r'^[A-Za-z0-9_]+_\d+_\d+$',
                                               match.group(1)) else
                                      match.group(1))
    return names, domains


def prune(names, domains, dry):
    removed = []
    for entry in sorted(os.listdir(POLICY)):
        if not entry.endswith('.te'):
            continue
        path = os.path.join(POLICY, entry)
        with open(path, encoding='utf-8') as handle:
            lines = handle.readlines()

        out = []
        changed = False
        for line in lines:
            match = DECL.match(line)
            if match and match.group(2) in names:
                removed.append((entry, match.group(2), 'declaration'))
                changed = True
                continue
            match = DAEMON.match(line)
            if match and match.group(1) in domains:
                removed.append((entry, match.group(1), 'init_daemon_domain'))
                changed = True
                continue
            out.append(line)

        if changed and not dry:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.writelines(out)

    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if not config.AOSP_POLICY:
        raise SystemExit(
            'no platform policy found.\n'
            '  set SERENITY_AOSP to the checkout, the one with system/sepolicy '
            'in it.')

    names, domains = platform_types()
    print(f'platform declares {len(names)} types, {len(domains)} of them domains')

    removed = prune(names, domains, args.dry_run)
    print(f'{len(removed)} declarations removed'
          f'{"" if args.dry_run else " from " + POLICY}')

    by_name = {}
    for entry, name, kind in removed:
        by_name.setdefault(name, []).append(f'{entry} ({kind})')
    for name in sorted(by_name)[:40]:
        print(f'  {name}: {", ".join(by_name[name])}')
    if len(by_name) > 40:
        print(f'  ... and {len(by_name) - 40} more')

    if args.dry_run:
        print('\nnothing was written, drop --dry-run to apply')
    return 0


if __name__ == '__main__':
    sys.exit(main())
