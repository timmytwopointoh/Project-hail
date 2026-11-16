# VEILFORGE Nexus Consumer v1.3.0 — trusted-signing preparation test

This **public EXE installer is a SELF-SIGNED TEST BUILD**, not a CA-trusted or
commercially trusted release. Windows may show an UnknownError/SmartScreen warning.

- Windows installer: 760160 bytes
- SHA-256: `c907c3d820102a397eb8a95a968bdc01005bba3a2232160ade8c1e8e141878c5`
- Owner-PC local signer thumbprint: `F7AA1F5846BF49F9512981412A27E9C29BD116FD`
- Native C# build and all automated signing regression checks: PASS
- CA-issued publisher certificates available on owner PC: 0
- Full commercial Windows trust / real CA signer: NOT VERIFIED
- New features: independent game creators' local Windows test identity and Android
  keystore, real Godot export code for EXE+PCK/APK, Save As, verified source
  QA, and a CA-issued publisher certificate check that blocks untrusted signing.
- Actual game export, live GUI, Android installation, third-party Windows trust,
  and SmartScreen reputation: NOT VERIFIED.
- Developer source, private keys, user workspace files: NOT INCLUDED.

A CA-issued code-signing certificate or Microsoft Artifact Signing Public Trust
identity validation must be obtained separately before a Windows-trusted release.
