"""Aggregate seeds -> paired seed-level statistics used in the manuscript (all derived from results/seed*/results.json).
Usage: python scripts/paired_stats.py results/paired_stats.json results/seed0 results/seed1 ..."""
import json, sys, os, math
import numpy as np
from scipy import stats
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,REPO)
from ldt.models import KINDS, LABELS
from ldt.data import ID_RANGES

def shift_magnitude(cond):
    if cond["split"]=="id": return 0.0
    return float(np.sqrt(np.mean(np.square([max(lo-cond[k],cond[k]-hi,0.0)/(hi-lo) for k,(lo,hi) in ID_RANGES.items()]))))

def ms(x):
    x=np.asarray(x,float); return [float(x.mean()), float(x.std(ddof=1)) if len(x)>1 else 0.0]

def paired(a,b):
    """difference d=a-b over seeds; mean, sd, 95% t-CI, n_neg (a<b), exact sign info"""
    d=np.asarray(a,float)-np.asarray(b,float); n=len(d)
    m=float(d.mean()); s=float(d.std(ddof=1)); se=s/math.sqrt(n)
    t=stats.t.ppf(0.975,n-1)
    try: pw=float(stats.wilcoxon(d).pvalue) if n>=5 else None
    except Exception: pw=None
    pt=float(stats.ttest_1samp(d,0.0).pvalue)
    return dict(mean=m,sd=s,lo=m-t*se,hi=m+t*se,a_lower=int((d<0).sum()),n=n,p_t=pt,p_w=pw)

def analyze(run_dirs):
    R=[json.load(open(f'{d}/results.json')) for d in run_dirs]
    D=[json.load(open(f'{d}/dataset_summary.json')) for d in run_dirs]
    n=len(R); out={'n':n}
    get=lambda k,sp,key:[r[k][sp][key] for r in R]
    S={}
    for k in KINDS:
        s={}
        for sp,tag in (('test_id','id'),('test_ood','ood')):
            for key,name in (('rmse','rmse'),('mae_std','mae'),('cov95','cov95'),('cov90','cov90'),('ece','ece'),('width95','width95'),('nll','nll'),('sync_error','sync'),('enkf_ms_per_step','enkf_ms')):
                s[f'{name}_{tag}']=ms(get(k,sp,key)); s[f'{name}_{tag}_all']=get(k,sp,key)
        s['sync_ood_median']=float(np.median(s['sync_ood_all'])); s['sync_id_median']=float(np.median(s['sync_id_all']))
        s['mae_pooled']=ms([0.5*(r[k]['test_id']['mae_std']+r[k]['test_ood']['mae_std']) for r in R])
        s['mae_pooled_all']=[0.5*(r[k]['test_id']['mae_std']+r[k]['test_ood']['mae_std']) for r in R]
        s['degr']=ms([100*(r[k]['test_ood']['rmse']/r[k]['test_id']['rmse']-1) for r in R])
        for sp,tag in (('test_id','id'),('test_ood','ood')):
            H=np.array([r[k][sp]['rmse_by_horizon'] for r in R]); s[f'hor_{tag}']=H.mean(0).tolist()
        S[k]=s
    out['S']=S
    div={}
    for k in KINDS:
        div[k]={}
        for sp,tag in (('test_id','id'),('test_ood','ood')):
            mx=[float(np.max(r[k][sp]['sync_series'])) for r in R]
            div[k][tag]=dict(max=mx,n_div=int(sum(m>5.0 for m in mx)),runs=[i for i,m in enumerate(mx) if m>5.0])
    out['div']=div
    out['latency']=ms([r['latency_ms_single_twin_step'] for r in R])
    out['dataset']={sp:ms([d['stats'][sp]['samples'] for d in D]) for sp in D[0]['stats']}
    # relative reductions (seed means) and wins
    rel={}
    for k in KINDS[:-1]:
        row={}
        for name,key in (('id_rmse','rmse_id'),('ood_rmse','rmse_ood'),('mae','mae_pooled'),('sync_id','sync_id'),('sync_ood','sync_ood')):
            b,p=S[k][key][0],S['proposed'][key][0]; row[name]=100*(b-p)/b
        row['wins']={nm:int(sum(pv<bv for pv,bv in zip(S['proposed'][key+'_all'] if key+'_all' in S['proposed'] else [],S[k][key+'_all'])))
                     for nm,key in (('id_rmse','rmse_id'),('ood_rmse','rmse_ood'),('sync_id','sync_id'),('sync_ood','sync_ood'))}
        rel[k]=row
    out['rel']=rel
    # paired contrasts (proposed vs X): metric -> paired stats of (proposed - X) and relative
    pc={}
    for k in KINDS[:-1]:
        pc[k]={}
        for key in ('rmse_id','rmse_ood','sync_id','sync_ood','ece_id','ece_ood','cov95_id','cov95_ood','mae_pooled'):
            pc[k][key]=paired(S['proposed'][key+'_all'],S[k][key+'_all'])
    out['paired']=pc
    # relative paired % differences (proposed vs X) per seed, CI on mean of per-seed relative change
    prc={}
    for k in KINDS[:-1]:
        prc[k]={}
        for key in ('rmse_id','rmse_ood','sync_id','sync_ood'):
            rr=100*(np.array(S['proposed'][key+'_all'])-np.array(S[k][key+'_all']))/np.array(S[k][key+'_all'])
            rr=list(rr); m=np.mean(rr); sd=np.std(rr,ddof=1); t=stats.t.ppf(0.975,n-1)
            prc[k][key]=dict(mean=float(m),lo=float(m-t*sd/math.sqrt(n)),hi=float(m+t*sd/math.sqrt(n)),per_seed=[float(x) for x in rr])
    out['paired_rel']=prc
    # horizon crossover
    for tag in ('id','ood'):
        p=np.array(S['proposed'][f'hor_{tag}']); d=np.array(S['data'][f'hor_{tag}']); ph=np.array(S['physics'][f'hor_{tag}'])
        better=p<d
        first_worse=int(np.argmax(~better))+1 if (~better).any() else None
        out[f'cross_{tag}']=dict(steps_better=(first_worse-1) if first_worse else len(p),end_p=float(p[-1]),end_d=float(d[-1]),end_ph=float(ph[-1]),
                                 all_better_prefix=bool(better[:((first_worse-1) if first_worse else len(p))].all()))
    # transition analysis
    T={k:[r[k]['test_id']['transition'] for r in R] for k in ('physics','hybrid_nouq','hybrid_nomode','proposed')}
    tr={'bins':T['physics'][0]['bins'],'true_rms':np.mean([t['true_rms'] for t in T['physics']],0).tolist(),
        'true_rms_sd':np.std([t['true_rms'] for t in T['physics']],0,ddof=1).tolist(),
        'stance':ms([t['true_rms_stance'] for t in T['physics']]),'swing':ms([t['true_rms_swing'] for t in T['physics']])}
    for k in ('hybrid_nouq','hybrid_nomode','proposed'):
        tr[k]=np.mean([t['rel_err'] for t in T[k]],0).tolist(); tr[k+'_sd']=np.std([t['rel_err'] for t in T[k]],0,ddof=1).tolist()
        tr[k+'_overall']=ms([t['overall_rel_err'] for t in T[k]])
    out['trans']=tr
    # domain shift: per-episode rmse per model, bins
    per={k:[] for k in KINDS}
    for r,d in zip(R,D):
        for k in KINDS:
            for sp in ('test_id','test_ood'):
                w_ep=np.array(r[k][sp]['window_episode']); w_r=np.array(r[k][sp]['window_rmse'])
                for e,cond in enumerate(d['conditions'][sp]):
                    m=w_ep==e
                    if m.any(): per[k].append((shift_magnitude(cond),float(np.sqrt(np.mean(w_r[m]**2)))))
    edges=[-1e-9,1e-9,1.4,1.8,2.3,10]; ds={}
    for k in KINDS:
        p=np.array(per[k]); ys=[];cnt=[]
        for lo,hi in zip(edges[:-1],edges[1:]):
            m=(p[:,0]>lo)&(p[:,0]<=hi); ys.append(float(p[m,1].mean()) if m.any() else None); cnt.append(int(m.sum()))
        ds[k]=dict(bin_means=ys,counts=cnt)
    out['shift']=ds
    return out

if __name__=='__main__':
    dirs=sys.argv[2:]; o=analyze(dirs); json.dump(o,open(sys.argv[1],'w'),indent=1)
    S=o['S']
    for k in KINDS: print(k,'rmse_id %.3f±%.3f ood %.3f±%.3f sync %.3f/%.3f'%(*S[k]['rmse_id'],*S[k]['rmse_ood'],S[k]['sync_id'][0],S[k]['sync_ood'][0]))
    print(json.dumps(o['rel']['physics']),o['cross_id'],o['cross_ood'])
