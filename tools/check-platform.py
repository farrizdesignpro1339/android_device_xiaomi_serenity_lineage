#!/usr/bin/env python3
"""Check that the branch holds the platform bits of its own platform.

The platform branches are siblings. A merge between them drags one branch's
platform bits onto the other, and the result still builds, it just builds the
wrong Android: the shipping API follows the platform, and the framework
compatibility matrix has to name the sepolicy versions that platform can load.

This compares what the tree says against what the branch name promises.

Usage: ./tools/check-platform.py [branch]
"""

import os
import re
import sys

TREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# branch -> (shipping API, newest sepolicy version, the toybox symlink)
EXPECTED = {
    'dev': (36, '202504', False),
    'lineage-22.0': (35, '202404', False),
    'lineage-23.2': (36, '202504', False),
    'lineage-24.0': (36, '202504', True),
}


def read(rel):
    with open(os.path.join(TREE, rel), encoding='utf-8') as handle:
        return handle.read()


def main():
    branch = sys.argv[1] if len(sys.argv) > 1 else None
    if branch is None:
        # the branch that is checked out, or the one the tree is on
        head = os.path.join(TREE, '.git')
        if os.path.isdir(head):
            import subprocess
            branch = subprocess.run(
                ['git', '-C', TREE, 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True).stdout.strip()
        branch = branch or 'dev'
    if branch == 'HEAD':
        branch = 'dev'

    if branch not in EXPECTED:
        print(f'check-platform: {branch} is not a known branch, nothing to '
              f'compare against')
        return 0

    api, matrix, lbracket = EXPECTED[branch]
    problems = []

    platform = read('platform.mk')
    found = re.search(r'PRODUCT_SHIPPING_API_LEVEL\s*:=\s*(\d+)', platform)
    if not found:
        problems.append('platform.mk has no PRODUCT_SHIPPING_API_LEVEL')
    elif int(found.group(1)) != api:
        problems.append(f'platform.mk says shipping API {found.group(1)}, '
                        f'{branch} wants {api}')

    # the API level must not also sit in the product file, where a merge can
    # drop a second copy of it in
    product = read('lineage_serenity.mk')
    if re.search(r'^\s*PRODUCT_SHIPPING_API_LEVEL', product, re.M):
        problems.append('lineage_serenity.mk sets PRODUCT_SHIPPING_API_LEVEL '
                        'as well, it belongs in platform.mk only')

    versions = re.findall(r'sepolicy-version>(\d+)',
                          read('configs/vintf/framework_compatibility_matrix.xml'))
    if versions and versions[-1] != matrix:
        problems.append(f'the compatibility matrix stops at sepolicy '
                        f'{versions[-1]}, {branch} wants {matrix}')

    has_symlink = 'vendor_bin_lbracket' in read('Android.bp')
    if has_symlink != lbracket:
        problems.append(
            'the toybox [ symlink is ' + ('there' if has_symlink else 'missing')
            + f', {branch} wants it ' + ('there' if lbracket else 'missing'))

    if problems:
        print(f'check-platform: {branch} does not hold its own platform bits:')
        for problem in problems:
            print(f'  - {problem}')
        print('\nThis is what a merge between two platform branches does. Take '
              'the files back from the branch that owns them:\n'
              '  git checkout origin/dev -- platform.mk '
              'lineage_serenity.mk \\\n'
              '      configs/vintf/framework_compatibility_matrix.xml\n'
              'and put the toybox symlink back where it belongs.')
        return 1

    print(f'check-platform: {branch} holds its own platform bits '
          f'(API {api}, sepolicy {matrix})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
