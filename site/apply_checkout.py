#!/usr/bin/env python3
"""Point the published site generator at the VMBridge Lemon Squeezy store.

Idempotent: a string that is already updated is left alone. A missing
old string and a missing new string is a hard failure.
"""

from pathlib import Path

CHECKOUT = "https://vmbridge.lemonsqueezy.com/checkout/buy/cbca7388-4a0c-4ccd-8e83-2e15f8e4f54f"

REPLACEMENTS = [
    (
        'DEFAULT_CHECKOUT = "https://example.lemonsqueezy.com/checkout/buy/PLACEHOLDER"',
        'DEFAULT_CHECKOUT = "'
        + CHECKOUT
        + '"\n'
        'STORE_ID = "497255"\n'
        'STORE_SLUG = "vmbridge"\n'
        'PRODUCT_ID = "1437706"\n'
        'VARIANT_ID = "2244841"',
    ),
    (
        "Open VMBridge. The 7-day full-featured trial starts at first launch on that Mac. The intended price after the trial is $9.99 once. The Lemon Squeezy link on the site is a checkout placeholder until the store ids are set. It is not a live store.",
        "Open VMBridge. The 7-day full-featured trial starts at first launch on that Mac. The price after the trial is $9.99 once. Buy opens the Lemon Squeezy checkout. The store is in test mode pending approval; the URL stays the same when the store is live.",
    ),
    (
        "These are public identifiers, not secrets:\n"
        "\n"
        "- VMBRIDGE_CHECKOUT_URL\n"
        "- VMBRIDGE_LEMON_PRODUCT_ID\n"
        "- VMBRIDGE_LEMON_VARIANT_ID\n"
        "\n"
        "GUEST_VM_AGENTS_CHECKOUT_URL, GUEST_VM_AGENTS_LEMON_PRODUCT_ID, and GUEST_VM_AGENTS_LEMON_VARIANT_ID still work.\n"
        "\n"
        "Until a real product id is set, the license check is not tied to a store product. Set the ids before selling. The license text in the repository is a draft and needs legal review before the app is sold.",
        "These public identifiers are the defaults. Environment variables override them. They are not secrets.\n"
        "\n"
        "- Store id 497255, slug vmbridge\n"
        "- Product id 1437706\n"
        "- Variant id 2244841\n"
        "- Checkout "
        + CHECKOUT
        + "\n"
        "- A license key can be active on 2 machines. It does not expire.\n"
        "\n"
        "VMBRIDGE_CHECKOUT_URL, VMBRIDGE_LEMON_STORE_ID, VMBRIDGE_LEMON_PRODUCT_ID, and VMBRIDGE_LEMON_VARIANT_ID override the defaults. GUEST_VM_AGENTS_CHECKOUT_URL, GUEST_VM_AGENTS_LEMON_STORE_ID, GUEST_VM_AGENTS_LEMON_PRODUCT_ID, and GUEST_VM_AGENTS_LEMON_VARIANT_ID still work.\n"
        "\n"
        "A key whose Lemon Squeezy meta store_id or product_id does not match is rejected. Set an id to 0 or placeholder to skip that one check. The license text in the repository is a draft and needs legal review before the app is sold. The Lemon Squeezy store is in test mode pending approval. The checkout URL stays the same when the store is live.",
    ),
    (
        "A one-time license key for VMBridge, not a subscription. The 7-day trial is full-featured and starts at first launch. A validated key keeps working for 14 days without reaching the license server. The checkout on this site is a Lemon Squeezy placeholder until the store ids are set.",
        "A one-time license key for VMBridge, not a subscription. It can be active on 2 machines and does not expire. The 7-day trial is full-featured and starts at first launch. A validated key keeps working for 14 days without reaching the license server. The Lemon Squeezy store is in test mode pending approval; the checkout URL stays the same when the store is live.",
    ),
    (
        '            "url": abs_url(base, "pricing"),',
        '            "url": checkout_url(),',
    ),
    (
        "The buy button is a Lemon Squeezy checkout placeholder, not a live store.",
        "Buy opens the Lemon Squeezy checkout. The store is in test mode pending approval; this URL stays the same when the store is live.",
    ),
    (
        "The checkout URL and the product and variant ids are configuration (<code>VMBRIDGE_CHECKOUT_URL</code>, <code>VMBRIDGE_LEMON_PRODUCT_ID</code>, <code>VMBRIDGE_LEMON_VARIANT_ID</code>). Until those are set to the real store values, the buy button stays a checkout placeholder.",
        "The checkout is the VMBridge Lemon Squeezy store (slug vmbridge, store id 497255, product id 1437706, variant id 2244841). A license key can be active on 2 machines and does not expire. <code>VMBRIDGE_CHECKOUT_URL</code>, <code>VMBRIDGE_LEMON_STORE_ID</code>, <code>VMBRIDGE_LEMON_PRODUCT_ID</code>, and <code>VMBRIDGE_LEMON_VARIANT_ID</code> still override those defaults. A key is refused when its store id or product id does not match.",
    ),
    (
        "Until a real product id is configured, that check is not tied to a store product. The website's buy button is a checkout placeholder and does not complete a purchase.",
        "A key is accepted only when its store id and product id match VMBridge. The website buy button opens that checkout. The store is in test mode pending approval.",
    ),
    (
        "It is not in force for customers while the store is unconfigured and the text is still marked draft. The buy button on this site is a Lemon Squeezy checkout placeholder.",
        "The text is still marked draft and is not in force as customer terms. The buy button opens the Lemon Squeezy checkout. The store is in test mode pending approval.",
    ),
    (
        "License checks use the Lemon Squeezy License API and do not require a store API secret in the app. The public checkout URL is a placeholder until VMBRIDGE_CHECKOUT_URL and the Lemon product ids are set.",
        "A license key can be active on 2 machines and does not expire. License checks use the Lemon Squeezy License API and do not require a store API secret in the app. The default store id is 497255 (slug vmbridge), product id 1437706, variant id 2244841. Checkout: "
        + CHECKOUT
        + ". The store is in test mode pending approval; that URL stays the same when the store is live. A key whose store id or product id does not match is rejected.",
    ),
]


def apply(text: str) -> str:
    for old, new in REPLACEMENTS:
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise SystemExit("checkout patch did not match the generator")
    return text


def main() -> None:
    path = Path("site/build_site.py")
    updated = apply(path.read_text())
    path.write_text(updated)


if __name__ == "__main__":
    main()
