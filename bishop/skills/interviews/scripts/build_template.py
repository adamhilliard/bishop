# -*- coding: utf-8 -*-
"""Build assets/template.html, the page every interview deck starts from, out of the engine source.

    python build_template.py [--check]

For the maintainer: run it after any change under engine/, then commit both. Candidates never run
it; build_deck.py fills the template's data slots.

The page is engine/shell.html with the styles, the answers-file code and the engine inlined, and the
Bishop robot (the dashboard's assets/robot.svg, so the two pages share one mark) as the top-left
mark and the favicon. --check rebuilds in memory and exits 1 if the committed template differs.
"""
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, ".."))
ENGINE = os.path.join(SKILL, "engine")
OUT = os.path.join(SKILL, "assets", "template.html")
ROBOT = os.path.normpath(os.path.join(SKILL, "..", "dashboard", "assets", "robot.svg"))
DATA_SLOTS = ("__CONTENT__", "__META__", "__MASTER_DATA__")


def read(path):
    with open(path, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    # A control character is always a mangled escape from an edit script.
    bad = re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text)
    if bad:
        line = text[: bad.start()].count("\n") + 1
        sys.exit("%s:%d: control character U+%04X" % (os.path.basename(path), line, ord(bad.group())))
    return text


def build():
    shell = read(os.path.join(ENGINE, "shell.html"))
    css = read(os.path.join(ENGINE, "engine.css"))
    js = read(os.path.join(ENGINE, "answers.js")) + "\n" + read(os.path.join(ENGINE, "engine.js"))
    robot = read(ROBOT).strip()
    favicon = "data:image/svg+xml," + urllib.parse.quote(robot, safe=" =:/'\"")
    fills = [
        ("__FAVICON__", favicon),
        ("__ROBOT__", robot),
        ("__ENGINE_CSS__", "<style>\n" + css + "</style>"),
        # "</script" in the engine's own text would end the inline script early.
        ("__ENGINE_JS__", "<script>\n" + re.sub(r"</script", r"<\\/script", js, flags=re.I) + "</script>"),
    ]
    for token, value in fills:
        if shell.count(token) != 1:
            sys.exit("engine/shell.html needs exactly one " + token)
        shell = shell.replace(token, value, 1)
    for slot in DATA_SLOTS:
        if shell.count(slot) != 1:
            sys.exit("engine/shell.html needs exactly one " + slot)
    return shell


def main(argv):
    html = build()
    if "--check" in argv:
        with open(OUT, encoding="utf-8") as f:
            same = f.read().replace("\r\n", "\n") == html
        print("template.html is current" if same else "template.html is out of date: run build_template.py")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("Wrote %s  (%d KB)" % (OUT, len(html) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
