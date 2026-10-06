"""Offline, one-command redraw of Figures 2–10 and generation of Tables 1–4."""
from pathlib import Path
import argparse, shutil, subprocess, sys, json, hashlib

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    p.add_argument('--audit-scripts',help='Optional separately installed figure QA helpers; not a bundled dependency')
    args=p.parse_args();base=Path(__file__).resolve().parent;out=Path(args.output).resolve()
    assert not out.exists(),'Use a new output directory; previous results are never overwritten.'
    out.mkdir(parents=True)
    for script,folder in [('plot_monthly_support.py','monthly'),('plot_main.py','main'),('plot_sensitivity.py','sensitivity'),('generate_tables.py','tables')]:
        command=[sys.executable,'-X','utf8',str(base/script),'--output',str(out/folder)]
        if args.audit_scripts and script!='generate_tables.py':command+=['--audit-scripts',args.audit_scripts]
        result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
        (out/f'{folder}_stdout.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        assert result.returncode==0,(script,result.stdout,result.stderr)
    figures=out/'figures';figures.mkdir()
    for n in range(2,11):
        folder='monthly' if n==2 else 'main' if n<=8 else 'sensitivity'
        for ext in ('png','pdf','svg'):
            source=out/folder/f'Figure_{n:02d}.{ext}'
            assert source.is_file() and source.stat().st_size>0
            shutil.copy2(source,figures/source.name)
    for source in (base/'static').glob('Figure_01.*'):shutil.copy2(source,figures/source.name)
    report={'numeric_figures_redrawn':9,'static_schematic_copied':1,'main_tables_generated':4,'statistical_tests_rerun':False,'font_note':'Pixel-identical redraws require the same fonts and versions. Numeric source values are invariant.','files':{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}}
    (out/'display_run_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
if __name__=='__main__':main()
