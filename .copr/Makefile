# Copr source method "make_srpm" runs:
#   make -f .copr/Makefile srpm outdir=... spec=...
# This target resolves the newest Qt6 PLUS tarball before rpmbuild.
.PHONY: srpm

REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)

srpm:
	dnf -y install rpmdevtools rpm-build python3 curl
	python3 "$(REPO_ROOT)/scripts/discover_latest.py" --update-spec "$(spec)"
	spectool -g -C "$(dir $(spec))" "$(spec)"
	rpmbuild -bs \
		--define "_sourcedir $(abspath $(dir $(spec)))" \
		--define "_specdir $(abspath $(dir $(spec)))" \
		--define "_srcrpmdir $(outdir)" \
		--define "_rpmdir $(outdir)" \
		--define "_builddir $(outdir)" \
		--define "_buildrootdir $(outdir)" \
		"$(spec)"
