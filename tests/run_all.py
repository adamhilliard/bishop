# -*- coding: utf-8 -*-
"""Run every Bishop check on this machine: one command, before any commit that touches a module and
before every release. Nothing runs on GitHub; GitHub only stores the code.

    python tests/run_all.py

What it runs:
  job search    the scripts' own tests (scripts/test_*.py)
  interviews    the template matches engine/, the test candidate's decks build clean (every round),
                and the deck flows pass in a headless browser (Chrome or Edge)
  contracts     tests/test_contracts.py: every file one module reads from another still has the parts
                CONTRACTS.md lists
  leak test     the maintainer's own data never ships (needs the apps repo and the vault beside this one)
  plugin        claude plugin validate (needs the claude command line)

A check whose tool isn't on this machine is reported as SKIPPED with the reason, never as a pass.
Exits 1 if anything failed.
"""
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PLUGIN = os.path.join(ROOT, "bishop")
INTERVIEWS = os.path.join(PLUGIN, "skills", "interviews")
CANDIDATE = os.path.join(ROOT, "tests", "candidate")
FLOWS = os.path.join(ROOT, "tests", "pages", "interviews_flows.js")
# The core deck's answers as the browser holds them; a company deck's page starts with them saved.
CORE_ANSWERS = os.path.join(ROOT, "tests", "pages", "core_answers.json")
PY = sys.executable
results = []


def record(name, status, detail=""):
    results.append((name, status, detail))
    mark = {"PASS": "ok  ", "FAIL": "FAIL", "SKIPPED": "skip"}[status]
    print("  %s %s%s" % (mark, name, ("  (" + detail + ")") if detail else ""))


def run(cmd, cwd=None, timeout=300):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def last_line(text):
    lines = [x for x in text.strip().splitlines() if x.strip()]
    return lines[-1] if lines else ""


def find_browser():
    names = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for n in names:
        if os.path.isfile(n):
            return n
    for n in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        if shutil.which(n):
            return shutil.which(n)
    return None


def job_search():
    print("job search")
    for t in sorted(glob.glob(os.path.join(PLUGIN, "skills", "job-search", "scripts", "test_*.py"))):
        code, out = run([PY, t], cwd=os.path.dirname(t))
        record(os.path.basename(t), "PASS" if code == 0 else "FAIL", last_line(out))


def build_decks(work):
    """Copy the candidate's decks to a scratch folder and build them there. Returns the folder."""
    prep = os.path.join(work, "Bishop", "Interview_Prep")
    shutil.copytree(os.path.join(CANDIDATE, "Interview_Prep"), prep)
    profile = os.path.join(CANDIDATE, "Reference_Profile.md")
    if os.path.isfile(profile):
        shutil.copy(profile, os.path.join(work, "Bishop", "Reference_Profile.md"))
    builder = os.path.join(INTERVIEWS, "scripts", "build_deck.py")
    ok = True
    for deck in sorted(d for d in os.listdir(prep) if os.path.isfile(os.path.join(prep, d, "meta.json"))):
        meta = json.load(open(os.path.join(prep, deck, "meta.json"), encoding="utf-8"))["meta"]
        rounds = [r["id"] for r in (meta.get("deck") or {}).get("rounds") or []]
        for r in rounds or [None]:
            cmd = [PY, builder, deck, "--check"] + (["--round", r] if r else [])
            code, out = run(cmd, cwd=prep)
            name = "deck %s%s builds clean" % (deck, " (round %s)" % r if r else "")
            clean = code == 0 and " 0 errors" in out and " 0 warnings" in out
            record(name, "PASS" if clean else "FAIL", last_line(out))
            ok = ok and clean
        code, out = run([PY, builder, deck], cwd=prep)
        if code != 0:
            record("deck %s writes" % deck, "FAIL", last_line(out))
            ok = False
    return prep if ok else None


def search_name():
    p = os.path.join(CANDIDATE, "Reference_Profile.md")
    if not os.path.isfile(p):
        return "Bishop"
    sys.path.insert(0, os.path.join(INTERVIEWS, "scripts"))
    import build_deck  # noqa: E402

    return build_deck.search_name(os.path.join(CANDIDATE, "Interview_Prep", "core")) or "Bishop"


def flows(prep, work):
    browser = find_browser()
    if not browser:
        record("deck flows in a browser", "SKIPPED", "no Chrome or Edge found")
        return
    script = open(FLOWS, encoding="utf-8").read()
    expect = json.dumps({"name": search_name()})
    seed = json.load(open(CORE_ANSWERS, encoding="utf-8"))
    seed.pop("_about", None)
    for page in sorted(glob.glob(os.path.join(prep, "*.html"))):
        html_text = open(page, encoding="utf-8").read()
        guard = "<script>window.__errors=[];addEventListener('error',function(e){window.__errors.push(String(e.message))});</script>"
        # Answers live only in the browser, so a company deck's browser gets what the core deck saved
        # (each page runs in a fresh browser profile).
        if os.path.basename(page) != "core.html":
            guard += "<script>localStorage.setItem('bishop-interviews:answers', %s);</script>" % json.dumps(json.dumps(seed)).replace("</", "<\\/")
        html_text = html_text.replace("<head>", "<head>\n" + guard, 1)
        html_text = html_text.replace("</body>", "<script>window.__expect=%s;\n%s</script>\n</body>" % (expect, script), 1)
        test_page = page[:-5] + ".test.html"
        open(test_page, "w", encoding="utf-8", newline="\n").write(html_text)
        profile_dir = os.path.join(work, "browser-" + os.path.basename(page))
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--user-data-dir=" + profile_dir, "--allow-file-access-from-files", "--virtual-time-budget=60000",
               "--dump-dom", "file:///" + test_page.replace("\\", "/")]
        try:
            code, out = run(cmd, timeout=180)
        except subprocess.TimeoutExpired:
            record("flows: " + os.path.basename(page), "FAIL", "the browser timed out")
            continue
        # The last match: the element the page adds at the end (the script's own text mentions the tag).
        found = re.findall(r'<pre id="test-results">(\[.*?\])</pre>', out, re.S)
        if not found:
            record("flows: " + os.path.basename(page), "FAIL", "no results came back from the page")
            continue
        for r in json.loads(html.unescape(found[-1])):
            record("%s: %s" % (os.path.basename(page)[:-5], r["name"]), "PASS" if r["ok"] else "FAIL", "" if r["ok"] else r["detail"])


def interviews():
    print("interviews")
    code, out = run([PY, os.path.join(INTERVIEWS, "scripts", "build_template.py"), "--check"])
    record("template matches engine/", "PASS" if code == 0 else "FAIL", last_line(out))
    if shutil.which("node"):
        code, out = run(["node", "--check", os.path.join(INTERVIEWS, "engine", "engine.js")])
        record("engine/engine.js parses", "PASS" if code == 0 else "FAIL", last_line(out))
    else:
        record("engine parses", "SKIPPED", "no node; the browser flows still load it")
    work = tempfile.mkdtemp(prefix="bishop-tests-")
    try:
        prep = build_decks(work)
        if prep:
            flows(prep, work)
        else:
            record("deck flows in a browser", "SKIPPED", "a deck didn't build")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def contracts():
    print("contracts")
    t = os.path.join(ROOT, "tests", "test_contracts.py")
    if not os.path.isfile(t):
        record("contract tests", "SKIPPED", "tests/test_contracts.py not written yet")
        return
    code, out = run([PY, t])
    for line in out.splitlines():
        m = re.match(r"\s*(ok|FAIL)\s+(.*)$", line)
        if m:
            name, _, detail = m.group(2).partition("  (")
            record(name.strip(), "PASS" if m.group(1) == "ok" else "FAIL", detail.rstrip(")"))
    if code != 0 and not any(s == "FAIL" for n, s, d in results if n):
        record("contract tests", "FAIL", last_line(out))


def leak_test():
    print("leak test")
    apps = os.path.normpath(os.path.join(ROOT, "..", "apps", "13-humblebrag", "test_leaks.mjs"))
    vault = os.path.normpath(os.path.join(ROOT, "..", "ai", "Projects", "02. Career", "02. Job Search", "07. Interview Prep"))
    if not (os.path.isfile(apps) and os.path.isdir(vault) and shutil.which("node")):
        record("maintainer data never ships", "SKIPPED", "needs ../apps, ../ai and node (the maintainer's machine)")
        return
    code, out = run(["node", apps, "--decks", vault, "--bishop", ROOT])
    record("maintainer data never ships", "PASS" if code == 0 else "FAIL", last_line(out))


def plugin():
    print("plugin")
    claude = shutil.which("claude")
    if not claude:
        record("claude plugin validate", "SKIPPED", "no claude command line")
        return
    code, out = run([claude, "plugin", "validate", PLUGIN])
    record("claude plugin validate", "PASS" if code == 0 else "FAIL", last_line(out))
    for p in sorted(glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md"))):
        text = open(p, encoding="utf-8").read()
        m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
        name = re.search(r"^name:\s*(\S+)", m.group(1), re.M) if m else None
        ok = bool(name) and name.group(1) == os.path.basename(os.path.dirname(p))
        record("skill %s frontmatter" % os.path.basename(os.path.dirname(p)), "PASS" if ok else "FAIL", "" if ok else "name missing or not the folder name")


def main():
    # Tools print characters a Windows console's default code page can't show.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    job_search()
    interviews()
    contracts()
    leak_test()
    plugin()
    failed = [r for r in results if r[1] == "FAIL"]
    skipped = [r for r in results if r[1] == "SKIPPED"]
    print("\n%d passed, %d failed, %d skipped" % (len(results) - len(failed) - len(skipped), len(failed), len(skipped)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
