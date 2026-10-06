"""Portable reproduction of the frozen monthly-support display, not inference.

Requires matplotlib and numpy. No network, records, credentials or local
author paths are used. Run with --output DIR; output must be a new directory.
Optional --audit-scripts DIR enables the author's separately installed figure
QA helpers. Without them, rendering is not described as a fresh QA pass.
"""
from pathlib import Path
import argparse, csv, json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Rectangle

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--audit-scripts')
    args=parser.parse_args()
    base=Path(__file__).resolve().parent
    output=Path(args.output).resolve()
    assert not output.exists(),'Use a new output directory to preserve earlier exports.'
    output.mkdir(parents=True)
    with (base/'data'/'monthly_support.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    observed=[r for r in rows if r['support_status']=='observed']
    assert len(rows)==72 and len(observed)==69
    assert sum(int(r['observed_comments']) for r in observed)==1235913
    assert all(int(r['observed_comments'])>0 for r in observed),'No zero/negative values mapped by LogNorm'
    matrix=np.full((6,12),np.nan)
    for r in observed:matrix[int(r['year'])-2021,int(r['month'])-1]=int(r['observed_comments'])
    assert np.isnan(matrix).sum()==3 and np.all(np.isnan(matrix[5,9:]))
    with plt.rc_context({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],'font.size':8,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'axes.linewidth':.6,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.right':False,'axes.spines.top':False}):
        width_mm=160
        fig,ax=plt.subplots(figsize=(width_mm/25.4,90/25.4))
        fig.subplots_adjust(left=.10,right=.98,top=.93,bottom=.36)
        norm=LogNorm(vmin=float(np.nanmin(matrix)),vmax=float(np.nanmax(matrix)))
        grid=ax.pcolormesh(np.arange(13)-.5,np.arange(7)-.5,np.ma.masked_invalid(matrix),norm=norm,cmap='Greys',edgecolors='white',linewidth=.55,shading='flat')
        for y in range(6):
            for x in range(12):
                value=matrix[y,x]
                if np.isnan(value):
                    ax.add_patch(Rectangle((x-.5,y-.5),1,1,facecolor='.94',edgecolor='white',linewidth=.55));label='NA';color='black'
                else:label=f'{int(value):,}';color='white' if norm(value)>.65 else 'black'
                ax.text(x,y,label,ha='center',va='center',fontsize=7.5,color=color)
        ax.set(xticks=range(12),xticklabels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],yticks=range(6),yticklabels=range(2021,2027),xlim=(-.5,11.5),ylim=(5.5,-.5),xlabel='Month',ylabel='Year')
        ax.tick_params(length=0,pad=5)
        for spine in ax.spines.values():spine.set_visible(False)
        cax=fig.add_axes([.10,.18,.88,.035]);cb=fig.colorbar(grid,cax=cax,orientation='horizontal',ticks=[500,1000,3000,10000,30000,60000])
        cb.ax.set_xticklabels(['500','1,000','3,000','10,000','30,000','60,000']);cb.ax.tick_params(labelsize=8,length=2,pad=3)
        cb.set_label('Observed corpus records per month (logarithmic grayscale)',fontsize=8,labelpad=4);cb.minorticks_off()
        fig.text(.10,.035,'NA: outside the collection window. Counts describe sample support, not discussion intensity.',fontsize=7.5)
        fig.canvas.draw()
        if args.audit_scripts:
            sys.path.insert(0,str(Path(args.audit_scripts).resolve()))
            from audit_panel_alignment import require_matplotlib_panel_alignment
            require_matplotlib_panel_alignment(fig,json_out=str(output/'Figure_02.alignment.json'),overlay_svg=str(output/'Figure_02.alignment.svg'),exclude_axes=[cax],strict=True)
        fig.savefig(output/'Figure_02.pdf',facecolor='white');fig.savefig(output/'Figure_02.svg',facecolor='white');fig.savefig(output/'Figure_02.png',dpi=1000,facecolor='white')
        plt.close(fig)
    print(json.dumps({'calendar_cells':72,'observed_cells':69,'outside_window':3,'comment_count':1235913,'count_scope':'Retained observed corpus support, not discussion intensity','graphical_inference':'None','fresh_full_QA':'Run PDF text/collision audits separately; this utility does not claim an automatic complete audit.'}))
if __name__=='__main__':main()
