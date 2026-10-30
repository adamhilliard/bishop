# -*- coding: utf-8 -*-
"""Update check.  Bishop, by Adam Hilliard (MIT).

Runs weekly, alongside the quality audit. One question: is a newer Bishop
release out than the one installed? If so, prints a one-line notice so the next
digest can pass it along.

It never fails the run. A network hiccup or an unreadable version is a quiet
skip, not an error, because a stale check is not a search defect. And it never
installs anything: /plugin commands don't work in a scheduled, non-interactive
run, so self-updating isn't possible. This only tells the user.

    python check_update.py
"""

from __future__ import print_function

import argparse
import io
import os
import re
import sys

try:
    from urllib.request import urlopen, Request
except ImportError:  # Python 2
    from urllib2 import urlopen, Request

GITHUB_REPO = "adamhilliard/bishop"


def read(path):
    try:
        return io.open(path, encoding="utf-8").read()
    except (IOError, OSError):
        return u""


def parse_version(s):
    """'v1.4.3' -> (1, 4, 3). Stops at the first non-numeric part."""
    nums = []
    for part in re.split(r"[.\-+]", (s or "").strip().lstrip("vV")):
        m = re.match(r"^(\d+)", part)
        if not m:
            break
        nums.append(int(m.group(1)))
    return tuple(nums)


def installed_version():
    """Read the version from the plugin's own plugin.json, three levels up
    from this script (scripts -> job-search -> skills -> plugin root)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    m = re.search(r'"version"\s*:\s*"([^"]+)"',
                  read(os.path.join(root, ".claude-plugin", "plugin.json")))
    return m.group(1) if m else None


def latest_release():
    """The version on main's plugin.json, which is what Sync installs.
    Bishop publishes no GitHub Releases, so the releases API has nothing."""
    url = ("https://raw.githubusercontent.com/%s/main/bishop/.claude-plugin/plugin.json"
           % GITHUB_REPO)
    try:
        req = Request(url, headers={"User-Agent": "bishop-update-check"})
        raw = urlopen(req, timeout=6).read().decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r'"version"\s*:\s*"([^"]+)"', raw)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".", help="the search's project folder")
    args = ap.parse_args()
    notice_path = os.path.join(os.path.abspath(args.project), "Update_Notice.md")

    installed = installed_version()
    if not installed:
        print("update: skipped, could not read the installed version")
        return 0
    latest = latest_release()
    if latest is None:
        # A network blip must not erase a real pending notice, so leave the
        # file untouched and skip.
        print("update: skipped, could not reach GitHub (not a failure)")
        return 0
    if parse_version(latest) > parse_version(installed):
        line = (u"**Bishop update available:** Bishop %s is out (you have %s). "
                u"To update: open Claude's Plugins screen and click Sync. "
                u"What changed is on [Bishop's GitHub page](https://github.com/%s)."
                % (latest.lstrip("vV"), installed, GITHUB_REPO))
        try:
            io.open(notice_path, "w", encoding="utf-8").write(line + u"\n")
        except (IOError, OSError):
            pass
        print("update: Bishop %s is available (you have %s); wrote Update_Notice.md"
              % (latest.lstrip("vV"), installed))
        print("NOTICE: the next digest includes Update_Notice.md.")
    else:
        # Caught up: clear any stale notice so it stops appearing in digests.
        try:
            if os.path.exists(notice_path):
                os.remove(notice_path)
        except OSError:
            pass
        print("update: up to date (%s)" % installed)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())
