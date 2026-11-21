#!/usr/bin/env python3
"""Generate the repository images: the banner and the terminal screenshot.

Both images are built from real command output, so the screenshot cannot show
anything the CLI does not actually print. Requires Pillow and Pygments
(`pip install pillow pygments`).

    python scripts/make_assets.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
MONO = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
MONO_BOLD = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")

# GitHub dark palette, plus the South African flag accents.
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#3fb950"
GOLD = "#ffb612"
RED = "#f85149"
BLUE = "#79c0ff"
PURPLE = "#d2a8ff"
STRING = "#a5d6ff"
COMMENT = "#8b949e"
SA_GREEN = "#007a4d"
SA_GOLD = "#ffb612"
SA_RED = "#de3831"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


# --- banner --------------------------------------------------------------


def make_banner(path: str, width: int = 1280, height: int = 640) -> None:
    """Centred wordmark, tagline and a small code card. No overlapping regions."""
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / height
        draw.line(
            [(0, y), (width, y)],
            fill=(int(13 + 6 * ratio), int(17 + 24 * ratio), int(23 + 18 * ratio)),
        )

    def centred(text: str, y: int, typeface, colour: str) -> None:
        text_width = draw.textlength(text, font=typeface)
        draw.text(((width - text_width) / 2, y), text, font=typeface, fill=colour)

    # flag accent, above the wordmark
    bar_w, gap = 74, 10
    total = bar_w * 3 + gap * 2
    left = (width - total) / 2
    for index, colour in enumerate((SA_GREEN, SA_GOLD, SA_RED)):
        x = left + index * (bar_w + gap)
        draw.rectangle([x, 62, x + bar_w, 70], fill=colour)

    centred("REX", 104, font(BOLD, 150), GOLD)
    centred("A tiny, friendly scripting language for API work.", 286, font(REGULAR, 34), TEXT)
    centred("Everything starts with rex.  ·  Made in Mzansi.", 334, font(REGULAR, 26), MUTED)

    # code card, centred and fully below the text block
    mono = font(MONO, 21)
    lines: List[Tuple[str, str]] = [
        ("# hello.rex", COMMENT),
        ('rex.show("Sawubona Mhlaba")', TEXT),
        ('rex.let post = rex.get(url)', TEXT),
        ("rex.show(post.title)", TEXT),
    ]
    card_w = max(draw.textlength(text, font=mono) for text, _ in lines) + 64
    card_w = max(card_w, 520)
    card_h = len(lines) * 30 + 36
    card = [(width - card_w) / 2, 400, (width + card_w) / 2, 400 + card_h]
    draw.rounded_rectangle(card, radius=12, fill=PANEL, outline=BORDER, width=2)
    y = card[1] + 18
    for text, colour in lines:
        draw.text((card[0] + 32, y), text, font=mono, fill=colour)
        y += 30

    assert card[3] < height - 20, "code card overflows the banner"
    image.save(path, "PNG", optimize=True)


# --- terminal screenshot -------------------------------------------------


def run(*args: str, cwd: str) -> str:
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT
    result = subprocess.run(
        [sys.executable, "-m", "rex", *args],
        cwd=cwd, capture_output=True, text=True, env=env,
    )
    return result.stdout.rstrip("\n")


def token_colours(line: str) -> List[Tuple[str, str]]:
    """Highlight one Rex source line with the repo's own Pygments lexer."""
    from pygments import lex
    from rex_lexer import RexLexer

    palette = {
        "Name.Namespace": BLUE,
        "Name.Builtin": PURPLE,
        "Name.Function": GOLD,
        "Keyword": RED,
        "Keyword.Constant": BLUE,
        "String.Double": STRING,
        "String.Single": STRING,
        "String.Interpol": GOLD,
        "String.Escape": GOLD,
        "Number": BLUE,
        "Comment": COMMENT,
        "Operator": MUTED,
        "Punctuation": MUTED,
        "Name": TEXT,
    }
    out: List[Tuple[str, str]] = []
    for kind, value in lex(line, RexLexer()):
        name = str(kind)
        for prefix in ("Token.", "Literal."):
            if name.startswith(prefix):
                name = name[len(prefix):]
        colour = TEXT
        while name and name not in palette:
            name = name.rsplit(".", 1)[0] if "." in name else ""
        colour = palette.get(name, TEXT)
        out.append((value, colour))
    if out and out[-1][0].endswith("\n"):
        out[-1] = (out[-1][0].rstrip("\n"), out[-1][1])
    return [pair for pair in out if pair[0]]


def make_screenshot(path: str, width: int = 1500, height: int = 1000) -> None:
    workdir = tempfile.mkdtemp(prefix="rex-shot-")
    source = os.path.join(workdir, "hello.rex")
    with open(source, "w", encoding="utf-8") as handle:
        handle.write(
            'rex.show("Sawubona Mhlaba")\n'
            'rex.let langs = ["Rex", "Python", "JavaScript"]\n'
            "rex.for lang in langs\n"
            '  rex.show(" -", rex.upper(lang))\n'
            "rex.end\n"
        )
    broken = os.path.join(workdir, "demo.rex")
    with open(broken, "w", encoding="utf-8") as handle:
        handle.write(
            'rex.show("checking this file")\n'
            'rex.sho("typo in the builtin")\n'
            "rex.len()\n"
            "rex.show(titel)\n"
        )

    output = run("run", "hello.rex", cwd=workdir)
    check_env = dict(os.environ)
    check_env["PYTHONPATH"] = ROOT
    checked = subprocess.run(
        [sys.executable, "-m", "rex", "check", "demo.rex"],
        cwd=workdir, capture_output=True, text=True, env=check_env,
    )

    image = Image.new("RGB", (width, height), "#05070a")
    draw = ImageDraw.Draw(image)

    # window
    draw.rounded_rectangle([24, 24, width - 24, height - 24], radius=16, fill=BG, outline=BORDER, width=2)
    draw.rounded_rectangle([24, 24, width - 24, 76], radius=16, fill=PANEL)
    draw.rectangle([24, 60, width - 24, 76], fill=PANEL)
    for index, colour in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        cx = 56 + index * 26
        draw.ellipse([cx, 42, cx + 14, 56], fill=colour)
    draw.text((width // 2 - 96, 38), "rex — zsh — 96×32", font=font(REGULAR, 18), fill=MUTED)

    mono = font(MONO, 24)
    mono_bold = font(MONO_BOLD, 24)
    x0 = 60
    y = 108
    line_h = 36

    def prompt(command: str) -> None:
        nonlocal y
        draw.text((x0, y), "$", font=mono_bold, fill=GREEN)
        draw.text((x0 + 22, y), command, font=mono, fill=TEXT)
        y += line_h + 6

    def source_line(text: str) -> None:
        nonlocal y
        x = x0 + 22
        for value, colour in token_colours(text):
            draw.text((x, y), value, font=mono, fill=colour)
            x += draw.textlength(value, font=mono)
        y += line_h

    def plain(text: str, colour: str = TEXT) -> None:
        nonlocal y
        draw.text((x0 + 22, y), text, font=mono, fill=colour)
        y += line_h

    def diagnostic(line: str) -> None:
        nonlocal y
        x = x0 + 22
        if ": error: " in line:
            head, rest = line.split(": error: ", 1)
            draw.text((x, y), head + ":", font=mono, fill=MUTED)
            x += draw.textlength(head + ": ", font=mono)
            draw.text((x, y), "error:", font=mono_bold, fill=RED)
            x += draw.textlength("error: ", font=mono)
            draw.text((x, y), rest, font=mono, fill=TEXT)
        elif ": warning: " in line:
            head, rest = line.split(": warning: ", 1)
            draw.text((x, y), head + ":", font=mono, fill=MUTED)
            x += draw.textlength(head + ": ", font=mono)
            draw.text((x, y), "warning:", font=mono_bold, fill=GOLD)
            x += draw.textlength("warning: ", font=mono)
            draw.text((x, y), rest, font=mono, fill=TEXT)
        else:
            draw.text((x, y), line, font=mono, fill=TEXT)
        y += line_h

    prompt("cat hello.rex")
    for line in open(source, encoding="utf-8").read().splitlines():
        source_line(line)
    y += 14

    prompt("rex run hello.rex")
    for line in output.splitlines():
        plain(line)
    y += 14

    prompt("rex check demo.rex")
    for line in checked.stdout.rstrip("\n").splitlines():
        diagnostic(line)
    y += 18

    draw.text((x0 + 22, y), "rex 1.0.0  ·  exit code %d  ·  Made in Mzansi" % checked.returncode,
              font=font(REGULAR, 20), fill=MUTED)

    image.save(path, "PNG", optimize=True)


def main() -> int:
    os.makedirs(ASSETS, exist_ok=True)
    banner = os.path.join(ASSETS, "banner.png")
    make_banner(banner)
    make_banner(os.path.join(ASSETS, "social-preview.png"))
    make_screenshot(os.path.join(ASSETS, "screenshot.png"))
    for name in ("banner.png", "social-preview.png", "screenshot.png"):
        full = os.path.join(ASSETS, name)
        with Image.open(full) as image:
            print("%s  %dx%d  %d bytes" % (name, image.width, image.height, os.path.getsize(full)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
