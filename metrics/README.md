# Sufficient-statistic replication module

This module uses non-identifying occupation-by-year and occupation-profile aggregates. It does not contain user-generated text, user/video IDs, employer records, or raw platform data. Source hashes and white-listed columns are recorded in `source_manifest.json`.

## Independently recomputed empirical results

Run from any directory, using Python 3.10 or later (standard library only):

```text
python recompute_metrics.py --report arithmetic_verification.json
```

The script independently recalculates the following, rather than just checking that reported columns add up:

- Twelve-category occupational precision estimates from the 2,106 adjudications' class-level counts; precision-adjusted public shares from 4,893 observed lexical occupational rows; TV distance from the corrected shares and matching recruitment shares. Recomputed TV is 0.5569816003782312, which rounds to the frozen 0.556982.
- Equal-weight percentile-rank PSI (two components), MRI (five absolute within-occupation changes), and descriptive median-cut quadrants. Average ranks preserve ties. The historical PSI computation uses the stored six-decimal attention-share representation, as did the source implementation.
- All 24 main recruitment Kitagawa decompositions, recomputed from 29 occupations' counts and within-occupation rates across 2021–2024, including renormalization within common support and the non-success of zero/zero dominance comparisons. The main magnitude criterion gives 20/24; this is an accounting contribution, not a causal effect.
- The 2025 recruitment adjustment: mean of the 2024 and 2026 occupation shares; within-occupation endpoint rates with minimum endpoint sample size 300; both available endpoints averaged, single qualified endpoint carried, neither available left missing; target composition renormalized over valid occupations separately for each metric. The source 2025 observed counts are not used as 2025 rate weights.

The initial full arithmetic probe passes 193/193 checks. These are deliberately scoped arithmetic and data-integrity checks, not a claim that 193 independent scientific results have been reproduced.

## Original synthetic power analysis

Install NumPy and pandas into your chosen environment. The portable script retains the original algorithm, seed schedule, null-size calibration, within-transformed permutation scheme, effect grid, and MDE interpolation. Six source generator functions are extracted exactly into `power_generator.py`; no legacy top-level simulation runs upon import.

```text
python power_audit_portable.py --reps 400 --calib-reps 500 --rperm 199
```

These settings match the frozen `power_reference_meta.json`, including the original 500 calibration replicates (not the source script's default 600). The output consists of `RQ3_2_功效审计.csv` and `RQ3_2_功效审计.json`, written beside the portable script. This is a genuine resimulation route requiring no empirical user-level data. A small smoke run (3 power replicates, 5 calibration replicates, 19 permutations, 55 grid points) passed, but the complete 400/500/199 run has not been repeated for this release. The root reproduction runner writes small-run estimates to the newly selected output directory under `power_smoke_NOT_PUBLISHED_RESULTS/`, not a pre-existing smoke/ directory; they must never replace the published values. Every power-analysis function AST and all six generator-function ASTs match the original source implementations exactly.

## Explicit limits

- The frozen TV double-bootstrap interval [0.528403, 0.589979] is not replayed. The final bootstrap generator and its input/draw stream were not recovered. Class-level adjudication counts suffice for precision point estimates, but do not by themselves recover the sampling/dependence structure or exact random stream used for the frozen interval. This package does not silently replace the interval with a newly invented binomial/Beta or iid bootstrap.
- The public channel-by-length Kitagawa sufficient table was not retained in the available exports. Existing public decomposition outputs are snapshots and arithmetic identities only. No raw comment matrix is included to reconstruct it.
- The empirical 360-specification temporal analysis and its permutation p-values remain frozen results in the parent display dataset. The synthetic power script is not a substitute for reestimating those empirical tests.
- Recruitment endpoint aggregation, wage imputation, sample selection, text labels, keyword recall, creator-level randomization, and ironic-text sensitivity depend on earlier restricted records or cluster-level inputs, which are not redistributed here.
- This is an author-controlled repository component, not a new licence grant. Actual availability depends on the hosting URL; access and redistribution permissions must be resolved before publication.

## File provenance

`build_safe_inputs.py` is the project-local extraction recipe and is not required to run the portable module. Do not include the project-local extraction recipe in the public/submission ZIP unless retaining its project paths is intentional. Portable runtime files are `recompute_metrics.py`, `power_audit_portable.py`, `power_generator.py`, `source_manifest.json`, this README, and the `data/` directory. Verification outputs may be included as execution evidence.
