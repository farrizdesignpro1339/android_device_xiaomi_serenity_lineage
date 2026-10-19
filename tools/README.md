# tools

Nothing here takes arguments you have to look up first. `config.py` resolves
the paths, from the environment when it is set and from where the tree sits
when it is not, and the Makefile in the tree root drives everything.

```bash
make paths      # what got resolved
make all        # regenerate everything, in order
make check      # the four checkers
```

Overriding a path, only needed when the guess is wrong:

| Variable | What it points at |
| :--- | :--- |
| `SERENITY_TREE` | this tree |
| `SERENITY_VENDOR_REPO` | the vendor repo, the one with `proprietary/` |
| `SERENITY_STOCK` | an extracted stock tree, `vendor/` and `odm/` unpacked |
| `SERENITY_AOSP` | a LineageOS checkout, only `emit.py` reads it |
| `SERENITY_PLATFORM_VINTF` | a `system/etc/vintf` to compare the manifest to |

## What each one does

| Tool | Task | Output |
| :--- | :--- | :--- |
| `gen-overlay-decls.py` | pick the overlays a LineageOS build can use, and the apks that must not ship | `configs/overlay/overlay-decls.xml`, `overlay-exclude.txt` |
| `gen-blobs.py` | walk the stock tree, drop what the build owns, follow symlinks and SONAMEs | `proprietary-files.txt` |
| `gen-props.py` | copy the stock build props, minus the keys the platform owns | `vendor.prop`, `odm.prop` |
| `make-vendor-repo.py` | build the vendor repo from the blob list without extract-utils | `../android_vendor_xiaomi_serenity_lineage` |
| `genpolicy.py` | report what the stock policy needs, writes nothing | stdout |
| `emit.py` | write the sepolicy from the stock CIL, in classic .te form | `sepolicy/vendor/` |

## The checkers

| Tool | What it catches |
| :--- | :--- |
| `check_policy.py` | a name referenced but never declared, a name declared twice here or against the platform, a label pointing at nothing |
| `preflight.py` | a module in both repos, a copy source that does not exist, a blob that lands nowhere, a symlink that resolves to nothing |
| `elf_audit.py` | a library with no DT_SONAME, a SONAME nothing provides, an unresolved private dependency |
| `vintf_coverage.py` | a HAL the vendor declares that no platform matrix covers |

`preflight.py` and `check_policy.py` compare against the platform policy, which
needs `SERENITY_AOSP`. Without it they report the difference as a note rather
than a failure, and the notes are the ones to recheck after a checkout exists.

`service_policy.py` and `check_vendor_link_closure.py` need more than the stock
tree to say anything: the first wants the platform policy, the second a `needed`
table from a running device.
