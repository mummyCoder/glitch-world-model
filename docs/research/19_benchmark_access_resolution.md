# Benchmark Access Resolution

## 1. Repo-state gate

- Checked on 2026-06-08.
- Branch: `main`.
- Working tree was clean before Phase 1B edits.
- Phase 1 docs are tracked:
  - `docs/research/17_source_verification_log.md`
  - `docs/research/18_full_paper_readiness_gap.md`
  - `docs/research/references.bib`
  - `docs/research/02_literature_matrix.md`
  - `docs/research/04_dataset_benchmark_map.md`
  - `docs/research/16_claim_registry.md`
- Local `main` was ahead of `origin/main` by commit `a06a972` only, then pushed successfully before continuing.

## 2. Resolution summary

TempGlitch is now the selected Phase 2 benchmark. The key change from Phase 1 is that a real public artifact was verified on 2026-06-08 at the Hugging Face dataset page:

- Dataset page: <https://huggingface.co/datasets/asgaardlab/TempGlitch>
- Access type: public download
- License: MIT
- Public size shown on the dataset page: `60.3 GB`
- Public row count shown on the dataset page: `1,500`

The public Hugging Face artifact exposes:

- one `train` split with `1,500` videos
- a `video` column
- a `label` column
- file paths grouped into five glitch categories with paired `Buggy` / `Normal` folders

The public artifact does not currently verify:

- finer temporal span annotations beyond the binary per-video label
- an official held-out split beyond the public `train` split
- an official evaluation script on the public dataset page

That is good enough for a real binary clip-level smoke pipeline in this repo, but not enough to justify temporal localization claims by itself.

## 3. Benchmark resolution table

| Benchmark | Official public artifact verified on 2026-06-08? | License / access | Public schema verified | Operational fit for this repo | Decision |
| --- | --- | --- | --- | --- | --- |
| TempGlitch | Yes | MIT; public HF dataset page and direct MP4 URLs | `video`, `label`; five category folders; paired `Buggy` / `Normal` clips; one public `train` split | Strong. Can download a tiny subset, preprocess each video, merge manifests, and map buggy videos to full-video positive intervals without changing CSV interfaces | Selected for Phase 2 |
| VideoGlitchBench / GliDe | Paper verified, public artifact not confirmed | Public download path still unverified | Paper claims detailed descriptions plus temporal spans, but no public repo / dataset was confirmed from primary-source checks | Weak today. Good paper-facing related work, not yet runnable here | Not selected |
| World of Bugs | Yes | Official site, public GitHub repo, public Kaggle links for train/test data | Platform docs, standalone builds, and train/test data links are public; direct mapping to this repo's labels CSV still requires environment-specific conversion work | Medium. Operationally heavier than TempGlitch for a fast smoke test | Fallback 1 |
| GlitchBench | Yes | MIT; public HF dataset | image-level rows with text metadata only | Good static-image fallback, but cannot support temporal detection claims | Fallback 2 |

## 4. TempGlitch public-artifact notes

Verified from the public dataset page and public API endpoints on 2026-06-08:

- dataset id: `asgaardlab/TempGlitch`
- public categories:
  - `Blinking`
  - `Frozen Animation`
  - `Shooting Error`
  - `Stuck in Place`
  - `Velocity Bug`
- public file layout is balanced:
  - each category has `150` `Buggy` videos
  - each category has `150` `Normal` videos
- total videos from public file listing: `1,500`
- public label names exposed by the dataset server:
  - `Buggy`
  - `Buggy `
  - `Normal`

The trailing-space label variant `Buggy ` appears to come from the public folder name `Stuck in Place/Buggy ` and should be normalized in local tooling.

## 5. Why TempGlitch wins operationally

- It is the only current benchmark candidate here with a verified public video artifact, a clear permissive license, and direct downloadable sample URLs.
- Its binary paired-video setup matches this repo's current anomaly-style baselines better than an open-ended language-grounding benchmark.
- A tiny smoke subset can be evaluated without rewriting the scorer registry or breaking the existing `manifest.csv`, labels CSV, `scores.csv`, and `metrics.json` interfaces.

## 6. Remaining limitations after Phase 1B

- The public TempGlitch artifact is clip-level binary, not verified as fine-grained temporal-span supervision.
- The public artifact exposes only a `train` split, so any local split protocol must be documented as repo-defined rather than official.
- Any near-term result in this repo should be described as a smoke test or baseline feasibility result, not a paper-ready benchmark comparison.
- VideoGlitchBench remains interesting because it promises richer temporal grounding, but it is not an executable benchmark in this repo yet.

## 7. Phase 2 implication

Proceed with TempGlitch using the narrowest valid claim:

- public benchmark access is verified
- local smoke evaluation will be binary clip-level detection on a tiny TempGlitch subset
- positive labels will map buggy videos to full-video positive intervals until richer public span annotations are verified
