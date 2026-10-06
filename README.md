# Data and code reproducibility package

This curated repository package reconstructs the manuscript displays and independently recomputes selected empirical results from de-identified aggregates. It is not an end-to-end record-to-results archive. It does not contain raw Bilibili text, user/video/creator identifiers, job-advertisement records, contacts, credentials, model weights or bundled third-party libraries.

## Run

Use Python 3.11 or later. Install the packages listed in `requirements.txt` in your own environment; this runner never installs software or accesses the network. Exact versions used for this release are recorded separately.

```text
python -m pip install -r requirements.txt
python run_reproduction.py --output reproduction_results
```

Run from any working directory by specifying the full path to `run_reproduction.py`. Always select a new output directory. The default command checks package hashes, executes the aggregate checks and metric recomputations, regenerates Figures 2–10 and Tables 1–4, preserves the static Figure 1, and performs a small power-algorithm smoke test. Logs and a machine-readable receipt are written only into the new output directory.

If you only need arithmetic, without installing plotting/simulation dependencies:

```text
python run_reproduction.py --output arithmetic_results --no-displays --power skip
```

To genuinely rerun the original synthetic power analysis with the recorded 400 power replicates, 500 calibration replicates and 199 permutations:

```text
python run_reproduction.py --output power_resimulation_results --no-displays --power full
```

The full simulation may be substantially slower. It was not repeated in full during package preparation. A software smoke run must never replace published estimates or be described as reproducing their values. Random-stream, dependency or floating-point differences can affect fresh simulation results; the supplied frozen reference outputs remain clearly distinct.

## Reproducibility coverage

| Result | What runs from this package | Boundary |
| --- | --- | --- |
| Figures 2–10 | Actual CSV-to-PNG/PDF/SVG plotting | Stored intervals and simulation estimates are plotted, not automatically re-estimated |
| Figure 1 | Original static schematic copied | Not a statistical figure regeneration |
| Main Tables 1–4 | CSV/Markdown table generation; Table 2 precision recomputed | Tables 1, 3 and 4 contain frozen editorial summaries |
| Occupational TV point estimate | Integer class-validation counts → precision correction → normalized public share → TV | Double-bootstrap interval is retained as a reference, not regenerated |
| PSI/MRI and quadrants | Percentile ranks, weights and median cuts recomputed | Descriptive profiles, not identified stable clusters |
| Recruitment decomposition | All 24 main Kitagawa decompositions from occupation counts and rates | Common-stratum denominator and source-track specification retained; not causal effects |
| 2025 adjusted requirements | Occupation-share interpolation and endpoint-supported rates; five annual indicators | Observed 2025 batch counts are not the adjusted rate denominator |
| Synthetic power analysis | Original generator and calibrated-analysis functions execute | Small smoke run verified; full profile provided but not fully repeated for this release |
| Public decomposition, empirical temporal tests, creator and irony inference | Frozen outputs inspectable and displays reconstructible | Restricted cluster/record-level inputs or final generator not redistributed/recovered; no full re-estimation claim |

The reference manuscript's exact values are unchanged. In the tested font environment, all nine numerical figure PNGs match the manuscript bytes. Other fonts and library versions can change graphical appearance without changing source numbers. Figure captions remain outside the images.

## Contents and data

`aggregates/` contains the original 26 figure/table CSVs (970 data rows), their dictionary and checksum-based arithmetic checker. `displays/` contains the portable figure/table code, the same 26 CSVs and static Figure 1. Duplicate inputs are retained to keep each component independently runnable; identical hashes are checked during assembly. `metrics/` adds four sufficient-statistic CSVs (348 rows), an additional variable dictionary, a source manifest, point-estimate and decomposition code, and the original synthetic power implementation.

Both the aggregate package and sufficient-statistic module preserve their object-specific denominators, missing values, period coverage and full precision. Do not pool their row counts as independent observations. Counts in monthly support describe retained sample support, not historical discussion volume.

## Rights and review anonymity

This package is prepared for author-controlled repository deposition. Preparation alone does not establish public availability, a DOI or a new redistribution licence. The repository owner must confirm the applicable redistribution rights before publication. Platform restrictions and third-party rights still apply; passing a contact/identifier scan is not a legal clearance or proof of complete anonymization. Dependencies are imported, not redistributed, and remain under their respective licences. Do not upload raw project folders or unrestricted debug logs in place of this curated package.

Author-identifying statements and title-page materials are supplied separately. Repository identities and metadata can reveal authorship even when package content does not. Public deposition or reviewer sharing must use the actual permissions and review arrangements chosen by the author. The frozen manuscript is not silently updated to claim public availability.
