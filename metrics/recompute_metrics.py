"""Offline independent arithmetic from sufficient aggregates. Python standard library only."""
from pathlib import Path
import argparse,csv,hashlib,json,math,statistics
BASE=Path(__file__).resolve().parent
def load(name):
    with (BASE/'data'/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def num(x):return float(x) if x not in ('','NA') else float('nan')
def norm(v):
    if not v or not all(math.isfinite(x) and x>=0 for x in v) or sum(v)<=0:raise ValueError('nonempty finite positive total required')
    return [x/sum(v) for x in v]
def ranks(v):
    if len(v)<2 or not all(math.isfinite(x) for x in v):raise ValueError('at least two finite values required')
    return [(sum(t<x for t in v)+(sum(t==x for t in v)+1)/2-1)/(len(v)-1) for x in v]
def kitagawa(s0,y0,s1,y1,renormalize=True):
    keep=[i for i in range(len(s0)) if all(math.isfinite(v[i]) for v in (s0,y0,s1,y1)) and (s0[i]>0 or s1[i]>0)]
    if not keep:raise ValueError('no common support')
    a=[s0[i] for i in keep];b=[s1[i] for i in keep];u=[y0[i] for i in keep];v=[y1[i] for i in keep]
    if renormalize:a,b=norm(a),norm(b)
    comp=sum((bb-aa)*(vv+uu)/2 for aa,bb,uu,vv in zip(a,b,u,v));within=sum((vv-uu)*(bb+aa)/2 for aa,bb,uu,vv in zip(a,b,u,v))
    delta=sum(bb*vv-aa*uu for aa,bb,uu,vv in zip(a,b,u,v))
    return {'composition':comp,'within':within,'delta':delta,'closure':comp+within-delta,'common_strata':len(keep),'dropped_strata':len(s0)-len(keep),'original_mass0':sum(s0[i] for i in keep),'original_mass1':sum(s1[i] for i in keep)}
def run():
    checks=[]
    def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
    manifest=json.loads((BASE/'source_manifest.json').read_text(encoding='utf-8'))
    for d in manifest['datasets']:check('sha256:'+d['file'],hashlib.sha256((BASE/d['file']).read_bytes()).hexdigest()==d['sha256'])
    p=load('occupation_precision_profiles.csv');N=[int(r['pub_rows_observed']) for r in p];pi=[int(r['T_genC'])/int(r['n_genC']) for r in p]
    adj=norm([n*x for n,x in zip(N,pi)]);m=[num(r['market_share_C7Qpooled']) for r in p]
    tv=sum(abs(a-b) for a,b in zip(adj,m))/2
    check('public_window_observed_rows',sum(N)==4893,sum(N));check('precision_sample_rows',sum(int(r['n_genC']) for r in p)==2106)
    check('TV_new_precision',abs(tv-0.556982)<5e-7,{'recomputed':tv,'published_6dp':0.556982})
    check('corrected_shares',max(abs(a-num(r['sP_adj_genC_piWindow2106'])) for a,r in zip(adj,p))<5e-7)
    # Historical PSI used rounded corrected-share export. Reproducing its ranks preserves ties.
    attention=[num(r['sP_adj_genC_piWindow2106']) for r in p]
    psi=[(a+b)/2 for a,b in zip(ranks(attention),ranks([num(r['neg_adj']) for r in p]))]
    mr=[ranks([abs(num(r['d_'+c])) for r in p]) for c in ['entry','exp','ba','ai','wage']]
    mri=[sum(a)/5 for a in zip(*mr)]
    check('PSI_percentile_rank',max(abs(a-num(r['PSI_adj_rank'])) for a,r in zip(psi,p))<1e-14)
    check('MRI_percentile_rank',max(abs(a-num(r['MRI_rank'])) for a,r in zip(mri,p))<1e-14)
    qp=[('Q1' if a>=statistics.median(psi) and b>=statistics.median(mri) else 'Q2' if a>=statistics.median(psi) else 'Q3' if b>=statistics.median(mri) else 'Q4') for a,b in zip(psi,mri)]
    check('descriptive_quadrants',all(r['quad_primary'].startswith(q) for r,q in zip(p,qp)))
    d=load('recruitment_occupation_year.csv');by={(r['occupation'],int(r['year'])):r for r in d};occs=sorted({r['occupation'] for r in d})
    check('recruitment_grid',len(d)==174 and len(occs)==29)
    metrics=['ai_tool','ai_rate','entry_rate','exp_level_mean','ba_plus','wage_mean_log'];wins=0;details=[]
    ref={(r['indicator'],int(r['t0']),int(r['t1'])):r for r in load('recruitment_decomposition_reference.csv') if r['group']=='main' and r['share_variant']=='n_raw'}
    for col in metrics:
        for y0,y1 in [(2021,2022),(2022,2023),(2023,2024),(2021,2024)]:
            s0=norm([num(by[o,y0]['n']) for o in occs]);s1=norm([num(by[o,y1]['n']) for o in occs]);r=kitagawa(s0,[num(by[o,y0][col]) for o in occs],s1,[num(by[o,y1][col]) for o in occs]);rr=ref[col,y0,y1]
            check(f'Kitagawa:{col}:{y0}-{y1}',max(abs(r[k]-num(rr[v])) for k,v in [('composition','comp'),('within','within'),('delta','delta_total')])<1e-12,r)
            wins+=abs(r['within'])>abs(r['composition']);details.append({'indicator':col,'t0':y0,'t1':y1,**r})
    check('within_dominance',wins==20,{'positive':wins,'denominator':24,'zero_zero_not_success':True})
    s24=norm([num(by[o,2024]['n']) for o in occs]);s26=norm([num(by[o,2026]['n']) for o in occs]);target=[(a+b)/2 for a,b in zip(s24,s26)]
    check('2025_target_composition',max(abs(a-num(by[o,2025]['n_target'])) for a,o in zip(target,occs))<1e-14)
    annual={int(r['Year']):r for r in load('recruitment_annual_reference.csv')};adjustment={}; branches={'interpolated':0,'carried_2024':0,'carried_2026':0,'missing':0}
    for col,refcol in [('ai_rate','Any AI requirement (%)'),('ai_tool','AI tool requirement (%)'),('entry_rate','Entry-level (%)'),('edu_unlimited','No formal education (%)'),('ba_plus','Bachelor+ (%)')]:
        values=[]
        for o in occs:
            a=num(by[o,2024][col]);b=num(by[o,2026][col]);ok0=num(by[o,2024]['n'])>=300 and math.isfinite(a);ok1=num(by[o,2026]['n'])>=300 and math.isfinite(b)
            branch='interpolated' if ok0 and ok1 else 'carried_2024' if ok0 else 'carried_2026' if ok1 else 'missing';branches[branch]+=1
            v=(a+b)/2 if ok0 and ok1 else a if ok0 else b if ok1 else float('nan');values.append(v)
            stored=num(by[o,2025][col]);check('2025_endpoint:'+col+':'+o,(not math.isfinite(v) and not math.isfinite(stored)) or abs(v-stored)<1e-13)
        valid=[i for i,x in enumerate(values) if math.isfinite(x)];rate=100*sum(target[i]*values[i] for i in valid)/sum(target[i] for i in valid);adjustment[col]=rate
        check('2025_annual_rate:'+col,abs(rate-num(annual[2025][refcol]))<.000051,{'recomputed_percent':rate,'reported_percent':num(annual[2025][refcol]),'valid_strata':len(valid),'target_mass_retained':sum(target[i] for i in valid)})
    check('synthetic_tied_ranks',ranks([1,1,3])==[.25,.25,1]);check('synthetic_kitagawa',abs(kitagawa([.5,.5],[0,1],[.5,.5],[1,0])['delta'])<1e-14)
    for name,fn in [('empty',lambda:norm([])),('all_zero',lambda:norm([0,0])),('one_rank',lambda:ranks([1]))]:
        try:fn();check('synthetic_reject_'+name,False)
        except ValueError:check('synthetic_reject_'+name,True)
    return {'assessment':'Usable with boundaries','checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'failed_checks':[c for c in checks if not c['passed']],'checks':checks,'TV':tv,'PSI':psi,'MRI':mri,'descriptive_quadrants':qp,'recruitment_decomposition':details,'adjustment_2025':adjustment,'adjustment_branches':branches,'not_recomputed':['Frozen TV double-bootstrap CI: upstream bootstrap draws and final generating implementation not recovered','Public Kitagawa underlying channel-length sufficient table unavailable in retained exports','Temporal empirical p-values: original estimates remain snapshots, not reestimated','Raw data retrieval, preprocessing, classifiers, annotation and privacy-protected corpora excluded']}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--report');args=a.parse_args();r=run();s=json.dumps(r,ensure_ascii=False,indent=2)
    if args.report:Path(args.report).write_text(s+'\n',encoding='utf-8')
    print(s);raise SystemExit(bool(r['failed_checks']))
