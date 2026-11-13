# Trial and license

VMBridge is a one-time purchase of $9.99 with a 7-day full-featured free trial. The trial starts at first launch on that Mac. It is stored in license.json in Application Support. Deleting that file alone does not reset the trial: the earliest start is also kept in a hidden .trial-origin file and in the preference VMBridgeTrialStartedAt. Setting the clock back does not extend it.

## After you buy

A license key is activated with Polar's customer-portal license-key API. No API token is shipped in the app. After a successful check, the app keeps working offline for 14 days.

## Store settings

These public identifiers are the defaults. Environment variables override them. They are not secrets.

- Polar organization id e1d27794-4788-4325-8d9c-399c4814fdb3
- Checkout https://buy.polar.sh/polar_cl_xQ7772UMU2C5OTxywIp6Sr75YFJqRNYjm1iIW0sAEL8
- A license key looks like VMB-<key>. It can be active on 3 machines. It does not expire.

VMBRIDGE_CHECKOUT_URL and VMBRIDGE_POLAR_ORGANIZATION_ID override the defaults. GUEST_VM_AGENTS_CHECKOUT_URL still works for the checkout URL.

A key whose organization id does not match is rejected. Set VMBRIDGE_POLAR_ORGANIZATION_ID to 0 or placeholder to skip that check. The end user license is available on the EULA page and inside the app. The seller is Chadwick Labs, an individual seller in the United States. Polar Software, Inc. is the merchant of record. Support is support@vmbridge.app. Governing law is the State of Connecticut, United States.
