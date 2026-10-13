# VMBridge site

GitHub Pages deploys this repository from the `main` branch, folder `/`.
The public site is https://vmbridgeapp.github.io.

`.github/workflows/build.yml` rebuilds the HTML when `site/build_site.py` or `site/gen/` changes, then commits the pages at the repository root. It keeps `.github/`, `site/`, `macos/`, `parallels_mcp/`, and this README.

`site/build_site.py` is the generator. `site/gen/part*` is a gzip+base64 copy used only when that file is missing. `.github/workflows/images.yml` rewrites `assets/icon.png` and `assets/og.png` if a text upload corrupts the PNGs.

From the source repository, `scripts/publish-site.sh` builds with `VMBRIDGE_SITE_URL=https://vmbridgeapp.github.io` and pushes `site/out` here. It needs `VMBRIDGE_PAGES_TOKEN` with contents write on this repository. The Cursor GitHub App installed on the private source repository cannot push here.
