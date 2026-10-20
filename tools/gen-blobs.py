#!/usr/bin/env python3
"""Walk an extracted stock tree and write the extract-utils blob list.

The stock tree is the unpacked vendor and odm partitions of a factory ROM,
extracted once with erofsfuse or MIO Kitchen. Paths are written relative to
that tree, which is what extract-files.py expects.

Usage:
    ./tools/gen-blobs.py <stock-tree> [-o proprietary-files.txt]

The stock tree must contain the vendor and odm directories.
"""

import argparse
import os
import sys
from collections import defaultdict

try:
    from elftools.elf.elffile import ELFFile
except ImportError:
    ELFFile = None

# The platform installs these at the same vendor path, so shipping the OEM
# copy produces a duplicate install. toybox_vendor is in this list because
# device.mk declares the platform package of the same name, and the stock tree
# calls its own copy that too
PLATFORM_TOOLS = {
    'awk',
    'dumpsys',
    'logwrapper',
    'sh',
    'toybox',
    'toybox_vendor',
}

# Directories never carried as blobs: the kernel modules live in
# BOARD_KERNEL_MODULES, the policy in sepolicy/, the rest is build metadata.
SKIP_DIRS = {
    'selinux',
    'modules',
    'sysdeps',
    'ld.config.txt',
    'ld.config.28.txt',
    'ld.config.29.txt',
}

# VINTF metadata cannot be installed by copying the file, the build refuses
# it: "VINTF metadata found in PRODUCT_COPY_FILES, use ODM_MANIFEST_FILE
# instead". The manifest and the compatibility matrix are declared in
# BoardConfig.mk and live in the device tree, so they are left out here. The
# fragments under etc/vintf/manifest/ are ordinary files and stay.
VINTF_METADATA = (
    'vendor/etc/vintf/manifest.xml',
    'vendor/etc/vintf/compatibility_matrix.xml',
    'odm/etc/vintf/manifest.xml',
)

# Symlinks that the platform owns and therefore ships itself. The toybox and
# toolbox symlink farms come from toybox_vendor, and the module loader path is
# the install_symlink the device tree declares by hand.
SKIP_SYMLINKS = ('toybox_vendor', 'toolbox', '/vendor_dlkm/lib/modules')

# Under vendor/firmware the camera tuning data carries a backup of every sensor
# the platform has ever shipped and a Simulation directory for the tuning
# tool. Neither is read at runtime and together they are most of the partition,
# so both are dropped. The sensor directories themselves stay, the phone only
# reads the ones its own sensor is configured for.
FIRMWARE_SKIP = {
    'backup',
    'Simulation',
}

# Extensions worth carrying from etc. Anything else there is either a symlink
# farm target, a NOTICE, or a text file the build already owns.
ETC_KEEP_EXT = {
    '.xml', '.conf', '.cfg', '.ini', '.json', '.jar', '.apk', '.txt', '.prop',
    '.db', '.prop', '.rc', '.csv', '.dat',
}

GROUPS = [
    ('vendor', 'firmware', 'Modem, WLAN, GNSS and DSP firmware'),
    ('vendor', 'framework', 'Vendor jars and apks'),
    ('vendor', 'overlay', 'Runtime resource overlays'),
    ('vendor', 'bin', 'Vendor services, minus the tools the platform ships'),
    ('vendor', 'lib', 'Vendor libraries, 32 bit'),
    ('vendor', 'lib64', 'Vendor libraries, 64 bit'),
    ('vendor', 'etc', 'Vendor configs'),
    ('odm', 'firmware', 'ODM firmware'),
    ('odm', 'logo', 'Boot and charging logos'),
    ('odm', 'bin', 'ODM services'),
    ('odm', 'lib', 'ODM libraries, 32 bit'),
    ('odm', 'lib64', 'ODM libraries, 64 bit'),
    ('odm', 'etc', 'ODM configs'),
    ('odm', 'overlay', 'ODM runtime overlays'),
]


def keep_file(rel):
    """Decide whether one stock file belongs in the blob list."""
    parts = rel.split('/')
    top = parts[0]
    sub = parts[1] if len(parts) > 2 else ''
    name = parts[-1]

    if name.startswith('NOTICE'):
        return False
    if rel in VINTF_METADATA:
        return False
    # The build installs its own build.prop into these partitions, from
    # vendor.prop and odm.prop. Shipping the stock one would be a second
    # copy at the same path.
    if rel in ('vendor/build.prop', 'odm/etc/build.prop'):
        return False
    if sub == 'firmware' and top == 'vendor':
        for skip in FIRMWARE_SKIP:
            if f'/{skip}/' in '/' + rel:
                return False
    for skip in SKIP_DIRS:
        if skip in parts:
            return False
    if top == 'vendor' and sub == 'bin' and name in PLATFORM_TOOLS:
        return False
    if sub == 'etc' or (len(parts) > 2 and parts[1] == 'etc'):
        ext = os.path.splitext(name)[1]
        if ext not in ETC_KEEP_EXT and name not in ('build.prop',):
            return False
    return True


def resolve(root, path, depth=0):
    """Follow a symlink chain to the real file, or None if it leaves the tree."""
    if depth > 8:
        return None
    target = os.readlink(path)
    if os.path.isabs(target):
        return None
    nxt = os.path.normpath(os.path.join(os.path.dirname(path), target))
    if not nxt.startswith(root + os.sep) or not os.path.isfile(nxt):
        return None
    if os.path.islink(nxt):
        return resolve(root, nxt, depth + 1)
    return os.path.relpath(nxt, root)


def symlink_map(root):
    """real blob path -> the symlink paths that have to point at it."""
    out = defaultdict(list)
    for top in ('vendor', 'odm'):
        base = os.path.join(root, top)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for name in filenames:
                full = os.path.join(dirpath, name)
                if not os.path.islink(full):
                    continue
                rel = os.path.relpath(full, root)
                if os.readlink(full) in SKIP_SYMLINKS:
                    continue
                real = resolve(root, full)
                if real is None:
                    # Points outside the tree, install_symlink has to make it
                    print(f'  manual symlink, not a blob: {rel} -> '
                          f'{os.readlink(full)}')
                    continue
                out[real].append(rel)
    return out


def soname(path):
    """DT_SONAME of an ELF file, or None when there is none."""
    if ELFFile is None:
        return None
    try:
        with open(path, 'rb') as handle:
            elf = ELFFile(handle)
            for section in elf.iter_sections():
                if section.header.get('sh_type') != 'SHT_DYNAMIC':
                    continue
                for tag in section.iter_tags():
                    if tag.entry.d_tag == 'DT_SONAME':
                        return getattr(tag, 'soname', None)
    except Exception:
        return None
    return None


def soname_map(root, candidates):
    """blob path -> the extra symlink its DT_SONAME needs.

    A library whose DT_SONAME differs from its file name breaks the loader: the
    libraries that need it look the SONAME up, find nothing, and the process
    dies at startup. The stock tree has seven like this and carries no symlink
    for them, so the link has to be made here.
    """
    out = defaultdict(list)
    if ELFFile is None:
        print('  pyelftools is missing, no SONAME symlinks were generated')
        return out
    added = 0
    for rel in candidates:
        name = os.path.basename(rel)
        so = soname(os.path.join(root, rel))
        if not so or so == name:
            continue
        link = os.path.join(os.path.dirname(rel), so)
        if link in candidates or os.path.exists(os.path.join(root, link)):
            continue
        out[rel].append(link)
        added += 1
    print(f'{added} SONAME symlinks')
    return out


def collect(root, top, sub):
    base = os.path.join(root, top, sub)
    if not os.path.isdir(base):
        return []
    out = []
    for dirpath, _dirnames, filenames in os.walk(base):
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, root)
            if keep_file(rel):
                out.append(rel)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stock_tree')
    ap.add_argument('-o', '--output', default='proprietary-files.txt')
    ap.add_argument('-x', '--exclude',
                    help='file of stock paths to leave out, one per line')
    args = ap.parse_args()

    excluded = set()
    if args.exclude:
        with open(args.exclude, encoding='utf-8') as handle:
            excluded = {line.strip() for line in handle
                        if line.strip() and not line.startswith('#')}
        print(f'excluding {len(excluded)} paths')

    root = os.path.abspath(args.stock_tree)
    if not os.path.isdir(os.path.join(root, 'vendor')):
        sys.exit(f'{root} has no vendor directory, is that the stock tree?')

    links = symlink_map(root)
    print(f'symlink targets: {len(links)}')
    all_blobs = []
    for top, sub, _comment in GROUPS:
        all_blobs.extend(collect(root, top, sub))
    for blob, extra in soname_map(root, all_blobs).items():
        links[blob].extend(extra)

    total = 0
    linked = 0
    with open(args.output, 'w') as out:
        out.write('# Unpinned blobs, generated by tools/gen-blobs.py\n')
        out.write('# Source: Redmi A5 / POCO C71 (serenity), Unisoc T7250\n')
        out.write('# SYMLINK names the extra paths that have to point at the\n')
        out.write('# blob, the way extract-utils reads it\n\n')
        for top, sub, comment in GROUPS:
            files = collect(root, top, sub)
            if not files:
                continue
            out.write(f'# {comment}\n')
            for rel in files:
                if rel in excluded:
                    continue
                extra = links.get(rel)
                if extra:
                    out.write(rel + ';SYMLINK=' + ','.join(sorted(extra)) + '\n')
                    linked += len(extra)
                else:
                    out.write(rel + '\n')
            out.write('\n')
            kept = len(files) - len([f for f in files if f in excluded])
            total += kept
            print(f'{top}/{sub}: {kept}')

    print(f'total {total} blobs, {linked} symlinks -> {args.output}')


if __name__ == '__main__':
    main()