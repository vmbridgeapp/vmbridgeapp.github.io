# VMBridge site

Published site for VMBridge. GitHub Pages should deploy from the `main` branch, folder `/` (root).

Build the files in the source repository:

```bash
VMBRIDGE_SITE_URL=https://vmbridgeapp.github.io python3 site/build_site.py --out site/out
```

Copy `site/out` onto this branch and keep `.github/`. `scripts/publish-site.sh` in the source repository does that copy when git can push to this repo.

`.github/workflows/images.yml` rewrites `assets/icon.png` and `assets/og.png` after a text publish. Those are PNG files, and a text upload corrupts them.
