#
# SPDX-FileCopyrightText: The Redmi A5 (serenity) Project
# SPDX-License-Identifier: Apache-2.0
#
# Everything the tools need is resolved by tools/config.py, so nothing has to be
# passed on the command line unless the default guess is wrong. Override with
# SERENITY_STOCK, SERENITY_VENDOR_REPO, SERENITY_AOSP or SERENITY_TREE.
#
#   make paths     what was resolved, and from where
#   make all       regenerate the blob list, the properties, the overlays,
#                  the vendor repo and the sepolicy, in that order
#   make check     run the four checkers
#

PY     := python3
TOOLS  := tools
# The paths come from tools/config.py, so a wrong guess is fixed there or with
# an environment variable, never by editing this file
STOCK  := $(shell $(PY) -c "import sys;sys.path.insert(0,'$(TOOLS)');import config;print(config.STOCK or '')")
VENDOR := $(shell $(PY) -c "import sys;sys.path.insert(0,'$(TOOLS)');import config;print(config.VENDOR_REPO or '')")

.PHONY: all paths blobs overlays props vendor policy check \
        check-policy check-preflight check-elf check-vintf clean

all: overlays blobs props vendor policy

paths:
	@$(PY) -c "import sys; sys.path.insert(0, '$(TOOLS)'); import config; print(config.describe())"

# The overlay list is read by gen-blobs.py, so it has to come first
overlays:
	$(PY) $(TOOLS)/gen-overlay-decls.py "$(STOCK)"

blobs:
	$(PY) $(TOOLS)/gen-blobs.py "$(STOCK)" -x configs/overlay/overlay-exclude.txt

props:
	$(PY) $(TOOLS)/gen-props.py "$(STOCK)"

vendor:
	$(PY) $(TOOLS)/make-vendor-repo.py "$(STOCK)" "$(VENDOR)" --prune

policy:
	$(PY) $(TOOLS)/emit.py

check: check-policy check-preflight check-elf check-vintf

check-policy:
	$(PY) $(TOOLS)/check_policy.py

check-preflight:
	$(PY) $(TOOLS)/preflight.py

check-elf:
	$(PY) $(TOOLS)/elf_audit.py

check-vintf:
	$(PY) $(TOOLS)/vintf_coverage.py

clean:
	rm -rf sepolicy/vendor
