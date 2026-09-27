# wsjtx-improved-copr

Fedora Copr packaging for **WSJT-X Improved PLUS** (DG2YCB), Qt6 build.

Upstream: https://sourceforge.net/projects/wsjt-x-improved/

This package **conflicts with** Fedora's official `wsjtx`. Both install `/usr/bin/wsjtx`.

Current pin (fallback if SourceForge cannot be queried; Copr rewrites this at SRPM time):

- Version: `3.2.0`
- PLUS snapshot: `260924`
- Source: Qt6 PLUS tarball (standard GUI, not AL / widescreen)

## Always build the latest PLUS drop

Two pieces keep the Copr package on the newest official Qt6 PLUS tarball:

1. **`.copr/Makefile`** runs `scripts/discover_latest.py` before `rpmbuild -bs`.
   Every Copr rebuild (webhook, `copr-cli build-package`, or the web UI)
   looks up the newest
   `ws-X.Y.Z_YYMMDD_qt6.tgz` on SourceForge and rewrites
   `Version` / `%snapshot` in the spec.
2. **`.github/workflows/watch-upstream.yml`** checks SourceForge daily. When
   DG2YCB publishes a newer drop it commits the new pin here. Copr
   `--webhook-rebuild on` then starts a build.

Manual spec bumps are no longer required for ordinary PLUS updates.

```bash
# See what SourceForge currently publishes
python3 scripts/discover_latest.py --print
```

## Enable (after the Copr project exists)

```bash
sudo dnf copr enable <fas-user>/wsjtx-improved
sudo dnf install wsjtx-improved
```

Remove official `wsjtx` first if it is installed:

```bash
sudo dnf swap wsjtx wsjtx-improved
```

## Hamlib

Build and run against **`xsnrg/hamlib`**, not only Fedora stock hamlib.

- Build-time extra repo: `copr://xsnrg/hamlib` so `hamlib-devel >= 4.7.2` resolves.
- Runtime repo dependency: enabling `wsjtx-improved` also enables `xsnrg/hamlib` for users.

Improved 3.2.0 PLUS is published against Hamlib 4.7.2 (the bundled tarball the spec deletes in `%prep`).

## Create the Copr project

You need `copr-cli` authenticated. There is no `login` subcommand.

```bash
sudo dnf install copr-cli
copr whoami
```

If that fails, open https://copr.fedorainfracloud.org/api/ while signed into FAS, paste the `[copr-cli]` block into `~/.config/copr`, then `chmod 600 ~/.config/copr`. Tokens expire (~180 days). `copr new-api-token` regenerates and **invalidates** the old token.

```bash
copr-cli create wsjtx-improved \
  --chroot fedora-43-x86_64 \
  --chroot fedora-44-x86_64 \
  --chroot fedora-rawhide-x86_64 \
  --repo copr://xsnrg/hamlib \
  --runtime-repo-dependency copr://xsnrg/hamlib \
  --description "WSJT-X Improved PLUS (Qt6), built against xsnrg/hamlib" \
  --instructions "dnf copr enable xsnrg/wsjtx-improved && dnf swap wsjtx wsjtx-improved"

copr-cli add-package-scm wsjtx-improved \
  --name wsjtx-improved \
  --clone-url https://github.com/xsnrg/wsjtx-improved-copr.git \
  --spec wsjtx-improved.spec \
  --type git \
  --method make_srpm \
  --webhook-rebuild on

copr-cli build-package wsjtx-improved --name wsjtx-improved
```

`--webhook-rebuild on` rebuilds when this Git repo changes. Combined with the
daily watcher, that is enough to track new PLUS drops. A rebuild started from
the Copr UI also picks up whatever is newest, even if this repo has not been
bumped yet.

If the Copr project already exists without the hamlib repo:

```bash
copr-cli modify wsjtx-improved \
  --repo copr://xsnrg/hamlib \
  --runtime-repo-dependency copr://xsnrg/hamlib
```

## Notes

- The SourceForge archive is nested: outer `wsjtx-VERSION/` contains `src/wsjtx.tgz`.
- Bundled hamlib is deleted; Copr builds should use `xsnrg/hamlib` (`hamlib-devel >= 4.7.2`).
- LTO is disabled. Fortran is built with `-fallow-argument-mismatch -std=legacy`.
- Standard Improved GUI only (not AL / widescreen). Those are separate upstream tarballs.
- Copr **binary** builds can keep networking off. Source generation (`make_srpm`)
  needs network to query SourceForge and download `Source0`.
