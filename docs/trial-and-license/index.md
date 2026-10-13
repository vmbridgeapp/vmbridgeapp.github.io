# Trial and license

VMBridge is a one-time purchase of $10 with a 7-day full-featured free trial. The trial starts at first launch on that Mac. It is stored in license.json and in the macOS login Keychain. Deleting only one of those copies does not restart the trial. Setting the clock back does not extend it.

## After you buy

A license key is activated with the Lemon Squeezy License API. No store API secret is shipped in the app. After a successful check, the app keeps working offline for 14 days.

## Store settings

These are public identifiers, not secrets:

- VMBRIDGE_CHECKOUT_URL
- VMBRIDGE_LEMON_PRODUCT_ID
- VMBRIDGE_LEMON_VARIANT_ID

GUEST_VM_AGENTS_CHECKOUT_URL, GUEST_VM_AGENTS_LEMON_PRODUCT_ID, and GUEST_VM_AGENTS_LEMON_VARIANT_ID still work.

Until a real product id is set, the license check is not tied to a store product. Set the ids before selling. The license text in the repository is a draft and needs legal review before the app is sold.
