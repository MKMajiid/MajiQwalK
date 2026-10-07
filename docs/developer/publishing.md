# Publishing

The public source repository is `MKMajiid/MajiQwalK`.

Before creating the first tagged pre-release:
1. Require the Linux/Windows CI matrix to pass on the exact release commit.
2. Validate the portable candidate on each target operating system.
3. Retain Apache-2.0 `LICENSE`, `NOTICE`, citation metadata and all third-party notices required by redistributed dependencies.
4. Confirm that README feature claims match executable tests.
5. Tag the validated commit and create release artifacts from that commit.

Do not add a DOI until a DOI has actually been minted for the release.
