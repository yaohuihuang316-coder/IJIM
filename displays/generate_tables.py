"""Generate editable CSV and Markdown tables from frozen aggregate inputs.

Table 2 rounding and sample-number formatting are recomputed. Tables 1, 3
and 4 preserve the frozen editorial result summaries: exporting their cells
is not a new test or a recomputation of the underlying p-values.
"""
from pathlib import Path
import argparse, csv, json

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    args=p.parse_args();base=Path(__file__).resolve().parent
    out=Path(args.output).resolve()
    assert not out.exists(),'Use a new output directory.'
    out.mkdir(parents=True)
    report=[]
    for n in range(1,5):
        source='recruitment_annual_table_source.csv' if n==2 else f'main_table_{n:02d}.csv'
        with (base/'data'/source).open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
        if n==2:
            for r in rows:
                r['Observed track records']=f"{int(r['Observed track records']):,}"
                for k in fields[2:7]:r[k]=f'{float(r[k]):.2f}'
        with (out/f'Table_{n:02d}.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        lines=['| '+' | '.join(fields)+' |','| '+' | '.join('---' for _ in fields)+' |']
        for r in rows:lines.append('| '+' | '.join(str(r[k]).replace('|','\\|').replace('\n','<br>') for k in fields)+' |')
        (out/f'Table_{n:02d}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        with (base/'data'/f'main_table_{n:02d}.csv').open(encoding='utf-8-sig',newline='') as f:expected=list(csv.DictReader(f))
        assert rows==expected,(n,'Generated cells must equal the frozen manuscript cells')
        report.append({'table':n,'source':source,'rows':len(rows),'columns':len(fields),'all_cells_match_frozen':True,'recomputed': 'Numeric rounding / record formatting' if n==2 else 'Frozen summary export only'})
    (out/'table_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
