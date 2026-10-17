# VEILFORGE H17 isolated branch ledger

Branch: feature/veilforge-live-replay-retry-20261017-h17
Parent: 9b24153018d061a76530e48f04e98978f445676e (factory run 39077062255: 18/18 jobs passed).
Original review handoff: run 38993296206, artifact 12085917087.
Selected defect: delayed same-role compositor replay may escape capture retries despite H16 downstream rejection.
Source: veilforge/android_visual_qa.py; independent evidence reader: veilforge/vq_android_camera_evidence.py.
Before: H16 154/154 accepted frames; original sword edge-on yaw0/25 is intentional. H13 measured improved sword broadside camera framing.
Change: retry and archive exact decoded-pixel replay against every previously accepted same-role frame, not only the immediately previous one. Add unit regressions, report counter and archived replay accounting.
After: PENDING new full 4-emulator, semantic/LOD Android run.
No asset or game change; no QA relaxation, auto-merge, auto-promotion or human-artistic acceptance.
