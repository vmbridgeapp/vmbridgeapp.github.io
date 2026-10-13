#!/usr/bin/env python3
"""Build the VMBridge site.

The public origin comes from ``VMBRIDGE_SITE_URL`` (default
https://vmbridgeapp.github.io). Cloudflare Pages at https://vmbridge.pages.dev
is the documented alternative. Nothing in this tree uses a custom domain.

    python site/build_site.py --out site/out
    VMBRIDGE_SITE_URL=https://vmbridge.pages.dev python site/build_site.py --out site/out
    VMBRIDGE_GSC_VERIFICATION=<token from Search Console> python site/build_site.py
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "https://vmbridgeapp.github.io"
ALTERNATE_BASE = "https://vmbridge.pages.dev"
GSC_PLACEHOLDER = "REPLACE_WITH_GOOGLE_SEARCH_CONSOLE_TOKEN"
DEFAULT_CHECKOUT = "https://example.lemonsqueezy.com/checkout/buy/PLACEHOLDER"
SOURCE_REPO = "https://github.com/AlexmChadwick/Parallels-Agents"
RELEASES_URL = SOURCE_REPO + "/releases"
LICENSE_URL = SOURCE_REPO + "/blob/main/LICENSE"
X_URL = "https://x.com/vmbridgeapp"
GITHUB_ORG_URL = "https://github.com/vmbridgeapp"
TRADEMARK = (
    "Parallels is a trademark of Parallels International GmbH. "
    "VMBridge is not affiliated with, endorsed by, or sponsored by "
    "Parallels International GmbH. VMPal is a product of TablePlus. "
    "VMBridge is not affiliated with TablePlus."
)
PRICE = "9.99"
UPDATED = "2026-10-13"

# 5x7 glyphs. Rows are left to right, "1" is ink.
_GLYPHS: dict[str, tuple[str, ...]] = {
    " ": ("00000",) * 7,
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "·": ("00000", "00000", "00000", "00100", "00000", "00000", "00000"),
}


def site_base(explicit: str | None = None) -> str:
    raw = (explicit or os.environ.get("VMBRIDGE_SITE_URL") or DEFAULT_BASE).strip()
    if not raw:
        raw = DEFAULT_BASE
    return raw.rstrip("/")


def checkout_url() -> str:
    return (
        os.environ.get("VMBRIDGE_CHECKOUT_URL", "").strip()
        or os.environ.get("GUEST_VM_AGENTS_CHECKOUT_URL", "").strip()
        or DEFAULT_CHECKOUT
    )


def abs_url(base: str, path: str) -> str:
    if path in {"", "/"}:
        return base + "/"
    return base + "/" + path.strip("/") + "/"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png_rgb(path: Path, width: int, height: int, rgb: bytes | bytearray) -> None:
    """Write an 8-bit RGB PNG. ``rgb`` is width*height*3 bytes, row-major."""

    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        start = y * stride
        raw.extend(rgb[start : start + stride])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


def _fill(buf: bytearray, width: int, height: int, color: tuple[int, int, int]) -> None:
    pixel = bytes(color)
    row = pixel * width
    for y in range(height):
        start = y * width * 3
        buf[start : start + width * 3] = row


def _rect(
    buf: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(width, x1)
    y1 = min(height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    span = (x1 - x0) * 3
    for y in range(y0, y1):
        start = (y * width + x0) * 3
        buf[start : start + span] = row


def _text_width(text: str, scale: int) -> int:
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def _blit(
    buf: bytearray,
    width: int,
    height: int,
    text: str,
    x: int,
    y: int,
    scale: int,
    color: tuple[int, int, int],
) -> None:
    cursor = x
    for ch in text:
        glyph = _GLYPHS.get(ch, _GLYPHS[" "])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit != "1":
                    continue
                _rect(
                    buf,
                    width,
                    height,
                    cursor + col * scale,
                    y + row * scale,
                    cursor + (col + 1) * scale,
                    y + (row + 1) * scale,
                    color,
                )
        cursor += 6 * scale


def _centered(text: str, canvas: int, scale: int) -> int:
    return max(0, (canvas - _text_width(text, scale)) // 2)


def write_icon(path: Path) -> None:
    size = 64
    buf = bytearray(size * size * 3)
    _fill(buf, size, size, (14, 59, 50))
    _rect(buf, size, size, 0, 0, size, 6, (212, 168, 74))
    label = "V"
    scale = 6
    _blit(
        buf,
        size,
        size,
        label,
        _centered(label, size, scale),
        14,
        scale,
        (244, 239, 228),
    )
    write_png_rgb(path, size, size, buf)


def write_og(path: Path) -> None:
    """1200x630 card. Deterministic bitmap font, no system fonts."""

    width, height = 1200, 630
    buf = bytearray(width * height * 3)
    bg = (10, 26, 22)
    cream = (244, 239, 228)
    muted = (176, 198, 188)
    gold = (232, 196, 120)
    _fill(buf, width, height, bg)
    _rect(buf, width, height, 0, 0, width, 12, (212, 168, 74))
    _rect(buf, width, height, 36, 36, width - 36, height - 36, (28, 72, 60))
    _rect(buf, width, height, 40, 40, width - 40, height - 40, bg)
    lines = [
        (118, 16, "VMBRIDGE", cream),
        (268, 5, "FOR PARALLELS DESKTOP", muted),
        (360, 6, "LET YOUR AI AGENT DRIVE", cream),
        (430, 6, "PARALLELS DESKTOP VMS", cream),
        (520, 5, "$9.99 ONCE  ·  7-DAY TRIAL", gold),
    ]
    for y, scale, text, color in lines:
        _blit(buf, width, height, text, _centered(text, width, scale), y, scale, color)
    _rect(buf, width, height, 420, 328, 780, 334, gold)
    write_png_rgb(path, width, height, buf)


def render_markdown(text: str) -> str:
    """Enough Markdown for the docs pages: headings, paragraphs, lists, code."""

    lines = text.strip().splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def inline(value: str) -> str:
        escaped = esc(value)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        return escaped

    for line in lines:
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
                code = []
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue
        if line.startswith("# "):
            flush_paragraph()
            flush_list()
            out.append(f"<h1>{inline(line[2:])}</h1>")
            continue
        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            out.append(f"<h2>{inline(line[3:])}</h2>")
            continue
        if line.startswith("### "):
            flush_paragraph()
            flush_list()
            out.append(f"<h3>{inline(line[4:])}</h3>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        paragraph.append(line.strip())
    flush_paragraph()
    flush_list()
    if in_code:
        out.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
    return "\n".join(out)


DOCS: dict[str, str] = {
    "quickstart": """# Quickstart

Give an agent a Parallels Desktop virtual machine. The host needs macOS 14 or later and Parallels Desktop Pro or Business.

## Install the command

```
git clone https://github.com/AlexmChadwick/Parallels-Agents.git
cd Parallels-Agents
./scripts/install.sh
```

That installs `vmbridge`. `parallels-pro-mcp` and `guest-vm-agents` are the same command. A notarized DMG ships with the GitHub release when a signed build is published. It is not a file on this website.

## Start the trial

Open VMBridge. The 7-day full-featured trial starts at first launch on that Mac. The intended price after the trial is $9.99 once. The Lemon Squeezy link on the site is a checkout placeholder until the store ids are set. It is not a live store.

## Connect Claude Code, Codex, or Cursor

```
vmbridge connect claude-code
vmbridge connect codex
vmbridge connect cursor
vmbridge connect list
```

Quit the agent and open it again so it loads the server. The same command covers Claude Desktop, Gemini CLI, VS Code, Windsurf, Cline, and the other MCP clients the app lists.

## Let it look at the guest

The agent can take a screenshot, read the text on the screen, click, and type. Those tools use the virtual machine's keyboard and mouse. They do not need Parallels Tools, which is how an agent can drive an installer. Commands, files, and the clipboard do need Parallels Tools.

## Stop it

Pause all agents from the menu-bar app, or turn off agent control for that VM. Either one is checked on the next tool call.
""",
    "install": """# Install VMBridge

VMBridge is a macOS app for Parallels Desktop. The host needs macOS 14 or later and Parallels Desktop Pro or Business, because the tools use prlctl and the Parallels Virtualization SDK.

## Developer install

```
git clone https://github.com/AlexmChadwick/Parallels-Agents.git
cd Parallels-Agents
./scripts/install.sh
```

That installs the `vmbridge` command. `parallels-pro-mcp` and `guest-vm-agents` are the same command.

## Connect an agent

```
vmbridge connect claude-code
vmbridge connect list
```

The same connect command covers Claude Desktop, Codex, Cursor, VS Code, Windsurf, Cline, Gemini CLI, and other MCP clients.

## Where state lives

The default folder is ~/Library/Application Support/VMBridge. Set VMBRIDGE_HOME to move it. PARALLELS_MCP_HOME still works. If the new folder does not exist and an older "Parallels Pro MCP" folder does, that older folder is kept so the trial clock is not reset.
""",
    "trial-and-license": """# Trial and license

VMBridge is a one-time purchase of $9.99 with a 7-day full-featured free trial. The trial starts at first launch on that Mac. It is stored in license.json and in the macOS login Keychain. Deleting only one of those copies does not restart the trial. Setting the clock back does not extend it.

## After you buy

A license key is activated with the Lemon Squeezy License API. No store API secret is shipped in the app. After a successful check, the app keeps working offline for 14 days.

## Store settings

These are public identifiers, not secrets:

- VMBRIDGE_CHECKOUT_URL
- VMBRIDGE_LEMON_PRODUCT_ID
- VMBRIDGE_LEMON_VARIANT_ID

GUEST_VM_AGENTS_CHECKOUT_URL, GUEST_VM_AGENTS_LEMON_PRODUCT_ID, and GUEST_VM_AGENTS_LEMON_VARIANT_ID still work.

Until a real product id is set, the license check is not tied to a store product. Set the ids before selling. The license text in the repository is a draft and needs legal review before the app is sold.
""",
    "mcp-tools": """# MCP tools for a Parallels Desktop VM

VMBridge speaks MCP. An agent on the Mac starts `vmbridge` over stdio. An agent inside a VM uses the daemon on the Parallels Shared or Host-Only network, with a token that works only for that VM.

## What an agent can do

- See the screen and read the text on it (vm_screenshot, vm_read_screen).
- Click, type, scroll, and drag with the VM's own keyboard and mouse.
- Run commands and move files (vm_run, vm_exec, vm_copy_to_guest, vm_copy_from_guest).
- List and focus windows, open an app or URL, and search files by name.
- Start, stop, pause, clone, and create VMs, and take and revert snapshots.
- Sign in at the login screen without the agent seeing the password.

## What it does not do

- It does not record video of the VM.
- It does not read the guest accessibility tree. On-screen text is OCR.
- It does not rename snapshots. prlctl has no rename.
- It is not a hypervisor. Parallels Desktop runs the VM.
""",
}


def pages() -> list[dict[str, object]]:
    faqs = [
        (
            "What is VMBridge?",
            "VMBridge is a macOS app for Parallels Desktop. It gives an AI agent a virtual machine as its own computer over MCP: screen, keyboard, mouse, commands, files, and snapshots. The intended price is $9.99 once, with a 7-day full-featured free trial.",
        ),
        (
            "Does VMBridge replace Parallels Desktop?",
            "No. VMBridge drives virtual machines that Parallels Desktop already runs. You need Parallels Desktop Pro or Business on the Mac. Parallels is a trademark of Parallels International GmbH. VMBridge is not affiliated with Parallels.",
        ),
        (
            "How does Claude Code control a VM?",
            "Run vmbridge connect claude-code on the Mac. Claude Code then talks to the VMBridge MCP server. The agent sees the guest screen and uses the guest keyboard and mouse. It does not drive your Mac desktop.",
        ),
        (
            "What does the $9.99 purchase include?",
            "A one-time license key for VMBridge, not a subscription. The 7-day trial is full-featured and starts at first launch. A validated key keeps working for 14 days without reaching the license server. The checkout on this site is a Lemon Squeezy placeholder until the store ids are set.",
        ),
        (
            "How is VMBridge different from VMPal?",
            "VMPal, from TablePlus, is a VM app with a built-in MCP server. VMBridge is an independent agent layer on Parallels Desktop. It does not include VMPal's hypervisor, Windows engine, or VM file format. See the comparison page for a feature-by-feature map.",
        ),
        (
            "Where is the DMG?",
            "The notarized disk image is not a file on this website. It ships with the GitHub release when a signed macOS build is published. Until then, install from the source repository with scripts/install.sh.",
        ),
        (
            "What leaves this Mac?",
            "The app does not include an analytics or crash-reporting SDK. Activating or validating a license key sends that key and an instance name to the Lemon Squeezy License API. Sign-in passwords stay in the login Keychain and are not returned by tools or written to the activity log.",
        ),
    ]
    home_faqs = faqs[:3]
    return [
        {
            "slug": "",
            "nav": "VMBridge",
            "in_nav": False,
            "title": "VMBridge for Parallels Desktop — let your AI agent drive VMs",
            "description": "Let your AI agent drive Parallels Desktop VMs. VMBridge is an MCP server for macOS 14 or later. $9.99 one-time, with a 7-day full-featured free trial. Works with Claude Code, Codex, and Cursor.",
            "h1": "Let your AI agent drive Parallels Desktop VMs",
            "kind": "home",
            "faqs": home_faqs,
        },
        {
            "slug": "mcp-server-for-parallels-desktop",
            "nav": "MCP server",
            "in_nav": False,
            "title": "MCP server for Parallels Desktop",
            "description": "VMBridge is an MCP server for Parallels Desktop. Agents see the VM screen, type, click, run commands, and move files without touching the Mac desktop.",
            "h1": "MCP server for Parallels Desktop",
            "kind": "article",
            "lead": "VMBridge is an MCP server that lets an AI agent drive a Parallels Desktop virtual machine.",
        },
        {
            "slug": "claude-code-control-a-vm",
            "nav": "Claude Code",
            "in_nav": False,
            "title": "Claude Code control a VM",
            "description": "Use Claude Code to control a Parallels Desktop VM with VMBridge. One command connects the agent. The VM's screen, keyboard, and mouse stay inside the guest.",
            "h1": "Use Claude Code to control a VM",
            "kind": "article",
            "lead": "Claude Code can control a Parallels Desktop VM through VMBridge's MCP server.",
        },
        {
            "slug": "ai-agent-virtual-machine-mac",
            "nav": "AI agent VM",
            "in_nav": False,
            "title": "AI agent virtual machine on Mac",
            "description": "Give an AI agent a virtual machine on a Mac. VMBridge runs on macOS and drives Parallels Desktop guests: Linux, Windows, and macOS, with per-VM permissions.",
            "h1": "An AI agent virtual machine on a Mac",
            "kind": "article",
            "lead": "VMBridge is how an AI agent gets a virtual machine on a Mac that already runs Parallels Desktop.",
        },
        {
            "slug": "vs-vmpal",
            "nav": "vs VMPal",
            "in_nav": True,
            "title": "VMBridge vs VMPal",
            "description": "VMBridge and VMPal both give an AI agent a computer over MCP. VMPal is a hypervisor from TablePlus. VMBridge drives Parallels Desktop and is not affiliated with TablePlus.",
            "h1": "VMBridge compared with VMPal",
            "kind": "compare",
            "lead": "VMPal and VMBridge both expose a virtual machine to an AI agent over MCP. They are different products.",
        },
        {
            "slug": "pricing",
            "nav": "Pricing",
            "in_nav": True,
            "title": "VMBridge pricing",
            "description": "VMBridge is a $9.99 one-time purchase for macOS, with a 7-day full-featured free trial. It is not a subscription. A license key is checked with Lemon Squeezy.",
            "h1": "Pricing",
            "kind": "pricing",
            "lead": "VMBridge is sold as a one-time purchase of $9.99, with a 7-day full-featured free trial.",
        },
        {
            "slug": "faq",
            "nav": "FAQ",
            "in_nav": True,
            "title": "VMBridge FAQ",
            "description": "Answers about VMBridge for Parallels Desktop: the MCP server, the $9.99 license, the 7-day trial, Claude Code, the DMG, privacy, and how it differs from VMPal.",
            "h1": "Questions about VMBridge",
            "kind": "faq",
            "faqs": faqs,
        },
        {
            "slug": "docs",
            "nav": "Docs",
            "in_nav": True,
            "title": "VMBridge docs",
            "description": "Install VMBridge, connect an MCP agent, and read the trial rules. The same pages are plain Markdown for people and for answer engines.",
            "h1": "Docs",
            "kind": "docs",
        },
        {
            "slug": "privacy",
            "nav": "Privacy",
            "in_nav": False,
            "title": "VMBridge privacy policy",
            "description": "What VMBridge stores on the Mac, and the one request a license check sends to Lemon Squeezy. No analytics SDK is included.",
            "h1": "Privacy policy",
            "kind": "legal",
        },
        {
            "slug": "eula",
            "nav": "EULA",
            "in_nav": False,
            "title": "VMBridge EULA (draft)",
            "description": "The VMBridge end user license is a draft and is not legal advice. Read the LICENSE file in the source repository before relying on it.",
            "h1": "End user license (draft)",
            "kind": "legal",
        },
        {
            "slug": "trademark",
            "nav": "Trademark",
            "in_nav": False,
            "title": "VMBridge trademark notice",
            "description": "Parallels is a trademark of Parallels International GmbH. VMBridge is not affiliated with Parallels or with TablePlus.",
            "h1": "Trademark notice",
            "kind": "legal",
        },
    ]


def organization(base: str) -> dict[str, object]:
    return {
        "@type": "Organization",
        "name": "VMBridge",
        "url": base + "/",
        "description": "VMBridge for Parallels Desktop. An MCP server and macOS app that lets an AI agent drive a virtual machine.",
        "logo": base + "/assets/icon.png",
        "sameAs": [X_URL, GITHUB_ORG_URL, SOURCE_REPO],
    }


def software(base: str) -> dict[str, object]:
    return {
        "@type": "SoftwareApplication",
        "name": "VMBridge",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "macOS 14 or later",
        "url": base + "/",
        "image": base + "/assets/og.png",
        "description": "VMBridge for Parallels Desktop. MCP server that gives an AI agent a virtual machine: screen, keyboard, mouse, commands, files, and snapshots.",
        "offers": {
            "@type": "Offer",
            "price": PRICE,
            "priceCurrency": "USD",
            "url": abs_url(base, "pricing"),
            "description": "One-time purchase of $9.99 with a 7-day full-featured free trial. Not a subscription.",
        },
    }


def breadcrumb(base: str, slug: str, title: str) -> dict[str, object]:
    items = [
        {"@type": "ListItem", "position": 1, "name": "VMBridge", "item": base + "/"},
    ]
    if slug:
        items.append({"@type": "ListItem", "position": 2, "name": title, "item": abs_url(base, slug)})
    return {"@type": "BreadcrumbList", "itemListElement": items}


def faq_ld(pairs: list[tuple[str, str]]) -> dict[str, object]:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in pairs
        ],
    }


def graph_for(base: str, page: dict[str, object]) -> dict[str, object]:
    slug = str(page["slug"])
    nodes: list[dict[str, object]] = [
        organization(base),
        breadcrumb(base, slug, str(page["h1"])),
    ]
    if page["kind"] in {"home", "pricing"}:
        nodes.append(software(base))
    faqs = page.get("faqs")
    if page.get("kind") == "faq" and isinstance(faqs, list) and faqs:
        nodes.append(faq_ld(faqs))  # type: ignore[arg-type]
    return {"@context": "https://schema.org", "@graph": nodes}


def article_body(page: dict[str, object]) -> str:
    slug = page["slug"]
    if slug == "mcp-server-for-parallels-desktop":
        return """
<p>An MCP server is the process an AI agent starts when it needs tools. VMBridge is that process for Parallels Desktop. The agent calls tools. VMBridge talks to Parallels. The guest's screen, keyboard, and mouse are what the agent uses.</p>
<h2>What the server exposes</h2>
<p>Screenshots come back with a coordinate map. OCR reads text on the screen. Clicks, typing, scrolling, and drags go through the Parallels Virtualization SDK, so the Mac does not ask for Accessibility or Screen Recording permission. Commands and files use Parallels Tools inside the guest.</p>
<ul>
<li>Window list and focus, open an app or a URL, search files by name.</li>
<li>Start, stop, pause, suspend, resume, restart, clone, create, and delete a VM.</li>
<li>Snapshots, sign-in at the lock screen, clipboard, and an activity log.</li>
</ul>
<h2>Where it listens</h2>
<p>On the Mac, the agent launches <code>vmbridge</code> over stdio. For an agent inside a VM, a daemon listens on 127.0.0.1 and on the Mac's address on the Parallels Shared and Host-Only networks. The default is not every interface on the Mac. A token for one VM is accepted only from that VM.</p>
<p><code>parallels-pro-mcp</code> and <code>guest-vm-agents</code> start the same server.</p>
<p>Related: <a href="../claude-code-control-a-vm/">Claude Code control a VM</a>, <a href="../ai-agent-virtual-machine-mac/">an AI agent virtual machine on a Mac</a>, <a href="../vs-vmpal/">VMBridge vs VMPal</a>.</p>
"""
    if slug == "claude-code-control-a-vm":
        return """
<h2>How do I connect Claude Code?</h2>
<p>On the Mac, with VMBridge installed:</p>
<pre><code>vmbridge connect claude-code</code></pre>
<p>Quit Claude Code and open it again so it loads the server. The app's Agents screen does the same click. Codex and Cursor use <code>vmbridge connect codex</code> and <code>vmbridge connect cursor</code>. <code>vmbridge connect list</code> shows every client name.</p>
<h2>What can Claude Code do in the VM?</h2>
<p>It can look at the guest screen, click and type, run a command as the signed-in user or as admin when you allow it, and copy files. Per-VM switches decide what is allowed. Pause all agents stops every agent at once. The activity log records what ran. Passwords typed at the login screen are not written into that log.</p>
<h2>Does the agent control the Mac?</h2>
<p>The computer-use tools act on the virtual machine, not on the Mac's own desktop. An agent that you also allow to run shell commands on the Mac is a separate permission in that agent. VMBridge's switches are the boundary for the VM.</p>
"""
    if slug == "ai-agent-virtual-machine-mac":
        return """
<h2>What do you need on the Mac?</h2>
<p>macOS 14 or later, Parallels Desktop Pro or Business, and VMBridge. Guests need Parallels Tools for commands, files, and the clipboard. The screen, keyboard, and mouse work without Tools, which is how an agent can drive an OS installer.</p>
<h2>Which guests?</h2>
<p>Linux, Windows, and macOS guests that Parallels Desktop can run. Pass <code>vm</code> when more than one VM is on. An agent inside a VM can only see its own VM. Its token is refused from any other address, including a clone.</p>
<h2>What stays on the Mac?</h2>
<p>The menu-bar app shows when an agent is working. Settings hold the trial and the license key. Sign-in passwords stay in the login Keychain under "VMBridge sign-in". Files an agent sends you land in ~/Downloads/From VMs.</p>
"""
    return ""


def compare_body() -> str:
    return """
<p>VMPal (TablePlus) first shipped on 6 October 2026. As of 11 October 2026 the public app was VMPal 0.69. Its headline feature is a built-in MCP server that gives an agent a whole computer. VMBridge brings that kind of agent access to virtual machines you already run in Parallels Desktop. Nothing from VMPal was copied. VMBridge uses Parallels' own SDK and CLI.</p>
<h2>What is the same idea?</h2>
<ul>
<li>An MCP server the agent can add in one step, including Claude Code, Codex, Cursor, and others.</li>
<li>The agent sees the display and can click, type, scroll, and drag.</li>
<li>Commands as the user or as admin, file copy, snapshots, and a stored sign-in password the agent does not receive.</li>
<li>Per-VM permission to let an agent control that VM, and a global switch for creating and deleting VMs.</li>
</ul>
<h2>What is different?</h2>
<ul>
<li>VMPal is a hypervisor. VMBridge is not. Parallels Desktop starts the VM, provides the disk format, and owns USB, graphics, and the guest OS installers.</li>
<li>VMBridge can focus a window, open an app or URL, search files by name, report the pointer after it moved it, pause the guest, and read its own activity log. Those tools were added because an agent driving a VM asks for them.</li>
<li>VMBridge does not record the screen as video. It returns still frames. A burst of images would fill the disk.</li>
<li>Neither product, as of that October 2026 check, ships the guest accessibility tree. VMBridge uses OCR. VMPal's public tracker listed an accessibility tree as requested, not shipped.</li>
<li>Snapshot rename is not available. prlctl has no rename command.</li>
</ul>
<h2>Which one is this page about?</h2>
<p>This page is about VMBridge. It is a factual comparison so you can tell the products apart. It is not a claim that the products are equivalent, and it is not an endorsement of either company.</p>
"""


def cta_block(checkout: str) -> str:
    return f"""
<div class="cta">
<a class="button" href="{esc(RELEASES_URL)}">Download DMG</a>
<a class="button ghost" href="{esc(checkout)}">Buy for $9.99</a>
</div>
<p class="fine">The notarized DMG is not a file on this site. It ships with the GitHub release when a signed build is published. The buy button is a Lemon Squeezy checkout placeholder, not a live store.</p>
"""


def pricing_body(checkout: str) -> str:
    return f"""
<p>The intended price is <strong>$9.99 USD, paid once</strong>. It is not a subscription. A full-featured trial lasts <strong>7 days</strong> from the first launch on that Mac.</p>
{cta_block(checkout)}
<ul>
<li>The trial clock is stored in the macOS login Keychain and in a file in Application Support. Removing only one copy does not start the trial over.</li>
<li>Setting the clock forward past the trial, then back, leaves the trial expired.</li>
<li>After a license key validates, the app keeps working for 14 days if the license server cannot be reached, as long as the key was active.</li>
<li>Keys are activated with the Lemon Squeezy License API. The app does not ship a store API secret.</li>
<li>You need macOS 14 or later and Parallels Desktop Pro or Business.</li>
</ul>
<p>The checkout URL and the product and variant ids are configuration (<code>VMBRIDGE_CHECKOUT_URL</code>, <code>VMBRIDGE_LEMON_PRODUCT_ID</code>, <code>VMBRIDGE_LEMON_VARIANT_ID</code>). Until those are set to the real store values, the buy button stays a checkout placeholder.</p>
<p>The license text in the repository is a draft and needs legal review before the app is sold. Read the <a href="../eula/">EULA page</a>.</p>
"""


def home_body(checkout: str) -> str:
    features = [
        (
            "Screen and input",
            "<code>vm_screenshot</code> (with a region zoom), <code>vm_read_screen</code> OCR, click, click text, type, key, scroll, drag, and mouse. <code>vm_cursor</code> reports the pointer only after this server moved it. <code>vm_act</code> batches steps. <code>vm_wait</code> waits for text, for text to leave, or for the screen to change. Input goes through the Parallels Virtualization SDK, so the Mac does not ask for Accessibility or Screen Recording permission. Screen and input work without Parallels Tools, including while an installer is on screen. Keystrokes use US key positions; other text should use paste, which needs Tools.",
        ),
        (
            "Commands and files",
            "<code>vm_run</code> is a shell line. <code>vm_exec</code> is an exact argv. Admin is a separate allow. Background jobs are <code>vm_job_status</code>, <code>vm_job_stop</code>, and <code>vm_job_list</code>. Read, write, and list files; copy to and from the guest; <code>vm_send_to_mac</code> lands in ~/Downloads/From VMs. <code>vm_windows</code> lists and focuses windows (Linux needs wmctrl). <code>vm_open</code> launches a quoted app or URL, not a shell command. <code>vm_find_files</code> matches file names, six folders deep, at most 200 paths, and is not a full-text search. On Windows, guest commands run as SYSTEM.",
        ),
        (
            "Virtual machines",
            "Start, stop, suspend, pause, resume, and restart. <code>vm_create</code> with <code>vm_systems</code> covers Ubuntu, Fedora, Debian, Kali, and macOS IPSW images. Windows is created with the Parallels assistant or an ISO; the agent can drive the installer. There is no unattended installer. <code>vm_run_ephemeral</code> copies a VM, runs, and deletes the copy. Snapshots: <code>snapshot_create</code>, <code>snapshot_revert</code>, <code>snapshot_delete</code>, <code>snapshot_list</code>. There is no rename. <code>vm_sign_in</code> types a Keychain password the agent never receives. Also: configure, shared folders, port forward, headless, autostart, delete to the Trash, status, list, install Tools, and the activity log.",
        ),
        (
            "Safety",
            "Each VM has its own agent-control switch. Creating, cloning, and deleting VMs need a global manage-all switch that is off by default, and the agent is asked to confirm the first time. Pause all agents stops every call. The activity log does not store typed secrets. An agent inside a VM gets an HTTP token that is accepted only from that VM's addresses. A clone cannot reuse it.",
        ),
    ]
    cards = []
    for title, body in features:
        cards.append(f"<article class=\"card\"><h3>{esc(title)}</h3><p>{body}</p></article>")
    return f"""
<p class="lede">VMBridge is the MCP server that gives Claude Code, Codex, Cursor, and other agents a Parallels Desktop virtual machine. The agent sees the guest screen and uses the guest keyboard and mouse. Your Mac desktop stays out of it.</p>
<ul class="facts">
<li>macOS 14 or later</li>
<li>Parallels Desktop Pro or Business</li>
<li>$9.99 once</li>
<li>7-day full-featured free trial</li>
</ul>
{cta_block(checkout)}
<figure class="demo">
<div class="poster" role="img" aria-label="Demo video placeholder. A walkthrough of an agent driving a Parallels Desktop virtual machine has not been published.">
<div class="chrome" aria-hidden="true"><span></span><span></span><span></span><b>VMBridge</b></div>
<div class="stage" aria-hidden="true"><span class="play"></span><p>Demo video</p></div>
</div>
<figcaption>Demo video placeholder. This page does not load a video file.</figcaption>
</figure>
<h2>Works with the agents you already run</h2>
<ul class="agents">
<li>Claude Code</li>
<li>Codex</li>
<li>Cursor</li>
</ul>
<p>Also Claude Desktop, Gemini CLI, Antigravity, VS Code, Windsurf, Cline, Grok, Zed, Kiro, OpenCode, Copilot CLI, and Devin. Connect with <code>vmbridge connect &lt;agent&gt;</code>. <code>parallels-pro-mcp</code> and <code>guest-vm-agents</code> are the same command.</p>
<h2>What the agent can actually call</h2>
<div class="grid">
{''.join(cards)}
</div>
<h2>What it does not do</h2>
<ul>
<li>It does not record video of the VM. Screenshots are still frames.</li>
<li>It does not read the guest accessibility tree. On-screen text is OCR.</li>
<li>It does not rename snapshots. prlctl has no rename command.</li>
<li>It does not pass through USB, and it does not install a guest unattended.</li>
<li>It is not a hypervisor. Parallels Desktop runs the VM.</li>
</ul>
<h2>Read more</h2>
<ul>
<li><a href="docs/quickstart/">Quickstart</a></li>
<li><a href="mcp-server-for-parallels-desktop/">MCP server for Parallels Desktop</a></li>
<li><a href="claude-code-control-a-vm/">Claude Code control a VM</a></li>
<li><a href="ai-agent-virtual-machine-mac/">AI agent virtual machine on a Mac</a></li>
<li><a href="vs-vmpal/">VMBridge vs VMPal</a></li>
<li><a href="pricing/">Pricing</a></li>
<li><a href="privacy/">Privacy policy</a></li>
</ul>
"""


def legal_body(slug: str) -> str:
    if slug == "privacy":
        return """
<p>VMBridge runs on your Mac and talks to virtual machines that Parallels Desktop is already running. This page describes that local app. It is not a promise about Parallels Desktop's own privacy policy.</p>
<h2>No analytics SDK</h2>
<p>The app does not include an analytics product, a telemetry pipeline, or a crash reporter such as Sentry. Pages on this website are static files. They do not set a cookie and they do not load a third-party script.</p>
<h2>What stays on the Mac</h2>
<ul>
<li>Trial state is stored in the login Keychain (service "VMBridge license") and in a license file under ~/Library/Application Support/VMBridge. An older "Parallels Pro MCP" folder is reused when it is the only copy, so the trial clock is not reset by the rename.</li>
<li>A guest sign-in password is stored in the login Keychain under "VMBridge sign-in". Tools do not return that password. The activity log records that a sign-in ran, not the secret.</li>
<li>The activity log records tool calls. Typed text and passwords are not written into it.</li>
<li>Files an agent sends to the Mac land in ~/Downloads/From VMs.</li>
</ul>
<h2>What is sent off the Mac</h2>
<p>Activating, validating, or deactivating a license key sends the key and an instance name to the Lemon Squeezy License API at api.lemonsqueezy.com. The app does not ship a store API secret. Until a real product id is configured, that check is not tied to a store product. The website's buy button is a checkout placeholder and does not complete a purchase.</p>
<p>Creating a Linux or macOS guest can download an image from the distribution's own publisher, or an IPSW from Apple, because that is how <code>vm_create</code> obtains install media. That download is the guest image, not a VMBridge account.</p>
<h2>Inside a virtual machine</h2>
<p>An agent running inside a guest uses a token that the daemon accepts only from that VM's addresses. The daemon listens on 127.0.0.1 and on the Parallels Shared and Host-Only networks. It does not listen on every interface unless you set that bind address yourself.</p>
"""
    if slug == "eula":
        return f"""
<p class="banner"><strong>Draft. Not legal advice.</strong> This license has not been reviewed by a lawyer. Do not treat this page as the terms of a sale, and do not ship it to customers until counsel has reviewed it.</p>
<p>The current draft is the <a href="{esc(LICENSE_URL)}">LICENSE</a> file in the source repository ({esc(SOURCE_REPO)}). Copyright 2026 Alex Chadwick. Portions derived from parallels-pro-mcp-server remain under the MIT License, copyright Jarod Wong. That notice is in LICENSES/MIT-upstream and THIRD_PARTY_NOTICES.</p>
<p>The draft describes a one-time purchase at an intended price of $9.99 and a 7-day full-featured trial. It is not in force for customers while the store is unconfigured and the text is still marked draft. The buy button on this site is a Lemon Squeezy checkout placeholder.</p>
<p><a href="{esc(LICENSE_URL)}">Read the draft EULA</a></p>
"""
    return f"""
<p>{esc(TRADEMARK)}</p>
<p>"Parallels Desktop" names the hypervisor VMBridge drives. It is not part of the product name. The product name is VMBridge. The tagline is "for Parallels Desktop".</p>
<p>VMPal is a virtual-machine application from TablePlus. The comparison on this site is factual. VMBridge does not include VMPal code and is not endorsed by TablePlus.</p>
<p>Nothing on this site grants a license to the Parallels, TablePlus, Claude, or other third-party marks.</p>
"""


def docs_index() -> str:
    items = [
        ("quickstart", "Quickstart", "Install, connect Claude Code, Codex, or Cursor, and stop the agent."),
        ("install", "Install", "The vmbridge command and where settings are stored."),
        ("trial-and-license", "Trial and license", "The 7-day trial, the $9.99 key, and the store settings."),
        ("mcp-tools", "MCP tools", "What an agent can call, and what VMBridge does not do."),
    ]
    lis = []
    for slug, title, blurb in items:
        href = slug + "/"
        lis.append(
            f'<li><a href="{esc(href)}">{esc(title)}</a> — {esc(blurb)} '
            f'<a href="{esc(href)}index.md">Markdown</a></li>'
        )
    return "<ul>\n" + "\n".join(lis) + "\n</ul>\n<p>Plain Markdown for each page is linked above and listed in <a href=\"../llms.txt\">llms.txt</a>.</p>"


def layout(base: str, page: dict[str, object], body: str, gsc: str, depth: int) -> str:
    slug = str(page["slug"])
    canonical = abs_url(base, slug)
    title = str(page["title"])
    description = str(page["description"])
    prefix = "../" * depth
    nav = []
    for item in pages():
        if not item.get("in_nav"):
            continue
        item_slug = str(item["slug"])
        href = prefix + item_slug + "/"
        current = ' aria-current="page"' if item_slug == slug or slug.startswith(item_slug + "/") else ""
        nav.append(f'<a href="{esc(href)}"{current}>{esc(str(item["nav"]))}</a>')
    home_href = prefix or "./"
    crumb = ""
    if slug and slug != "404":
        crumb = (
            f'<nav class="crumbs" aria-label="Breadcrumb"><a href="{esc(home_href)}">VMBridge</a> '
            f'<span aria-hidden="true">/</span> <span>{esc(str(page["h1"]))}</span></nav>'
        )
    ld = json.dumps(graph_for(base, page), ensure_ascii=False, indent=2)
    gsc_meta = f'<meta name="google-site-verification" content="{esc(gsc)}">'
    og = base + "/assets/og.png"
    legal = []
    for item_slug, label in (("privacy", "Privacy"), ("eula", "EULA (draft)"), ("trademark", "Trademark")):
        legal.append(f'<a href="{esc(prefix + item_slug + "/")}">{label}</a>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta name="theme-color" content="#0e3b32">
<meta property="og:type" content="website">
<meta property="og:site_name" content="VMBridge">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="VMBridge">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@vmbridgeapp">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og)}">
<meta name="twitter:image:alt" content="VMBridge">
{gsc_meta}
<link rel="icon" href="{esc(prefix)}assets/icon.png" type="image/png">
<link rel="stylesheet" href="{esc(prefix)}assets/site.css">
<script>
(function(){{try{{var t=localStorage.getItem("vmbridge-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();
</script>
<script type="application/ld+json">
{ld}
</script>
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="site">
<a class="brand" href="{esc(home_href)}">
<img src="{esc(prefix)}assets/icon.png" width="32" height="32" alt="VMBridge">
<span>VMBridge <small>for Parallels Desktop</small></span>
</a>
<nav aria-label="Primary">
{''.join(nav)}
</nav>
<button type="button" class="theme" data-theme-toggle aria-pressed="false">Theme</button>
</header>
<main id="content">
{crumb}
<h1>{esc(str(page["h1"]))}</h1>
{body}
</main>
<footer>
<nav aria-label="Legal">{' '.join(legal)}</nav>
<p><a href="{esc(X_URL)}">@vmbridgeapp</a> on X. Public GitHub organization <a href="{esc(GITHUB_ORG_URL)}">vmbridgeapp</a>. Source of this build: <a href="{esc(SOURCE_REPO)}">AlexmChadwick/Parallels-Agents</a>.</p>
<p>{esc(TRADEMARK)}</p>
<p>Upstream portions of the software are MIT-licensed, copyright Jarod Wong. The commercial terms are a draft and need legal review before sale.</p>
</footer>
<script>
(function(){{
  var root=document.documentElement, button=document.querySelector("[data-theme-toggle]");
  function current(){{
    var set=root.getAttribute("data-theme");
    if(set==="light"||set==="dark") return set;
    return window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";
  }}
  function paint(){{
    if(!button) return;
    var mode=current();
    button.textContent=mode==="dark"?"Light":"Dark";
    button.setAttribute("aria-pressed", mode==="dark"?"true":"false");
  }}
  paint();
  if(button) button.addEventListener("click", function(){{
    var next=current()==="dark"?"light":"dark";
    root.setAttribute("data-theme", next);
    try{{localStorage.setItem("vmbridge-theme", next);}}catch(e){{}}
    paint();
  }});
}})();
</script>
</body>
</html>
"""


def faq_html(pairs: list[tuple[str, str]]) -> str:
    blocks = []
    for question, answer in pairs:
        blocks.append(f"<section>\n<h2>{esc(question)}</h2>\n<p>{esc(answer)}</p>\n</section>")
    return "\n".join(blocks)


CSS = """
:root {
  color-scheme: light;
  --bg: #f3efe6;
  --bg-elev: #fffdf8;
  --ink: #1c1914;
  --muted: #5c564c;
  --line: #ddd4c4;
  --link: #0c3d6e;
  --accent: #0e3b32;
  --accent-ink: #f6f3ea;
  --gold: #8a5a12;
  --poster: #10241f;
  --poster-ink: #f4efe4;
  --shadow: 0 1px 0 rgba(28, 25, 20, .04);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #101411;
    --bg-elev: #1a211c;
    --ink: #f2eee6;
    --muted: #b7b0a4;
    --line: #314038;
    --link: #9ecbff;
    --accent: #8fd0bf;
    --accent-ink: #10211c;
    --gold: #e6c27a;
    --poster: #0c1814;
    --poster-ink: #f4efe4;
    --shadow: none;
  }
}
html[data-theme="dark"] {
  color-scheme: dark;
  --bg: #101411;
  --bg-elev: #1a211c;
  --ink: #f2eee6;
  --muted: #b7b0a4;
  --line: #314038;
  --link: #9ecbff;
  --accent: #8fd0bf;
  --accent-ink: #10211c;
  --gold: #e6c27a;
  --poster: #0c1814;
  --poster-ink: #f4efe4;
  --shadow: none;
}
* { box-sizing: border-box; }
html { scroll-behavior: auto; }
body { margin: 0; font: 18px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }
a { color: var(--link); }
a:hover { text-decoration-thickness: 2px; }
:focus-visible { outline: 2px solid var(--link); outline-offset: 3px; }
.skip { position: absolute; left: -999px; top: 0; background: var(--bg-elev); color: var(--ink); padding: .5rem; }
.skip:focus { left: .5rem; z-index: 2; }
header.site, main, footer { width: min(72rem, calc(100% - 2rem)); margin-inline: auto; }
header.site { display: flex; flex-wrap: wrap; gap: .75rem 1.5rem; align-items: center; justify-content: space-between; padding: 1rem 0; border-bottom: 1px solid var(--line); }
.brand { display: flex; gap: .6rem; align-items: center; color: inherit; text-decoration: none; font-weight: 650; }
.brand img { border-radius: 8px; }
.brand small { font-weight: 450; color: var(--muted); }
nav { display: flex; flex-wrap: wrap; gap: .35rem .9rem; }
nav a { text-decoration: none; }
nav a[aria-current="page"] { text-decoration: underline; text-underline-offset: .2em; }
button.theme { font: inherit; color: var(--ink); background: transparent; border: 1px solid var(--line); border-radius: 999px; padding: .3rem .75rem; cursor: pointer; }
main { padding: 1.75rem 0 3rem; }
h1 { font-size: clamp(2rem, 4vw, 3.1rem); line-height: 1.12; letter-spacing: -.02em; margin: 0 0 1rem; max-width: min(18ch, 100%); }
h2 { font-size: 1.45rem; line-height: 1.25; margin: 2rem 0 .6rem; }
h3 { font-size: 1.05rem; margin: 0 0 .4rem; }
p, li { max-width: 68ch; }
.lede { font-size: 1.2rem; max-width: 42rem; }
ul.facts, ul.agents { display: flex; flex-wrap: wrap; gap: .5rem; padding: 0; margin: 1.25rem 0; list-style: none; max-width: none; }
ul.facts li, ul.agents li { max-width: none; border: 1px solid var(--line); background: var(--bg-elev); border-radius: 999px; padding: .35rem .8rem; box-shadow: var(--shadow); }
ul.agents li { font-weight: 650; }
.cta { display: flex; flex-wrap: wrap; gap: .6rem; margin: 1.25rem 0 .4rem; }
.button { display: inline-block; background: var(--accent); color: var(--accent-ink); text-decoration: none; padding: .7rem 1.15rem; border-radius: 999px; font-weight: 650; }
.button.ghost { background: transparent; color: var(--ink); border: 1px solid var(--line); }
.button:hover { text-decoration: none; filter: brightness(1.08); }
.fine { color: var(--muted); font-size: .95rem; }
.demo { margin: 1.5rem 0 0; max-width: 52rem; }
.poster { background: var(--poster); color: var(--poster-ink); border-radius: 16px; min-height: 22rem; display: flex; flex-direction: column; border: 1px solid var(--line); overflow: hidden; }
.chrome { display: flex; gap: .4rem; align-items: center; padding: .7rem .9rem; background: rgba(255,255,255,.04); }
.chrome span { width: .7rem; height: .7rem; border-radius: 50%; background: #c4554a; }
.chrome span:nth-child(2) { background: #d6a13a; }
.chrome span:nth-child(3) { background: #3f8f62; }
.chrome b { margin-left: .4rem; font-weight: 600; font-size: .95rem; }
.stage { flex: 1; display: grid; place-items: center; text-align: center; padding: 2rem 1rem 2.5rem; }
.stage p { margin: .8rem 0 0; letter-spacing: .04em; text-transform: uppercase; font-size: .85rem; color: var(--poster-ink); max-width: none; }
.play { width: 4.5rem; height: 4.5rem; border-radius: 50%; background: rgba(255,255,255,.1); display: grid; place-items: center; }
.play::before { content: ""; border-style: solid; border-width: .7rem 0 .7rem 1.15rem; border-color: transparent transparent transparent var(--poster-ink); margin-left: .25rem; }
figcaption { color: var(--muted); font-size: .95rem; margin-top: .5rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 1rem; margin-top: .5rem; }
.card { background: var(--bg-elev); border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.1rem 1.1rem; box-shadow: var(--shadow); }
.card p { max-width: none; }
.banner { border: 1px solid var(--gold); background: var(--bg-elev); padding: .8rem 1rem; border-radius: 12px; }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: .92em; }
pre { background: var(--bg-elev); border: 1px solid var(--line); padding: .8rem 1rem; overflow: auto; max-width: 68ch; border-radius: 10px; }
table { border-collapse: collapse; width: min(100%, 68ch); }
th, td { border-bottom: 1px solid var(--line); text-align: left; padding: .4rem .6rem .4rem 0; vertical-align: top; }
.crumbs { color: var(--muted); margin-bottom: .5rem; }
footer { border-top: 1px solid var(--line); padding: 1.5rem 0 3rem; color: var(--muted); font-size: .95rem; }
footer p, footer nav { max-width: 72ch; }
footer nav { margin-bottom: .8rem; }
"""


def llms_txt(base: str) -> str:
    lines = [
        "# VMBridge",
        "",
        "> VMBridge is a macOS app for Parallels Desktop. It is an MCP server that gives an AI agent a virtual machine: screen, keyboard, mouse, commands, files, and snapshots. The intended price is $9.99 USD once, with a 7-day full-featured free trial. Parallels is a trademark of Parallels International GmbH. VMBridge is not affiliated with Parallels.",
        "",
        "The command is `vmbridge`. `parallels-pro-mcp` and `guest-vm-agents` are aliases. Default site: "
        + DEFAULT_BASE
        + ". Alternative host: "
        + ALTERNATE_BASE
        + ". X: @vmbridgeapp. Source repository: "
        + SOURCE_REPO
        + ".",
        "",
        "## Pages",
    ]
    for page in pages():
        slug = str(page["slug"])
        lines.append(f"- [{page['title']}]({abs_url(base, slug)}): {page['description']}")
    lines += [
        "",
        "## Docs (Markdown)",
        f"- [Quickstart]({abs_url(base, 'docs/quickstart')}index.md): install and connect an agent.",
        f"- [Install]({abs_url(base, 'docs/install')}index.md): install the vmbridge command.",
        f"- [Trial and license]({abs_url(base, 'docs/trial-and-license')}index.md): $9.99 one-time and the 7-day trial.",
        f"- [MCP tools]({abs_url(base, 'docs/mcp-tools')}index.md): what an agent can call.",
        f"- [Full text]({base}/llms-full.txt): quotable summary of the product, price, trial, and VMPal comparison.",
        "",
        "## Optional",
        f"- [Source repository]({SOURCE_REPO}): the fork that contains this site.",
        "",
    ]
    return "\n".join(lines)


def llms_full(base: str) -> str:
    chunks = [
        llms_txt(base).strip(),
        "",
        "## Quotable facts",
        "",
        "VMBridge is the product name. The tagline is for Parallels Desktop. The product name does not include the word Parallels.",
        "",
        "Hero: Let your AI agent drive Parallels Desktop VMs.",
        "",
        "Price: $9.99 USD, one time. Trial: 7 days, full-featured, starting at first launch. Offline use after a successful license check: 14 days. License checks use the Lemon Squeezy License API and do not require a store API secret in the app. The public checkout URL is a placeholder until VMBRIDGE_CHECKOUT_URL and the Lemon product ids are set. The license text is a draft and is not legal advice.",
        "",
        "Host requirements: macOS 14 or later, Parallels Desktop Pro or Business. The command is vmbridge. Works with Claude Code, Codex, Cursor, and other MCP clients.",
        "",
        "VMBridge is not a hypervisor. It drives virtual machines that Parallels Desktop runs. It does not record VM video, does not expose a guest accessibility tree (it uses OCR), and cannot rename snapshots because prlctl has no rename.",
        "",
        "VMPal is a VM application from TablePlus, first released 6 October 2026. Public notes as of 11 October 2026 refer to VMPal 0.69. VMBridge is an independent implementation. It contains no VMPal code and is not affiliated with TablePlus.",
        "",
        TRADEMARK,
        "",
        "## Docs",
        "",
    ]
    for name, text in DOCS.items():
        chunks.append(text.strip())
        chunks.append("")
        chunks.append(f"Source: {abs_url(base, 'docs/' + name)}index.md")
        chunks.append("")
    return "\n".join(chunks)


def robots(base: str) -> str:
    bots = ["*", "GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "Googlebot", "Bingbot"]
    blocks = []
    for bot in bots:
        blocks.append(f"User-agent: {bot}\nAllow: /\n")
    blocks.append(f"Sitemap: {base}/sitemap.xml\n")
    return "\n".join(blocks)


def sitemap(base: str) -> str:
    urls = [abs_url(base, str(page["slug"])) for page in pages()]
    for slug in DOCS:
        urls.append(abs_url(base, "docs/" + slug))
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        body.append("  <url>")
        body.append(f"    <loc>{esc(url)}</loc>")
        body.append(f"    <lastmod>{UPDATED}</lastmod>")
        body.append("  </url>")
    body.append("</urlset>")
    return "\n".join(body) + "\n"


def appcast(base: str, version: str) -> str:
    template = (ROOT / "macos" / "Sparkle" / "appcast-template.xml").read_text(encoding="utf-8")
    return (
        template.replace("SITE_BASE_URL", base)
        .replace("VERSION", version)
        .replace("BUILD", "1")
    )


def build(out: Path, base: str, gsc: str) -> None:
    if out.exists():
        for child in sorted(out.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
    out.mkdir(parents=True, exist_ok=True)
    assets = out / "assets"
    assets.mkdir()
    (assets / "site.css").write_text(CSS, encoding="utf-8")
    write_icon(assets / "icon.png")
    write_og(assets / "og.png")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text(robots(base), encoding="utf-8")
    (out / "sitemap.xml").write_text(sitemap(base), encoding="utf-8")
    (out / "llms.txt").write_text(llms_txt(base), encoding="utf-8")
    (out / "llms-full.txt").write_text(llms_full(base), encoding="utf-8")
    version = "1.0.0"
    init = ROOT / "parallels_mcp" / "__init__.py"
    for line in init.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            version = line.split('"')[1]
    (out / "appcast.xml").write_text(appcast(base, version), encoding="utf-8")
    checkout = checkout_url()

    for page in pages():
        slug = str(page["slug"])
        kind = page["kind"]
        if kind == "home":
            body = home_body(checkout) + "<h2>Common questions</h2>\n" + faq_html(page["faqs"])  # type: ignore[arg-type]
            depth = 0
            target = out / "index.html"
        elif kind == "faq":
            body = faq_html(page["faqs"])  # type: ignore[arg-type]
            depth = 1
            target = out / slug / "index.html"
        elif kind == "compare":
            body = f"<p class=\"lede\">{esc(str(page['lead']))}</p>\n" + compare_body()
            depth = 1
            target = out / slug / "index.html"
        elif kind == "pricing":
            body = f"<p class=\"lede\">{esc(str(page['lead']))}</p>\n" + pricing_body(checkout)
            depth = 1
            target = out / slug / "index.html"
        elif kind == "docs":
            body = docs_index()
            depth = 1
            target = out / slug / "index.html"
        elif kind == "legal":
            body = legal_body(slug)
            depth = 1
            target = out / slug / "index.html"
        else:
            body = f"<p class=\"lede\">{esc(str(page['lead']))}</p>\n" + article_body(page)
            depth = 1
            target = out / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(layout(base, page, body, gsc, depth), encoding="utf-8")

    for slug, text in DOCS.items():
        folder = out / "docs" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.md").write_text(text.strip() + "\n", encoding="utf-8")
        first = text.strip().splitlines()
        doc_page = {
            "slug": f"docs/{slug}",
            "nav": "Docs",
            "title": first[0].lstrip("# ").strip() + " | VMBridge",
            "description": "VMBridge for Parallels Desktop. " + first[2][:140],
            "h1": first[0].lstrip("# ").strip(),
            "kind": "doc",
        }
        body_md = "\n".join(first[1:]).strip()
        html_doc = layout(base, doc_page, render_markdown(body_md), gsc, depth=2)
        (folder / "index.html").write_text(html_doc, encoding="utf-8")

    missing = out / "404.html"
    missing.write_text(
        layout(
            base,
            {
                "slug": "404",
                "title": "Page not found | VMBridge",
                "description": "That page is not on the VMBridge site.",
                "h1": "Page not found",
                "kind": "missing",
            },
            '<p>The page is not here. Go back to <a href="/">VMBridge</a>.</p>',
            gsc,
            depth=0,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the VMBridge static site.")
    parser.add_argument("--out", type=Path, default=ROOT / "site" / "out")
    parser.add_argument("--base-url", default=None, help="Overrides VMBRIDGE_SITE_URL.")
    args = parser.parse_args()
    gsc = os.environ.get("VMBRIDGE_GSC_VERIFICATION", "").strip() or GSC_PLACEHOLDER
    build(args.out, site_base(args.base_url), gsc)


if __name__ == "__main__":
    main()
