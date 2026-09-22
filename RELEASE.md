# Verified initial release

Published from main on 22 September 2026 (Asia/Riyadh):

- Commit: `d4e36c44535ed09bc14bc2c1acb2078a2d0555b4`
- [Green CI run](https://github.com/Nasser-Alsuduni0/rasheed-NasserAlsuduni-SDA-AIE-113/actions/runs/35659835859)
- Image: `ghcr.io/nasser-alsuduni0/rasheed-capstone:d4e36c44535ed09bc14bc2c1acb2078a2d0555b4`
- Digest: `sha256:dd8f0881331bff9e18f7fb2a52ada8bd30766ad8f9b2865c5839c1a9b6b7f57e`

All five jobs passed: lint, secrets, test, image-smoke, publish.
An empty Docker configuration directory was used for a successful anonymous pull.
No Docker/GitHub login is needed to download this public release.

Run the verified artifact without rebuilding (PowerShell, repository root):

```powershell
$env:RASHEED_IMAGE = "ghcr.io/nasser-alsuduni0/rasheed-capstone@sha256:dd8f0881331bff9e18f7fb2a52ada8bd30766ad8f9b2865c5839c1a9b6b7f57e"
docker compose pull
docker compose up --detach --no-build --wait
```

This file records the initial application release; later documentation-only commits
can produce additional image tags without invalidating this verified digest.
For newer application releases, consult their successful CI publish summaries.
