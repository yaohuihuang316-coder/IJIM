"""Redraw frozen numerical figure summaries; does not re-estimate inference.

No raw records, network access or private absolute paths are required.
Fonts use the manuscript font with an open fallback; exact pixels can vary
with font availability and Matplotlib version. Supplied CIs/p-values/power
curves are frozen results, not recomputed by this graphical layer.
"""
from pathlib import Path
import argparse, csv, json, hashlib, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
P=argparse.ArgumentParser()
P.add_argument('--output', required=True)
P.add_argument('--audit-scripts')
args=P.parse_args()
BASE=Path(__file__).resolve().parent
OUT=Path(args.output).resolve()
assert not OUT.exists(), 'Use a new output directory.'
OUT.mkdir(parents=True)
DATA=BASE/'data'
QA=OUT/'qa'; QA.mkdir()
if args.audit_scripts:
    sys.path.insert(0,str(Path(args.audit_scripts).resolve()))
    from audit_panel_alignment import require_matplotlib_panel_alignment
# Serif reproduces the manuscript; sans-serif remains the final open fallback.
plt.rcParams.update({'font.family':['serif','sans-serif'],'font.serif':['Times New Roman','DejaVu Serif'],
 'font.size':8,'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
 'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,
 'legend.fontsize':8,'legend.frameon':False,'svg.fonttype':'none','pdf.fonttype':42})
used=[]
def read(name):
    used.append(name)
    with (DATA/name).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def panel(ax,label):
    ax.annotate('('+label+')',(0,1),xycoords='axes fraction',xytext=(-12,9),
                textcoords='offset points',fontweight='bold',fontsize=9,annotation_clip=False)
def style(ax):
    ax.grid(axis='y',color='.9',lw=.5)
    ax.set_axisbelow(True)
manifest=[]
def save(fig,n,entry):
    exclude=()
    n+=1
    fig.canvas.draw()
    if args.audit_scripts:
        require_matplotlib_panel_alignment(fig,json_out=str(QA/f'Figure_{n:02d}.alignment.json'),
            overlay_svg=str(QA/f'Figure_{n:02d}.alignment.svg'),exclude_axes=list(exclude),strict=True)
    fig.savefig(OUT/f'Figure_{n:02d}.png',dpi=600,facecolor='white')
    fig.savefig(OUT/f'Figure_{n:02d}.pdf',facecolor='white')
    fig.savefig(OUT/f'Figure_{n:02d}.svg',facecolor='white')
    entry.update({'figure':n,'redrawn':True,'inference_reestimated':False});manifest.append(entry)
    plt.close(fig)
# Figure 8 claim: between-creator variance shares decline under stricter
# creator-activity strata; different strata remain different populations.
rows = read("creator_variance.csv")
selected = [r for r in rows if r["metric"] == "neg_rate_polOK"]
assert len(rows) == 15 and len(selected) == 3
assert [r["layer"] for r in selected] == ["全体", "≥3视频", "≥5视频"]
print(f"Figure 8 filter: before={len(rows)}, kept={len(selected)}, dropped={len(rows)-len(selected)} (80%); primary metric only")
for r in selected:
    assert abs(float(r["between_up_share"]) + float(r["within_up_share"]) - 1) < 1e-10
    assert int(r["video_n_in_layer"]) - int(r["dropped_denom_zero"]) == int(r["video_n"])
fig, ax = plt.subplots(figsize=(160 / 25.4, 72 / 25.4))
fig.subplots_adjust(left=.34, right=.98, bottom=.20, top=.82)
labels = ["All eligible creators", "Creators with ≥3 videos", "Creators with ≥5 videos"]
yticks = []
for i, (r, label) in enumerate(zip(selected, labels)):
    between = float(r["between_up_share"]) * 100
    within = float(r["within_up_share"]) * 100
    ax.barh(i, between, height=.50, color=".25", edgecolor=".25", linewidth=.5,
            label="Between creators" if i == 0 else None)
    ax.barh(i, within, left=between, height=.50, color=".85", edgecolor=".25", linewidth=.5,
            label="Within creators" if i == 0 else None)
    ax.text(between / 2, i, f"{between:.2f}%", ha="center", va="center", color="white", fontsize=8)
    ax.text(between + within / 2, i, f"{within:.2f}%", ha="center", va="center", color=".10", fontsize=8)
    yticks.append(f"{label}\n{int(r['video_n']):,} videos; {int(r['up_n']):,} creators")
ax.set(yticks=range(3), yticklabels=yticks, xlim=(0, 100), xticks=[0, 25, 50, 75, 100],
       xlabel="Share of video-level variance (%)", ylim=(2.55, -.55))
ax.tick_params(axis="y", length=0, pad=8)
ax.spines["left"].set_visible(False)
ax.legend(loc="lower center", bbox_to_anchor=(.50, 1.09), ncol=2, handlelength=1.4, columnspacing=1.8)
save(fig, 8, {
    "claim": "Between-creator variance shares decline across more active creator strata",
    "source": "creator_variance.csv", "filter": "metric == neg_rate_polOK",
    "rows_before": 15, "rows_kept": 3, "rows_excluded": 12, "excluded_pct": 80,
    "source_rows": selected,
    "caption": "Figure 8. Creator-level decomposition of video-level employment-related negative rates. Bars separate between-creator and within-creator shares for all eligible creators and for creators represented by at least three or five videos. Negative rates use employment-related comments with classifiable positive, neutral or negative polarity as the denominator. The corresponding valid samples contain 4,513, 2,566 and 2,013 videos from 2,381, 584 and 297 creators. Videos with zero denominators are excluded. These are descriptive variance shares, not causal effects; the strata differ in composition.",
})

# Figure 9 claim: all three explicitly different irony-removal scenarios leave
# the distributional distance close to the precision-corrected baseline.
rows = read("irony_distance.csv")
assert len(rows) == 5
by_variant = {r["variant"]: r for r in rows}
assert set(by_variant) == {"base", "v1", "v2", "v3", "unif"}
print("Figure 9 filter: before=5, points=4, benchmark=1, dropped=0")
fig, ax = plt.subplots(figsize=(160 / 25.4, 72 / 25.4))
fig.subplots_adjust(left=.34, right=.98, bottom=.20, top=.82)
labels = ["Precision-corrected baseline", "Observed-row removal", "Weighted-rate extrapolation", "Unweighted-rate extrapolation"]
for i, key in enumerate(["base", "v1", "v2", "v3"]):
    value = float(by_variant[key]["TV"])
    ax.plot(value, i, marker="o" if key == "base" else "s", color=".2", markersize=5,
            markerfacecolor=".2" if key == "base" else "white", markeredgewidth=.9, linestyle="none")
    ax.text(value + .024, i, f"{value:.3f}", va="center", ha="left", fontsize=8)
benchmark = float(by_variant["unif"]["TV"])
ax.axvline(benchmark, color=".5", ls="--", lw=.9)
ax.text(benchmark, 1.04, "Uniform-public benchmark: 0.303", transform=ax.get_xaxis_transform(),
        ha="center", va="bottom", fontsize=7.5)
ax.set(yticks=range(4), yticklabels=labels, ylim=(3.5, -.5), xlim=(0, .70),
       xticks=[0, .1, .2, .3, .4, .5, .6, .7], xlabel="Total variation distance")
ax.tick_params(axis="y", length=0, pad=8)
ax.spines["left"].set_visible(False)
save(fig, 9, {
    "claim": "Distributional distance is stable under three irony-removal scenarios",
    "source": "irony_distance.csv", "rows_before": 5, "rows_kept": 5,
    "rows_excluded": 0, "point_rows": 4, "benchmark_rows": 1, "source_rows": rows,
    "caption": "Figure 9. Sensitivity of occupational distributional distance to irony handling. Total variation distance is shown for the precision-corrected baseline and three removal specifications: removal of observed ironic comments, extrapolation from occupation-specific inverse-probability-weighted irony rates, and extrapolation from unweighted rates. The latter two are sensitivity assumptions rather than observed removals. The dashed line is the distance between the recruitment distribution and a uniform public distribution, not an irony-removal estimate. Points are descriptive estimates; no uncertainty intervals are implied.",
})

(OUT/'render_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
