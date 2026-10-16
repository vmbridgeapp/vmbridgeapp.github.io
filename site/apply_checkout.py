#!/usr/bin/env python3
"""Point the published site generator at the Polar checkout.

Idempotent. A generator that already uses the Polar URL is left alone.
A leftover Lemon Squeezy checkout URL is replaced. A generator with
neither URL is a hard failure, so a partial edit cannot publish quietly.
"""

from pathlib import Path

CHECKOUT = "https://buy.polar.sh/polar_cl_xQ7772UMU2C5OTxywIp6Sr75YFJqRNYjm1iIW0sAEL8"
LEMON_CHECKOUT = "https://vmbridge.lemonsqueezy.com/checkout/buy/cbca7388-4a0c-4ccd-8e83-2e15f8e4f54f"
PLACEHOLDER = "https://example.lemonsqueezy.com/checkout/buy/PLACEHOLDER"


def apply(text: str) -> str:
    text = text.replace(LEMON_CHECKOUT, CHECKOUT)
    text = text.replace(PLACEHOLDER, CHECKOUT)
    if CHECKOUT not in text:
        raise SystemExit("Polar checkout URL missing from the generator")
    if "lemonsqueezy.com" in text:
        raise SystemExit("Lemon Squeezy checkout URL still in the generator")
    return text


def main() -> None:
    path = Path("site/build_site.py")
    updated = apply(path.read_text())
    if updated != path.read_text():
        path.write_text(updated)


if __name__ == "__main__":
    main()
