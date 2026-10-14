# Trial and license

VMBridge is a one-time purchase of $9.99 with a 7-day full-featured free trial. The trial starts at first launch on that Mac. It is stored in license.json and in the macOS login Keychain. Deleting only one of those copies does not restart the trial. Setting the clock back does not extend it.

## After you buy

A license key is activated with the Lemon Squeezy License API. No store API secret is shipped in the app. After a successful check, the app keeps working offline for 14 days.

## Store settings

These public identifiers are the defaults. Environment variables override them. They are not secrets.

- Store id 497255, slug vmbridge
- Product id 1437706
- Variant id 2244841
- Checkout https://vmbridge.lemonsqueezy.com/checkout/buy/cbca7388-4a0c-4ccd-8e83-2e15f8e4f54f
- A license key can be active on 2 machines. It does not expire.

VMBRIDGE_CHECKOUT_URL, VMBRIDGE_LEMON_STORE_ID, VMBRIDGE_LEMON_PRODUCT_ID, and VMBRIDGE_LEMON_VARIANT_ID override the defaults. GUEST_VM_AGENTS_CHECKOUT_URL, GUEST_VM_AGENTS_LEMON_STORE_ID, GUEST_VM_AGENTS_LEMON_PRODUCT_ID, and GUEST_VM_AGENTS_LEMON_VARIANT_ID still work.

A key whose Lemon Squeezy meta store_id or product_id does not match is rejected. Set an id to 0 or placeholder to skip that one check. The license text in the repository is a draft and needs legal review before the app is sold. The Lemon Squeezy store is in test mode pending approval. The checkout URL stays the same when the store is live.
