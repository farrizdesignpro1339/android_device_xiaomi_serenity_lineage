# Device tree for the Redmi A5 / POCO C71 (serenity)

The Redmi A5 / POCO C71 (codenamed "serenity") is a budget smartphone from Xiaomi.

## Device specifications

| Basic                   | Spec                                                        |
| ----------------------- | :---------------------------------------------------------- |
| SoC                     | Unisoc T7250 (12 nm)                                        |
| CPU                     | Octa-core (up to 1.8 GHz; 2× Cortex-A75 & 6× Cortex-A55)   |
| GPU                     | Mali-G57 MP1                                                |
| Memory                  | 4/6 GB LPDDR4X                                                |
| Shipped Android version | 15 Upgradeable to Android 17                                |
| Storage                 | 64/128 GB eMMC 5.1                                          |
| MicroSD                 | microSDXC                                                   |
| Battery                 | Non-removable Li-Polymer 5200 mAh                           |
| Dimensions              | 171.7 x 77.8 x 8.2 mm                                       |
| Display                 | IPS LCD 120 Hz, 6.9 inches, 720 x 1640 pixels               |
| Rear Camera             | 32 MP                                                       |
| Front Camera            | 8 MP                                                        |

## Device Picture

![Redmi A5](docs/serenity.png)

## Extracting the blobs

`proprietary-files.txt` is the list and the vendor repo is its generated output.
Both need a LineageOS checkout, with this tree at `device/xiaomi/serenity` and the
blobs at `vendor/xiaomi/serenity`:

    ./extract-files.py
    ./setup-makefiles.py

Soong only accepts letters, digits and `_ . @ + -` in a module name, and
`build/tools/extract-utils` builds one straight from the path, so
`vendor/bin/[` becomes `vendor_bin_[`, which Soong rejects. File names have the
same problem: `lib{bar}.so` would be named `lib{bar}`.
`docs/extract-utils-module-name.patch` covers both, leaving legal names alone.

The patch is lost on every `repo sync`, because `build/tools/extract-utils`
belongs to the LineageOS checkout and not to either repo, so the one symlink it
affects is declared by hand in `Android.bp`. The blob list no longer carries
that entry, so a regeneration never competes with it.
