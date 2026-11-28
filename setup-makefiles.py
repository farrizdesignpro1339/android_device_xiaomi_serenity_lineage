#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: The Serenity Project
# SPDX-License-Identifier: Apache-2.0
#
# Regenerate the vendor makefiles, then drop the prebuilt prefer flags. A
# prebuilt that claims an AOSP module of the same name on another partition is
# what Soong rejects, and where the platform builds a vendor variant that copy
# is the right one anyway. scratch/preflight.py checks the result.
#

import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
candidates = [
    pathlib.Path.home() / 'android/vendor/xiaomi/serenity/Android.bp',
    HERE.resolve() / '../../../vendor/xiaomi/serenity/Android.bp',
    pathlib.Path.cwd() / '../../../vendor/xiaomi/serenity/Android.bp',
]
VENDOR_BP = next((p.resolve() for p in candidates if p.resolve().exists()), candidates[0])
PREFER = re.compile(r'^    prefer: true,\n', re.M)

# libmt_trusty is a prebuilt built against keymint-V3. Its generated shared_libs
# would drag in lib_android_keymaster_keymint_utils (keymint-V4) and
# libkeymint_support (keymint-V5), so soong aborts with "depends on multiple
# versions of the same aidl_interface". There is no suppression flag; drop those
# two propagated entries from this module only. The ELF NEEDED entries still
# satisfy runtime; libkeymint_support / lib_android_keymaster_keymint_utils /
# keymint-V4/V5-ndk are installed independently. proprietary-files.txt has no
# field to express this, so it is applied after regeneration.
LIBMT_TRUSTY = re.compile(
    r'cc_prebuilt_library_shared \{\n    name: "libmt_trusty".*?\n\}\n', re.S
)
KEYMINT_CONFLICT = re.compile(
    r'^\s+"lib_android_keymaster_keymint_utils",\n|^\s+"libkeymint_support",\n',
    re.M,
)

subprocess.run(
    [str((HERE / 'extract-files.py').resolve()), '--regenerate_makefiles'],
    check=True,
)

bp = VENDOR_BP.resolve()
text = bp.read_text()
text, count = PREFER.subn('', text)
text = LIBMT_TRUSTY.sub(lambda m: KEYMINT_CONFLICT.sub('', m.group(0)), text)
bp.write_text(text)

if count:
    print(f'dropped {count} prefer: true lines from {bp}')
