# Aggregate figure and table data

This is an author-controlled aggregate-data package. Actual repository availability is established only by its real hosting URL; preparation does not confer redistribution rights or a new reuse licence. Source permissions and review-anonymity arrangements remain the author’s responsibility. No licence for platform material, third-party algorithms, model weights or dependencies is implied by inclusion of these summaries.

## What is included

The `data/` directory contains 19 selected frozen analytical-summary/source CSVs and seven CSV transcriptions of the displayed manuscript/supplementary tables. `manifest.json` gives the exact row counts, selected fields, source-file digests and figure/table coverage. `data_dictionary.csv` defines all selected analytical fields. CSV is UTF-8 with a byte-order mark; data are readable without the original Chinese workspace path.

Coverage: sample-flow values for the schematic Figure 1; all nine numerical main figures (Figures 2–10); four main tables and three supplementary tables. The prior creator and irony sensitivity figures are now main Figures 9 and 10. The prior main Table 2 is now main Table 3; prior supplementary Table S4 is now main Table 4, not duplicated in the supplement. The new monthly-support Figure 2 retains all 72 calendar cells (69 observed and three outside the collection window) and does not interpret comment counts as discussion intensity. The new annual recruitment Table 2 has separate full-precision source and two-decimal displayed CSVs. Figure 1's layout and graphic artwork are not recreated here. The table transcriptions preserve displayed rounding and are not substituted for full-precision analysis inputs.

Included units are year/topic cells, year/occupation cells, occupation/window decompositions, occupation profiles, simulation-grid outputs, analytical specifications and creator-activity-stratum summaries. No user-, video-, creator- or job-advertisement-level rows are included. Counts such as `video_n` and `up_n` are aggregate sample sizes, not identifiers. No verbatim platform texts, individual contact details, model weights, network/API configuration or project-wide source-code collection is supplied.

## Reproduce the checks

Use Python 3.10 or newer, with only its standard library:

```text
python reproduce_summaries.py
python reproduce_summaries.py --report verification_results.json
```

The script verifies every data-file digest and row count, independently recalculates selected published arithmetic from the supplied aggregates, verifies the PSI/MRI rank-index construction, and reports the exact checks performed. It does not fit new models or generate publication figures. The default command prints JSON and does not modify files; `--report` writes the same result to the named local path. The script contains synthetic tied-rank and empty-denominator checks so its verification logic is also tested at boundary cases.

## Essential measurement boundaries

- Public annual sentiment uses the 422,620-comment primary analysis set, not the entire 1,235,913-comment corpus. Topic analyses have their own API-labelled denominators. API labels are machine-teacher labels, not error-free human gold labels. These are digital traces, not population-representative opinions.
- Learning/education **topic share** is 9.6815, 12.8688, 6.8553, 7.5833, 6.6848 and 4.7112 percent (2021–2026). The series 8.0165 to 18.8504 percent is its **within-topic negative rate**. Do not interchange them.
- Annual recruitment series use the specified recruitment source track, not all 472,066 advertisements. `contains` is the main AI-requirement rule; exact-membership rows are a separate sensitivity definition.
- The 2025 recruitment composition is interpolated from the normalized mean of 2024 and 2026 occupation shares. Within-occupation rates use endpoint interpolation where both endpoint counts meet 300, carry a supported endpoint where only one meets that threshold, and remain missing otherwise; valid cells are renormalized. The frozen main adjusted rates do **not** use observed 2025 within-cell rates. The 2026 recruitment track is a partial collection window through 18 September, dominated by August/September observations, and excludes enterprise ATS channels.
- Direct-standardized public endpoints and the common-strata Kitagawa change are different estimands. The endpoint difference 32.069 − 28.352 = 3.717 percentage points must not replace the decomposed change 2.1702 = −2.0235 + 4.1937 percentage points.
- Occupational TV compares the observed occupational signal after category-specific precision correction, not population occupational prevalence. Per-occupation share intervals were not produced; precision intervals must not be repurposed as share intervals. Superseded TV versions and permutation-boundary rows that do not define the current displayed TV summary are deliberately excluded; the current three display rows remain.
- Temporal specifications include 360 stored rows, of which 336 are estimable: 48 main plus 288 other-window tests. They are not 384 mutually independent tests. The power curve is selected by `block=power_grid`, `kind=main`, `T_eff=4`, `G_nocc=12`, `phi=0.5`. Stored confidence limits, p-values and power results are original outputs, not independently re-simulated here.
- PSI is the equal-weight average of percentile ranks of corrected public occupational share and corrected negative rate. MRI is the equal-weight average of percentile ranks of absolute 2024–2022 changes in five occupational outcomes (entry level, experience, bachelor+, AI requirements, log wage). Percentile rank is `(average rank − 1)/(12 − 1)`. Median-cut quadrants are descriptive profiles, not identified stable occupational clusters.
- Creator-stratum variance shares are descriptive and compare differently composed strata. Irony variants `v2` and `v3` extrapolate rates; they are not observed removals. `unif` is a uniform-public benchmark, not an irony estimate.
- `NA`, empty and em dash denote undefined or unavailable values and must not become zeros. Decomposition shares are undefined when both components are zero.

## What this package cannot reproduce

This component supplies figure/table data and selected arithmetic checks, not complete record-to-results replication. The sibling metrics/ module additionally recomputes selected sufficient-statistic results, including the 2025 adjustment and the occupational TV point estimate; the root runner also regenerates Figures 2–10. The limits below describe this aggregate component alone, not the combined package. Without restricted records, label/context input, video clustering and annotation-level precision validation it cannot rerun collection, deduplication, annotation/classifier training, contamination correction, raw-to-aggregate weighting, the 2025 within-cell adjustment, cluster bootstrap confidence intervals, precision-uncertainty propagation, fitted temporal-panel effects, permutation calibration or power simulations. The original outputs are retained to make displayed results inspectable; their inferential quantities are not newly validated by passing the aggregate checks.

The sibling metrics/ directory contains the selected sufficient-statistic inputs and implementations approved for this curated package. Additional sharing beyond that whitelist requires a separate rights and reidentification-risk assessment and documentation of permissible controlled access to restricted records. Do not replace the manuscript's existing reasonable-request statement with a claim of public deposition until a real repository record exists and its permissions have been approved.

## Before release

1. Author approval of the precise aggregate whitelist and third-party/platform redistribution terms; automated contact/identifier scans are not legal permission or a privacy guarantee.
2. Decide data and code licences independently, after checking ownership. None is granted by this draft.
3. Resolve double-anonymous review: repository authorship/metadata and DOI registration may reveal the author even if file content is anonymous. Use a genuinely anonymous reviewer-access route only after checking its actual repository settings; otherwise explain restrictions to the editor and retain request-based access during review.
4. Inspect README, dictionary, manifest, data and repository metadata together. Store author contacts separately, not in this anonymous candidate.
5. Publish only after explicit author approval; record the resulting stable URL/DOI and amend the manuscript's data statement truthfully.

## Expanded-display synchronization

`monthly_support.csv` provides the new Figure 2 source. `recruitment_annual_table_source.csv` supplies full-precision values for the new main Table 2; `main_table_02.csv` supplies displayed rounding. All previous numeric source cells remain unchanged. The six previous table transcriptions remain byte-identical under the renaming above, with three retained supplementary tables. The verification script includes monthly total/window and new Table 2 source/display reconciliation checks.

`plot_monthly_support.py --output NEW_DIRECTORY` additionally recreates the new Figure 2's display using Matplotlib and NumPy, without restricted records or author-specific paths. It does not run the original empirical analyses. Only this newly authored chart is recreated; the other existing charts' frozen numeric inputs remain inspectable. For optional fresh plotting alignment checks, provide `--audit-scripts` pointing to your own installation of the author's QA helpers; those third-party tools are not redistributed or licensed by this candidate. PDF text/font/collision audits must be run separately before presenting a new export as quality-checked. No dependency installation is performed by either script, and font appearance can differ when Arial is unavailable.
