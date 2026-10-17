# VEILFORGE per-angle REVIEW provenance — isolated branch ledger

Verified camera-fit parent: `27399138080f36cc133b85e927c0b5041a28f2a7`, factory run `38996754894` with 19/19 successful jobs, four Android 15 emulators, 154 captured frames and independent semantic/LOD reviewers. The original five REVIEW proposals originate from source `85f634f58d0a5863186b22a90c1fd74292cc8c2b`, run `38993296206`, task artifact `12085917087`.

The camera correction for `ancient_tree` was already completed and validated on its separate branch: actual frame-fresh baseline `325ca6df457ee77a971ae2a4b1fde8a5c7223a6f`, run `38995400473`, compared to `27399138080f36cc133b85e927c0b5041a28f2a7`, run `38996754894`. Tree coverage min 0.00079→0.00138, median 0.00792→0.01277, max 0.01858→0.02905. All 14 corresponding views improved, with 14 unique PNG SHA hashes in each set. These are measured color-threshold silhouettes, not subjective artistic quality.

This branch changes only review-evidence integrity: verify all 154 PNG SHA-256 hashes, camera angles, unique per-asset frames, Android 15 API, same APK digest across roles, source commit, and semantic min/max; then append 14 exact screenshot paths/hashes/angles to each REVIEW proposal. No model rewrite, approval, queue mutation, threshold weakening, renderer change, game change or asset promotion. Rejected: sword yaw 0/25 edge-on visibility is not proof of missing blade geometry; the static `queue_backlog.json` is unrelated to dynamic REVIEW tasks.

CI run, resulting SHA and all QA gates must be checked after push. Keep source snapshots and accepted/rejected screenshot evidence. No photorealism, physical-device performance or final human-artistic acceptance claimed.
