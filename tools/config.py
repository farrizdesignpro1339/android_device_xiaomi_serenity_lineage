#!/usr/bin/env python3
"""Where everything is, for the tools in this directory.

Every tool used to read a different set of hard coded paths, which meant nothing
ran without a wall of environment variables. The paths are resolved here once:
an environment variable wins, otherwise the obvious place is searched, and if
that fails the tool says which variable to set instead of failing obscurely.

    SERENITY_TREE         this device tree, default the parent of tools/
    SERENITY_VENDOR_REPO  the vendor repo, default a sibling of the tree
    SERENITY_STOCK        an extracted stock tree, searched for
    SERENITY_AOSP         a LineageOS checkout, only the sepolicy tools need it
    SERENITY_PLATFORM_VINTF  a system/etc/vintf to compare the manifest against
"""

import glob
import os

TOOLS = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.abspath(os.environ.get('SERENITY_TREE')
                       or os.path.dirname(TOOLS))


def _sibling(pattern):
    """A sibling of the tree, so the two repos sit next to each other."""
    home = os.path.dirname(TREE)
    hits = sorted(glob.glob(os.path.join(home, pattern)))
    return os.path.abspath(hits[0]) if hits else None


def _looks_like_stock(path):
    """The two selinux files only an unpacked vendor partition has.

    build.prop is not a marker: a vendor partition keeps it at the root while
    odm keeps it under etc/, and which one MIO Kitchen leaves behind depends on
    the tool.
    """
    return all(os.path.isfile(os.path.join(path, rel)) for rel in (
        'vendor/etc/selinux/vendor_sepolicy.cil',
        'vendor/etc/selinux/plat_pub_versioned.cil',
    ))


def find_stock():
    """An extracted stock tree, either given or found next to the tree."""
    given = os.environ.get('SERENITY_STOCK')
    if given:
        return os.path.abspath(given)

    roots = [os.path.dirname(TREE),
             os.path.join(os.path.dirname(TREE), 'Unduhan')]
    # MIO Kitchen unpacks a fastboot ROM into a directory next to its own
    patterns = ('MIO-KITCHEN*/super*', 'Unduhan/MIO-KITCHEN*/super*',
                'Unduhan/MIO-KITCHEN*/*', '*/*stock*')
    for root in roots:
        for pattern in patterns:
            for hit in sorted(glob.glob(os.path.join(root, pattern))):
                if os.path.isdir(hit) and _looks_like_stock(hit):
                    return os.path.abspath(hit)
    return None


def _checkout(name):
    """A LineageOS or AOSP checkout, if one sits next to the tree."""
    given = os.environ.get(name)
    if given:
        return os.path.abspath(given)
    for candidate in (os.environ.get('ANDROID_BUILD_TOP'),
                      os.path.join(os.path.dirname(TREE), 'lineage'),
                      os.path.join(os.path.dirname(TREE), 'LineageOS'),
                      os.path.join(os.path.dirname(TREE), 'aosp')):
        if candidate and os.path.isfile(os.path.join(candidate, 'build/envsetup.sh')):
            return os.path.abspath(candidate)
    return None


STOCK = find_stock()
VENDOR_REPO = (os.path.abspath(os.environ['SERENITY_VENDOR_REPO'])
               if os.environ.get('SERENITY_VENDOR_REPO')
               else _sibling('android_vendor_xiaomi_*'))
AOSP = _checkout('SERENITY_AOSP')
PLATFORM_VINTF = (os.environ.get('SERENITY_PLATFORM_VINTF')
                  or (os.path.join(STOCK, 'system/etc/vintf') if STOCK else None))

# The stock system is unpacked either flat or one level deeper, depending on
# whether the tool that unpacked it kept the partition directory.
if PLATFORM_VINTF and not os.path.isdir(PLATFORM_VINTF):
    nested = os.path.join(STOCK, 'system/system/etc/vintf') if STOCK else ''
    if nested and os.path.isdir(nested):
        PLATFORM_VINTF = nested


def need(name, value, hint):
    """Return a path, or say what to set and stop."""
    if value:
        return value
    raise SystemExit(
        f'config: {name} is not set and could not be found.\n'
        f'  Set {hint}, or run from a tree that sits next to the stock dump.')


def describe():
    """A short report, for the Makefile and for the README."""
    rows = (('tree', TREE), ('vendor repo', VENDOR_REPO), ('stock tree', STOCK),
            ('AOSP checkout', AOSP), ('platform vintf', PLATFORM_VINTF))
    return '\n'.join(f'  {label:<13} {value or "(not found)"}'
                     for label, value in rows)
