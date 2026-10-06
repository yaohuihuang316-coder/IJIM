"""Standalone, offline checks of frozen aggregate display data (not full replication)."""
from pathlib import Path
import argparse, csv, hashlib, json, math, statistics, re

BASE=Path(__file__).resolve().parent
def load(name):
    with (BASE/'data'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ranks(xs):
    return [(sum(v<x for v in xs)+(sum(v==x for v in xs)+1)/2-1)/(len(xs)-1) for x in xs]
def run():
    checks=[]
    def check(name,ok,detail):
        checks.append({'check':name,'passed':bool(ok),'detail':detail})
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    for d in manifest['datasets']:
        p=BASE/d['file']
        check('integrity:'+d['file'],hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256'],f"{d['rows']} expected rows")
        with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        check('rows:'+d['file'],len(rows)==d['rows'],f'{len(rows)} observed rows')
    flow={r['variable']:int(r['value']) for r in load('sample_flow.csv')}
    check('sample_flow:labelled',flow['label_api']+flow['label_model']==flow['public_rows_analyzable'],'API + model = usable labelled texts')
    check('sample_flow:full_public',flow['public_rows_analyzable']+flow['label_none']==flow['public_corpus_total'],'usable + unlabelled = full observed corpus')
    check('sample_flow:recruitment',flow['recruitment_raw_500k']-flow['recruitment_dropped']==flow['recruitment_corpus'],'500000 - 27934 = 472066')
    annual=load('annual_sentiment.csv')
    check('annual:main_set',sum(int(r['denominator']) for r in annual)==flow['public_main_set'],'annual denominators sum to 422620')
    check('annual:net',all(abs(float(r['positive_rate'])-float(r['negative_rate'])-float(r['net']))<0.0011 for r in annual),'six positive-minus-negative checks, rounding tolerance 0.0011 pp')
    edu=load('education_topic.csv')
    check('education:negative_rate',all(abs(100*int(r['neg'])/int(r['n_topic_obs'])-float(r['topic_negative_rate_pct']))<0.000051 for r in edu),'six numerator/denominator checks, rounding tolerance 0.000051 pp')
    shares=[float(r['topic_share_pct']) for r in edu]
    check('education:share_not_increasing',not all(b>a for a,b in zip(shares,shares[1:])),{'topic_shares_pct':shares,'not_negative_rate':True})
    pub={r['item']:r['value'] for r in load('public_decomposition.csv')}
    check('public:decomposition_closure',abs(float(pub['composition_component'])+float(pub['within_component'])-float(pub['total_change']))<1e-10,'-2.0235 + 4.1937 = 2.1702 pp')
    endpoint=float(pub['standardized_negative_rate_end'])-float(pub['standardized_negative_rate_start'])
    check('public:distinct_estimands',abs(endpoint-float(pub['check_standardized_endpoint_diff']))<1e-10 and abs(endpoint-float(pub['total_change']))>1,'3.717 endpoint difference and 2.1702 decomposition are not substituted')
    dec=load('recruitment_decomposition.csv')
    check('recruitment:closure24',all(abs(float(r['within_component'])+float(r['composition_component'])-float(r['delta_total']))<1e-10 for r in dec),'24 original within + composition identities')
    wins=sum(abs(float(r['within_component']))>abs(float(r['composition_component'])) for r in dec)
    check('recruitment:within_dominance',wins==20 and len(dec)==24,{'within_gt_composition':wins,'denominator':len(dec)})
    occ=load('occupational_distance.csv');tv=sum(.5*abs(float(r['corrected_public_share'])-float(r['recruitment_share'])) for r in occ)
    corrected=next(float(r['estimate']) for r in load('distance_summary.csv') if r['metric']=='corrected_tv')
    check('distance:TV',abs(tv-corrected)<0.00001,{'computed_from_rounded_shares':tv,'original_estimate':corrected,'tolerance':0.00001})
    check('distance:contributions',all(abs(.5*abs(float(r['corrected_public_share'])-float(r['recruitment_share']))-float(r['contrib']))<0.000002 for r in occ),'12 contribution checks on rounded export')
    power=[r for r in load('power_audit.csv') if r['block']=='power_grid' and r['kind']=='main' and float(r['T_eff'])==4 and float(r['G_nocc'])==12 and float(r['phi'])==.5]
    check('power:display_selection',len(power)==11 and len({r['beta_std_target'] for r in power})==11,'11 main power-grid points; original simulation output, no resimulation')
    specs=load('temporal_specifications.csv');ok=[r for r in specs if r['status']=='ok']; main=[r for r in ok if r['main_or_expanded']=='main']
    check('temporal:coverage',len(specs)==360 and len(ok)==336 and len(main)==48,{'stored':len(specs),'estimable':len(ok),'main':len(main),'excluded_nonestimable':len(specs)-len(ok)})
    check('temporal:main_detection',sum(float(r['p_raw'])<.05 for r in main)==0,'0/48 main raw p-values below .05; original p-values not recomputed')
    profiles=load('occupation_indices.csv');n=len(profiles)
    psi=[sum(v)/2 for v in zip(ranks([float(r['psi_component_sP_adj']) for r in profiles]),ranks([float(r['psi_component_neg_adj']) for r in profiles]))]
    mri_components=[ranks([float(r[c]) for r in profiles]) for c in ['mri_abs_d_entry','mri_abs_d_exp','mri_abs_d_ba','mri_abs_d_ai','mri_abs_d_wage']]
    mri=[sum(v)/5 for v in zip(*mri_components)]
    check('profiles:PSI',n==12 and max(abs(x-float(r['public_index_rank'])) for x,r in zip(psi,profiles))<1e-10,'equal-weight percentile rank of 2 components; ties average ranks')
    check('profiles:MRI',max(abs(x-float(r['recruitment_index_rank'])) for x,r in zip(mri,profiles))<1e-10,'equal-weight percentile rank of 5 absolute changes')
    creator=[r for r in load('creator_variance.csv') if r['metric']=='neg_rate_polOK']
    check('creator:display_selection',len(creator)==3,'three primary negative-rate creator strata')
    check('creator:variance_closure',all(abs(float(r['between_up_share'])+float(r['within_up_share'])-1)<1e-10 for r in creator),'between + within = 1 in three primary strata')
    check('creator:denominator_exclusions',all(int(r['video_n_in_layer'])-int(r['dropped_denom_zero'])==int(r['video_n']) for r in creator),'three excluded-zero-denominator reconciliations')
    irony=load('irony_distance.csv')
    check('irony:baseline',abs(next(float(r['TV']) for r in irony if r['variant']=='base')-corrected)<1e-10,'same frozen baseline; extrapolation variants retained separately')
    check('synthetic:tied_ranks',ranks([1,1,3])==[.25,.25,1.0],'synthetic tied-value percentile-rank boundary')
    def share(a,b):return None if abs(a)+abs(b)==0 else abs(a)/(abs(a)+abs(b))
    check('synthetic:zero_components',share(0,0) is None and share(0,2)==0,'undefined zero/zero is not a within-dominance success')
    monthly=load('monthly_support.csv');observed=[r for r in monthly if r['support_status']=='observed']
    check('monthly:coverage',len(monthly)==72 and len(observed)==69 and sum(int(r['observed_comments']) for r in observed)==1235913,{'calendar_cells':len(monthly),'observed_cells':len(observed),'outside_window':len(monthly)-len(observed),'count_scope':'Full retained observed corpus, not all analytical denominators.'})
    check('monthly:unavailable_not_zero',all(r['observed_comments']=='' and r['year']=='2026' and int(r['month'])>=10 for r in monthly if r['support_status']!='observed'),'October–December 2026 unavailable, not zero')
    source=load('recruitment_annual_table_source.csv');display=load('main_table_02.csv')
    check('annual_recruitment:rows',len(source)==6 and len(display)==6,'six source years and six displayed years')
    check('annual_recruitment:rounding',all(a['Year']==b['Year'] and int(a['Observed track records'])==int(b['Observed track records'].replace(',','')) and all(f'{float(a[k]):.2f}'==b[k] for k in ['Any AI requirement (%)','AI tool requirement (%)','Entry-level (%)','No formal education (%)','Bachelor+ (%)']) for a,b in zip(source,display)),'same numeric values; two-decimal rounding only')
    check('annual_recruitment:specification',next(r['Specification'] for r in display if r['Year']=='2025')=='Adjusted rates' and next(r['Specification'] for r in display if r['Year']=='2026')=='Partial window','Adjusted 2025 rate estimates do not use observed within-cell rates; partial 2026 marked.')
    return {'assessment':'Usable with boundaries: display aggregates and selected arithmetic only; not full empirical replication.','checks_passed':sum(r['passed'] for r in checks),'checks_total':len(checks),'failed_checks':[r for r in checks if not r['passed']],'checks':checks,'raw_record_processing':False,'inference_resimulated':False,'publication_status':manifest['status']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report');a=parser.parse_args();result=run();s=json.dumps(result,ensure_ascii=False,indent=2)
    if a.report:Path(a.report).write_text(s+'\n',encoding='utf-8')
    print(s);raise SystemExit(0 if not result['failed_checks'] else 1)
