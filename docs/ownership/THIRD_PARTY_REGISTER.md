# Third-party component inventory (initial review; NOT clearance)\n\nProject claimant: Timothy Harris (GitHub: timmytwopointoh).

Project-hail includes original project-specific code and external tooling.
A repository ownership claim does not include intellectual-property rights
in the external materials. Licenses and obligations MUST be checked before
distribution, publication, commercial game shipment or licensing the engine.

| Component / role | How used in this repository | Present conclusion |
|---|---|---|
| GitHub Actions service and runners | CI execution, checks, artifacts | GitHub terms apply; no claim of ownership |
| actions/checkout, upload/download-artifact, setup-* | Executed from workflow YAML | Exact version and licensing to verify |
| reactivecircus/android-emulator-runner@v2 | Android emulator workflows | Upstream license/notice to verify |
| Android SDK, AOSP emulator, Android Gradle plugin | Builds/tests Android apps | Android/Google tool licenses apply |
| Gradle and Java/JDK distributions | Building source and running test tools | Upstream redistribution terms to verify |
| Python Pillow | Procedural material baking, images and image analysis | License and binary dependencies to verify |
| Qwen2.5-Coder (0.5b, 1.5b, 3b) | Optional local coding proposals | External model weights; exact model-card license/version to verify |
| Ollama | Local host/installer for third-party model | Upstream software and downloaded model terms to verify |
| Other GitHub Action dependencies | Test/build workflows | Generate lockfile/SBOM and verify |

**No external components are marked cleared in this initial record.**
The table is an initial discovery list, not an exhaustive SBOM or legal
opinion. Retain actual upstream LICENSE/NOTICE files wherever required.
Keep records of downloaded model tags, digests, source asset provenance,
stock textures, fonts, images and other resources, and human contributors.

Future tooling should export SPDX or CycloneDX data at the exact GitHub SHA.
Commercial use depends on actual licenses and contributor agreements;
some materials may be subject to more than copyright.
