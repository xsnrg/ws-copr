#!/usr/bin/env python3
"""Find the newest WS Qt6 source tarball on SourceForge.

Upstream renamed WSJT-X Improved to WS. Standard GUI tarball:
  WS_vX.Y.Z/Source code/Qt6/ws-X.Y.Z_YYMMDD_qt6.tgz
(not _AL_ or _widescreen_).

Used by .copr/Makefile at SRPM time and by the GitHub Actions watcher.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import subprocess
import sys
from typing import Iterable

PROJECT_FILES = "https://sourceforge.net/projects/wsjt-x-improved/files/"
RSS_URL = "https://sourceforge.net/projects/wsjt-x-improved/rss?path=/"
USER_AGENT = (
    "wsjtx-improved-copr/1.0 "
    "(+https://github.com/xsnrg/wsjtx-improved-copr)"
)

# Standard Qt6 GUI only. _AL_ and _widescreen_ do not match: the snapshot
# must follow the version immediately.
TARBALL_RE = re.compile(
    r"WS_v(\d+\.\d+\.\d+)/Source(?:%20| )code/Qt6/"
    r"ws-\1_(\d{6})_qt6\.tgz"
)
FOLDER_RE = re.compile(r"WS_v(\d+\.\d+\.\d+)")
QT6_NAME_RE = re.compile(
    r"(?<![A-Za-z0-9_])ws-(\d+\.\d+\.\d+)_(\d{6})_qt6\.tgz"
)


def _curl(url: str) -> str:
    cmd = [
        "curl",
        "-fsSL",
        "--retry",
        "3",
        "--retry-delay",
        "2",
        "-A",
        USER_AGENT,
        url,
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"curl failed ({proc.returncode}) for {url}: {proc.stderr.strip()}"
        )
    return proc.stdout


def _ver_key(version: str, snapshot: str) -> tuple:
    return tuple(int(p) for p in version.split(".")), int(snapshot)


def _best(pairs: Iterable[tuple[str, str]]) -> tuple[str, str] | None:
    items = list(pairs)
    if not items:
        return None
    return max(items, key=lambda item: _ver_key(*item))


def _from_text(text: str) -> list[tuple[str, str]]:
    return TARBALL_RE.findall(text) + QT6_NAME_RE.findall(text)


def discover() -> tuple[str, str]:
    found: list[tuple[str, str]] = []

    try:
        found.extend(_from_text(_curl(RSS_URL)))
    except RuntimeError as exc:
        print(f"warning: RSS fetch failed: {exc}", file=sys.stderr)

    try:
        index = _curl(PROJECT_FILES)
        found.extend(_from_text(index))
        versions = sorted(set(FOLDER_RE.findall(index)), key=lambda v: _ver_key(v, "0"))
    except RuntimeError as exc:
        print(f"warning: files index fetch failed: {exc}", file=sys.stderr)
        versions = sorted({v for v, _ in found}, key=lambda v: _ver_key(v, "0"))

    for ver, _snap in found:
        if ver not in versions:
            versions.append(ver)
    # Hard fallback series so a JS-only files index still works.
    for fallback in ("3.2.0", "3.1.0"):
        if fallback not in versions:
            versions.append(fallback)
    versions = sorted(set(versions), key=lambda v: _ver_key(v, "0"))

    # Probe the newest series folders directly; SF index pages are often JS-heavy.
    for version in reversed(versions[-3:] or []):
        qt6 = (
            f"{PROJECT_FILES}WS_v{version}/Source%20code/Qt6/"
        )
        try:
            found.extend(_from_text(_curl(qt6)))
        except RuntimeError as exc:
            print(f"warning: Qt6 listing {qt6} failed: {exc}", file=sys.stderr)

    best = _best(found)
    if best is None:
        raise SystemExit("could not discover a WS Qt6 source tarball on SourceForge")
    return best


def spec_pins(spec_text: str) -> tuple[str, str]:
    snap = re.search(r"^%define\s+snapshot\s+(\S+)", spec_text, re.M)
    ver = re.search(r"^Version:\s+(\S+)", spec_text, re.M)
    if not snap or not ver:
        raise SystemExit("spec is missing Version or %define snapshot")
    return ver.group(1), snap.group(1)


def update_spec(spec_path: pathlib.Path, version: str, snapshot: str) -> bool:
    text = spec_path.read_text()
    old_ver, old_snap = spec_pins(text)
    if old_ver == version and old_snap == snapshot:
        return False

    text = re.sub(
        r"^(%define\s+snapshot\s+)\S+",
        rf"\g<1>{snapshot}",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"^(Version:\s+)\S+",
        rf"\g<1>{version}",
        text,
        count=1,
        flags=re.M,
    )

    today = datetime.date.today().strftime("%a %b %d %Y")
    rel = re.search(r"^Release:\s+(\d+)", text, re.M)
    relnum = rel.group(1) if rel else "1"
    entry = (
        f"* {today} Jim Howard <xsnrg@users.noreply.github.com> "
        f"- {version}-{relnum}.{snapshot}\n"
        f"- Auto-select upstream WS Qt6 {version} snapshot {snapshot}\n\n"
    )
    text = re.sub(r"(?m)^%changelog\n", f"%changelog\n{entry}", text, count=1)
    spec_path.write_text(text)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update-spec",
        metavar="SPEC",
        help="Rewrite Version / %%snapshot in the spec when upstream moved",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print 'VERSION SNAPSHOT' and exit",
    )
    args = parser.parse_args()

    version, snapshot = discover()
    if args.print or not args.update_spec:
        print(f"{version} {snapshot}")

    if args.update_spec:
        path = pathlib.Path(args.update_spec)
        changed = update_spec(path, version, snapshot)
        print(
            f"{'updated' if changed else 'unchanged'} "
            f"{path} -> {version} snapshot {snapshot}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
