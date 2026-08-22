# wsjtx-improved-copr

Fedora Copr packaging for **WSJT-X Improved PLUS** (DG2YCB), Qt6 build.

Upstream: https://sourceforge.net/projects/wsjt-x-improved/

This package **conflicts with** Fedora's official `wsjtx`. Both install `/usr/bin/wsjtx`.

Current pin:

- Version: `3.2.0`
- PLUS snapshot: `260818`
- Source: Qt6 PLUS tarball

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

`--webhook-rebuild on` rebuilds when this Git repo changes. That is not a full upstream watcher yet. When DG2YCB ships a new PLUS drop, bump `Version` / `%snapshot` in `wsjtx-improved.spec` and push; Copr will rebuild from the webhook.

If the Copr project already exists without the hamlib repo:

```bash
copr-cli modify wsjtx-improved \
  --repo copr://xsnrg/hamlib \
  --runtime-repo-dependency copr://xsnrg/hamlib
```

## Updating to a newer PLUS drop

1. Find the new Qt6 PLUS tarball under
   `https://sourceforge.net/projects/wsjt-x-improved/files/WSJT-X_vX.Y.Z/Source code/Qt6/`
2. Edit `wsjtx-improved.spec`:
   - `%define snapshot YYMMDD`
   - `Version:` if the series changed
   - `%changelog`
3. Push to this repo and let the Copr webhook fire, or run `copr-cli build-package`.

## Notes

- The SourceForge archive is nested: outer `wsjtx-VERSION/` contains `src/wsjtx.tgz`.
- Bundled hamlib is deleted; Copr builds should use `xsnrg/hamlib` (`hamlib-devel >= 4.7.2`).
- LTO is disabled. Fortran is built with `-fallow-argument-mismatch -std=legacy`.
- Standard Improved GUI only (not AL / widescreen). Those are separate upstream tarballs.
