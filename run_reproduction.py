"""Offline reproduction runner; creates new output, never edits package data."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent

def run_step(name, command, cwd, out):
    started = time.monotonic()
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
    (out/f'{name}.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
    if proc.returncode:
        raise RuntimeError(f'{name} failed (exit {proc.returncode}); see {out/name}.log')
    return {'step':name,'exit_code':0,'elapsed_seconds':round(time.monotonic()-started,3)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',required=True,help='A new local output directory')
    p.add_argument('--power',choices=['skip','smoke','full'],default='smoke',help='smoke is a software test, NOT a replication of published Monte Carlo estimates')
    p.add_argument('--no-displays',action='store_true',help='Skip graphics; arithmetic can run with only the Python standard library when --power skip is also used')
    a=p.parse_args()
    manifest=json.loads((BASE/'package_manifest.json').read_text(encoding='utf-8'))
    for name,h in manifest['files'].items():
        assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==h,'Package input changed: '+name
    out=Path(a.output).resolve()
    assert not out.exists(),'Use a new output directory; prior runs are not overwritten'
    out.mkdir(parents=True)
    checks=out/'checks';checks.mkdir()
    results=[]
    for name,component,script in [('aggregate_checks','aggregates','reproduce_summaries.py'),('metrics','metrics','recompute_metrics.py')]:
        results.append(run_step(name,[sys.executable,'-X','utf8',str(BASE/component/script),'--report',str(checks/f'{name}.json')],BASE/component,out))
        report=json.loads((checks/f'{name}.json').read_text(encoding='utf-8'))
        assert not report.get('failed_checks'),name+' has failed checks'
    if not a.no_displays:
        results.append(run_step('displays',[sys.executable,'-X','utf8',str(BASE/'displays/run_displays.py'),'--output',str(out/'displays')],BASE/'displays',out))
    if a.power!='skip':
        power_out=out/('power_smoke_NOT_PUBLISHED_RESULTS' if a.power=='smoke' else 'power_full_resimulation')
        power_out.mkdir()
        for name in ('power_audit_portable.py','power_generator.py'):
            shutil.copy2(BASE/'metrics'/name,power_out/name)
        if a.power=='smoke':
            settings=['--reps','3','--calib-reps','5','--rperm','19']
        else:
            settings=['--reps','400','--calib-reps','500','--rperm','199']
        results.append(run_step('power_'+a.power,[sys.executable,'-X','utf8',str(power_out/'power_audit_portable.py')]+settings,power_out,out))
    report={'scope':'Aggregate-derived metrics and quantitative display reproduction, not raw-to-results replication','power_profile':a.power,'power_smoke_is_published_replication':False,'steps':results,'package_inputs_unchanged':True,'restricted_tasks_not_rerun':['TV double-bootstrap interval','public-side decomposition underlying channel-length re-estimation','empirical temporal permutation tests','raw collection, annotation, training and creator-level inference']}
    for name,h in manifest['files'].items():
        assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==h,'Package input changed during run: '+name
    (out/'run_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
