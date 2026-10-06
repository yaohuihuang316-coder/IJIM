# Portable display reproduction

This component redraws all nine quantitative main figures (Figures 2–10)
from de-identified frozen aggregate CSVs and generates the four main tables.
It performs no network requests and needs no record-level platform content.
Figure 1 is the preserved static study schematic, copied rather than treated
as a quantitative data figure. Tables 1, 3 and 4 contain frozen editorial
summaries, not executable statistical tests. Table 2 numeric rounding is
recomputed from the unrounded annual aggregate input.

## Run

Use Python 3.11 or later and install `requirements.txt` in your own environment.
From this folder, run:

```text
python -m pip install -r requirements.txt
python run_displays.py --output display_results
```

The output directory must not already exist. The command generates PNG,
editable PDF and SVG for Figures 2–10, preserves the original Figure 1,
and writes CSV/Markdown versions of Tables 1–4. Each subprocess has a
separate log and the final report records output SHA-256 values. Font
availability changes graphical pixel hashes; source numbers are unchanged.
Times New Roman falls back to DejaVu Serif; Arial falls back to DejaVu Sans.
The original manuscript images are not replaced by this reproduction run.

## What this layer does and does not reproduce

| Display | Frozen source CSV | Executed transformation |
|---|---|---|
| Figure 2 | monthly_support | 72 calendar cells; 69 observed counts; 3 unavailable cells; logarithmic grayscale |
| Figure 3 | annual_sentiment, topic_sentiment, education_topic, topic_annual | confidence-interval rendering; explicitly separate topic prevalence from within-topic negativity |
| Figure 4 | recruitment_occupation, recruitment_ai, recruitment_requirements | endpoint comparison; `contains` AI series; adjusted 2025 shading |
| Figure 5 | public_decomposition, recruitment_decomposition | signed components and absolute within-component shares; undefined zero/zero cells remain NA |
| Figure 6 | occupational_distance, occupation_indices | corrected distribution shares and individual TV contributions |
| Figure 7 | power_audit, temporal_specifications | 11 calibrated curve points from 84 stored rows; 336 estimable specifications from 360 rows (48 nested main cases) |
| Figure 8 | occupation_indices | descriptive occupational indices and median quadrant lines |
| Figure 9 | creator_variance | three primary negative-rate strata from 15 rows; within/between variance shares |
| Figure 10 | irony_distance | four scenario points plus a separate uniform-public benchmark; no dropped rows |
| Table 1 | main_table_01 | editorial analysis-object cell export |
| Table 2 | recruitment_annual_table_source | six years; rounding and record-count formatting, with all displayed cells checked against main_table_02 |
| Table 3 | main_table_03 | editorial inferential-summary cell export |
| Table 4 | main_table_04 | editorial sensitivity-summary cell export |

Stored intervals, p-values, simulation curves, creator variance shares and
irony scenarios are plotted as frozen results. This layer does not repeat
their original bootstrap, permutation or power simulations, does not rerun
the annotation models and does not claim end-to-end raw-data replication.
Separate inference components, if included in the parent package, define
the calculations that can actually be recomputed from their aggregate inputs.

The optional `--audit-scripts PATH` argument enables separately installed
figure-alignment QA scripts. Those external authoring tools are not required
to redraw displays and are not redistributed here. Without those tools,
the run does not claim a fresh automatic figure-layout audit. Local author
validation reports are supplied separately where available.
