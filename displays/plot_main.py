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
 'font.size':7.5,'axes.labelsize':7.5,'xtick.labelsize':7,'ytick.labelsize':7,
 'axes.titlesize':8,'axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.65,'lines.linewidth':1.1,'lines.markersize':3.7,
 'legend.fontsize':6.8,'legend.frameon':False,'svg.fonttype':'none','pdf.fonttype':42})
used=[]
def read(name):
    used.append(name)
    return pd.read_csv(DATA/name)
def panel(ax,label):
    ax.annotate('('+label+')',(0,1),xycoords='axes fraction',xytext=(-12,9),
                textcoords='offset points',fontweight='bold',fontsize=9,annotation_clip=False)
def style(ax):
    ax.grid(axis='y',color='.9',lw=.5)
    ax.set_axisbelow(True)
manifest=[]
def save(fig,n,exclude=()):
    n+=1
    fig.canvas.draw()
    if args.audit_scripts:
        require_matplotlib_panel_alignment(fig,json_out=str(QA/f'Figure_{n:02d}.alignment.json'),
            overlay_svg=str(QA/f'Figure_{n:02d}.alignment.svg'),exclude_axes=list(exclude),strict=True)
    fig.savefig(OUT/f'Figure_{n:02d}.png',dpi=600,facecolor='white')
    fig.savefig(OUT/f'Figure_{n:02d}.pdf',facecolor='white')
    fig.savefig(OUT/f'Figure_{n:02d}.svg',facecolor='white')
    manifest.append({'figure':n,'redrawn':True,'inference_reestimated':False})
    plt.close(fig)
# Figure 2 retains annual polarity and six topical results, adding the corrected
# education-prevalence series as a separate panel rather than relabelling sentiment.
annual=read('annual_sentiment.csv')
topics=read('topic_sentiment.csv')
edu=read('education_topic.csv')
topic_year=read('topic_annual.csv')
assert np.allclose(edu.neg/edu.n_topic_obs*100,edu.topic_negative_rate_pct,atol=.0001)
fig,axs=plt.subplots(2,2,figsize=(6.3,6.2))
fig.subplots_adjust(left=.10,right=.98,bottom=.20,top=.94,wspace=.45,hspace=.57)
for ax,label in zip(axs.ravel(),'abcd'):panel(ax,label);style(ax)
ax=axs[0,0]
for col,lo,hi,label,marker,color,ls in [('positive_rate','pos_lo','pos_hi','Positive','o','.15','-'),('negative_rate','neg_lo','neg_hi','Negative','s','.5','--')]:
    ax.errorbar(annual.year,annual[col],yerr=[annual[col]-annual[lo],annual[hi]-annual[col]],label=label,marker=marker,color=color,ls=ls,capsize=2)
ax.set(ylabel='Share of comparable comments (%)',xticks=[2021,2023,2026],ylim=(17,40));ax.legend(loc='upper left',ncol=2)
ax=axs[0,1]
topic6=topics[~topics.topic_en.str.startswith('unclassified')].sort_values('negative_rate')
names={'work and employment':'Work / employment','learning and education':'Learning / education','content creation':'Content creation','life and entertainment':'Life / entertainment','ethics and governance':'Ethics / governance','human future':'Human future'}
ax.errorbar(topic6.negative_rate,np.arange(6),xerr=[topic6.negative_rate-topic6.cluster95_low,topic6.cluster95_high-topic6.negative_rate],fmt='o',color='.25',capsize=2)
ax.set(yticks=np.arange(6),yticklabels=[names[t].replace(' / ',' /\n') for t in topic6.topic_en],xlabel='Negative rate (%)',xlim=(0,70),ylim=(-.5,5.5));ax.grid(False);ax.grid(axis='x',color='.9',lw=.5)
ax=axs[1,0]
ax.plot(edu.year,edu.topic_share_pct,'o-',color='.15',label='Topic share')
ax.plot(edu.year,edu.topic_negative_rate_pct,'s--',color='.5',label='Within-topic negative rate')
ax.set(ylabel='Learning / education (%)',xticks=[2021,2023,2026],ylim=(0,24));ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),fontsize=6)
ax=axs[1,1]
for i,t in enumerate(names):
    d=topic_year[topic_year.topic_en==t].sort_values('year')
    ax.plot(d.year,d.net,marker=['o','s','^','D','v','x'][i],ls=['-','--',':','-.','-','--'][i],color=[str(v) for v in [.1,.45,.25,.6,.35,.05]][i],label=names[t])
ax.axhline(0,color='.7',lw=.6);ax.set(ylabel='Net sentiment (percentage points)',xticks=[2021,2023,2026],ylim=(-70,70))
ax.legend(loc='upper left',bbox_to_anchor=(-.02,-.23),ncol=2,fontsize=5.8,columnspacing=.6,handlelength=1.2)
save(fig,2)

# Figure 3: only the contains rule defines the main AI series. Exact-membership
# sensitivity rows remain in the packaged CSV, but never join the main line.
occ=read('recruitment_occupation.csv')
ai_raw=read('recruitment_ai.csv')
ai=ai_raw[ai_raw.rule=='contains'].sort_values('year')
exp=read('recruitment_requirements.csv').sort_values('year')
assert len(ai)==6 and ai.year.is_unique
fig,axs=plt.subplots(2,2,figsize=(6.3,6.1))
fig.subplots_adjust(left=.23,right=.98,bottom=.12,top=.92,wspace=.46,hspace=.52)
for ax,label in zip(axs.ravel(),'abcd'):panel(ax,label);style(ax)
selected=[('生产/制造/技工','Production /\nmanufacturing'),('物流/配送/驾驶','Logistics / delivery'),('质量/质检','Quality inspection'),('设计','Design'),('人力/行政','HR / administration'),('销售/门店','Sales / stores')]
ax=axs[0,0]
for i,(cn,en) in enumerate(selected):
    x=[float(occ[(occ.occupation_group==cn)&(occ.year==yr)].share_pct.iloc[0]) for yr in [2021,2026]]
    ax.plot(x,[i,i],color='.6');ax.plot(x[0],i,'o',mfc='white',mec='.25',label='2021' if i==0 else None);ax.plot(x[1],i,'s',color='.25',label='2026' if i==0 else None)
ax.set(yticks=np.arange(6),yticklabels=[en for cn,en in selected],xlabel='Share of advertisements (%)',xlim=(0,24));ax.invert_yaxis();ax.legend(loc='upper left',bbox_to_anchor=(0,1.18),ncol=2);ax.grid(False);ax.grid(axis='x',color='.9',lw=.5)
ax=axs[0,1]
for col,label,m,ls,c in [('ai_total_rate','Any AI requirement','o','-','.1'),('ai_tool_rate','AI tool','s','--','.45'),('ai_rd_rate','AI R&D','^',':','.65')]:ax.plot(ai.year,ai[col],marker=m,ls=ls,color=c,label=label)
ax.set(ylabel='Share of advertisements (%)',xticks=[2021,2023,2026],ylim=(-.05,2.6));ax.legend(loc='upper left',bbox_to_anchor=(0,.93),fontsize=6)
ax=axs[1,0]
ax.plot(exp.year,exp.entry_level_rate,'o-',color='.15');ax.set(ylabel='Entry-level share (%)',xticks=[2021,2023,2026],ylim=(67,74))
ax=axs[1,1]
ax.plot(exp.year,exp.no_education_rate,'o-',color='.15',label='No formal requirement');ax.plot(exp.year,exp.bachelor_or_above_rate,'s--',color='.5',label='Bachelor or above')
ax.set(ylabel='Share of advertisements (%)',xticks=[2021,2023,2026],ylim=(15,34));ax.legend(loc='upper left',fontsize=6)
for ax in [axs[0,1],axs[1,0],axs[1,1]]:ax.axvspan(2024.88,2025.12,color='.9',zorder=0)
fig.text(.23,.025,'Shaded: adjusted 2025; 2026 is a partial collection window.',fontsize=7)
save(fig,3)

# Reconstruct the remaining statistical encodings from their frozen plotting tables.
# Original PNGs remain untouched; every delivered figure now has an editable source.
pub=read('public_decomposition.csv')
dec=read('recruitment_decomposition.csv')
fig,axs=plt.subplots(1,2,figsize=(6.3,4.1))
fig.subplots_adjust(left=.11,right=.98,bottom=.22,top=.88,wspace=.70)
for ax,l in zip(axs,'ab'):panel(ax,l)
pv=pub.set_index('item').value
# Pull delivered components by their names, not rounded manuscript values.
keys=[k for k in pv.index if 'composition' in k or 'within' in k or 'total' in k]
print('Public decomposition source keys:',keys)
vals=[float(pv[next(k for k in keys if stem in k)]) for stem in ['composition','within','total']]
ax=axs[0];ax.bar(['Composition','Within','Total'],vals,color=['.7','.25','.5'],width=.65)
for x,v in enumerate(vals):ax.text(x,v+(.18 if v>=0 else -.18),f'{v:+.2f}',ha='center',va='bottom' if v>=0 else 'top',fontsize=7)
ax.axhline(0,color='.4',lw=.7);ax.set(ylabel='Change in negative rate (pp)',ylim=(-3.2,5.5));ax.tick_params(axis='x',labelrotation=25);style(ax)
labels={'ai_tool':'AI tool','ai_rate':'AI requirement','entry_rate':'Entry-level','exp_level_mean':'Experience','ba_plus':'Bachelor+','wage_mean_log':'Log wage'}
ind=list(dec.indicator.unique());windows=list(dec.window.unique())
mat=dec.pivot(index='indicator',columns='window',values='abs_within_share').reindex(index=ind,columns=windows).astype(float)*100
ax=axs[1];ax.imshow(mat,vmin=0,vmax=100,cmap='Greys',aspect='auto')
ax.set(xticks=range(len(windows)),xticklabels=[w.replace('→','–').replace('（累计）','\n(cumulative)') for w in windows],yticks=range(len(ind)),yticklabels=[labels.get(x,x) for x in ind]);ax.tick_params(axis='x',rotation=0)
for i,metric in enumerate(ind):
    for j,w in enumerate(windows):
        row=dec[(dec.indicator==metric)&(dec.window==w)].iloc[0];v=mat.iloc[i,j]
        txt='NA' if not np.isfinite(v) else f'{v:.0f}'
        ax.text(j,i,txt,ha='center',va='center',color='white' if v>65 else 'black',fontsize=7)
        if bool(row.sign_opposite):ax.plot(j+.34,i-.32,'o',ms=3,mfc='none',mec='white' if v>65 else 'black',mew=.6)
ax.set_title('Within share of absolute components (%)',fontsize=7,pad=12)
save(fig,4)

shares=read('occupational_distance.csv')
idx=read('occupation_indices.csv')
names12=dict(zip(idx.occupation12,idx.occupation12_en))
fig,axs=plt.subplots(1,2,figsize=(6.3,4.4))
fig.subplots_adjust(left=.31,right=.98,bottom=.15,top=.88,wspace=.32)
for ax,l in zip(axs,'ab'):panel(ax,l)
y=np.arange(len(shares));ax=axs[0]
for j,r in shares.iterrows():ax.plot([100*r.recruitment_share,100*r.corrected_public_share],[j,j],color='.75',lw=.8)
ax.plot(shares.recruitment_share*100,y,'o',mfc='white',mec='.2',label='Recruitment');ax.plot(shares.corrected_public_share*100,y,'s',color='.35',label='Public, corrected')
ax.set(yticks=y,yticklabels=[names12[x] for x in shares.occupation12],xlabel='Occupation share (%)',ylim=(11.6,-.6),xlim=(-1,32));ax.legend(loc='lower left',bbox_to_anchor=(-.02,1.01),fontsize=6)
ax=axs[1];ax.barh(y,shares.contrib,color='.45');ax.set(yticks=y,yticklabels=[],xlabel='Contribution to TV',ylim=(11.6,-.6),xlim=(0,.14))
for j,v in enumerate(shares.contrib):ax.text(v+.003,j,f'{v:.3f}',va='center',fontsize=6.3)
save(fig,5)

power_all=read('power_audit.csv')
power=power_all[(power_all.block=='power_grid')&(power_all.kind=='main')&(power_all.T_eff==4)&(power_all.G_nocc==12)&(power_all.phi==.5)].sort_values('beta_std_realized')
assert len(power)==11 and power.beta_std_target.is_unique
print('Figure6 power selection:',len(power),'of',len(power_all),'rows; T_eff=4, G=12, phi=0.5, main')
spec=read('temporal_specifications.csv');spec=spec[spec.status=='ok'].sort_values('effect').reset_index(drop=True)
assert len(spec)==336
fig,axs=plt.subplots(2,1,figsize=(6.3,5.1))
fig.subplots_adjust(left=.13,right=.97,bottom=.12,top=.94,hspace=.52)
for ax,l in zip(axs,'ab'):panel(ax,l);style(ax)
ax=axs[0];ax.plot(power.beta_std_realized,power.power_calibrated_main,'o-',color='.15')
ax.axhline(.8,color='.55',ls='--',lw=.8);ax.axvline(.4406931135,color='.4',ls=':',lw=.9)
ax.text(.02,.91,'MDE80 = 0.441',transform=ax.transAxes,fontsize=7)
ax.set(xlabel='Absolute standardized effect',ylabel='Calibrated power',ylim=(0,1.04))
ax=axs[1];main=spec.main_or_expanded.eq('main')
for mask,label,marker,c in [(~main,'Expanded','.', '.6'),(main,'Main (48)','o','.15')]:ax.plot(np.flatnonzero(mask)+1,spec.loc[mask,'effect'],ls='none',marker=marker,color=c,ms=3,label=label)
ax.axhline(0,color='.6',lw=.6);ax.axhline(.4406931135,color='.4',ls=':',lw=.8);ax.axhline(-.4406931135,color='.4',ls=':',lw=.8)
ax.set(xlabel='Specification ordered by estimated effect',ylabel='Standardized effect',ylim=(-.52,.52),xlim=(0,337));ax.legend(loc='lower left',bbox_to_anchor=(.05,1.01),ncol=2)
save(fig,6)

fig,axs=plt.subplots(1,2,figsize=(6.3,4.4))
fig.subplots_adjust(left=.10,right=.98,bottom=.16,top=.91,wspace=.9)
for ax,l in zip(axs,'ab'):panel(ax,l)
ax=axs[0];ax.scatter(idx.recruitment_index_rank,idx.public_index_rank,s=18,color='.2')
ax.axvline(idx.recruitment_index_rank.median(),color='.5',ls='--',lw=.7);ax.axhline(idx.public_index_rank.median(),color='.5',ls='--',lw=.7)
for j,r in idx.iterrows():ax.annotate(str(j+1),(r.recruitment_index_rank,r.public_index_rank),xytext=((-7,-9) if j==0 else (4,4)),textcoords='offset points',fontsize=6.5)
ax.set(xlabel='MRI',ylabel='PSI',xlim=(0,1),ylim=(0,1))
ax=axs[1];y=np.arange(12)
for j,r in idx.iterrows():ax.plot([r.public_index_rank,r.recruitment_index_rank],[j,j],color='.7',lw=.8)
ax.plot(idx.public_index_rank,y,'o',mfc='white',mec='.2',label='PSI');ax.plot(idx.recruitment_index_rank,y,'s',color='.35',label='MRI')
ax.set(yticks=y,yticklabels=[f'{j+1} {r.occupation12_short_en}' for j,r in idx.iterrows()],xlabel='Percentile-rank index',ylim=(11.6,-.6),xlim=(0,1))
ax.tick_params(axis='y',labelsize=6.1);ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=2)
save(fig,7)

(OUT/'render_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
