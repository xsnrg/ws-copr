# Copr source method "make_srpm" runs:
#   make -f .copr/Makefile srpm outdir=... spec=...
.PHONY: srpm

srpm:
	dnf -y install rpmdevtools rpm-build
	spectool -g -C "$(dir $(spec))" "$(spec)"
	rpmbuild -bs \
		--define "_sourcedir $(abspath $(dir $(spec)))" \
		--define "_specdir $(abspath $(dir $(spec)))" \
		--define "_srcrpmdir $(outdir)" \
		--define "_rpmdir $(outdir)" \
		--define "_builddir $(outdir)" \
		--define "_buildrootdir $(outdir)" \
		"$(spec)"
