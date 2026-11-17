"""Three questions; shared document-intercept binomial logit, no change point."""
from pathlib import Path
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from scipy.special import logit
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
SEED=20261116

def inputs():
    a=pd.read_csv(ROOT/'data/annotated_G_date_corrected.csv')
    a=a[a['대표연도'].between(1500,1955)&a['문장유형'].isin(['(수사)의문문','부정명령문','단순부정문'])].copy()
    cases=[]
    for c,label,old,types in [('Q','（수사）의문문','생심이나',['(수사)의문문']),('P','부정명령문','생심도',['부정명령문']),('N','단순부정문','생심도',['단순부정문']),('PN','부정명령문+단순부정문','생심도',['부정명령문','단순부정문'])]:
        s=a[a['문장유형'].isin(types)].copy()
        for m in ['M1','M3']:
            d=s[s['계열'].eq('생심류')].copy() if m=='M1' else s.copy()
            d['y']=d['대표형식'].eq(old).astype(int) if m=='M1' else d['계열'].eq('생심류').astype(int)
            d=d.groupby(['문헌연대ID','대표연도'],as_index=False).agg(n=('y','size'),y=('y','sum')).rename(columns={'문헌연대ID':'문헌ID'})
            cases.append((m+'_'+c,label,d,False))
            if c=='PN':
                e=s[s['계열'].eq('생심류')].copy() if m=='M1' else s.copy()
                e['y']=e['대표형식'].eq(old).astype(int) if m=='M1' else e['계열'].eq('생심류').astype(int)
                e=e.groupby(['문헌연대ID','대표연도','문장유형'],as_index=False).agg(n=('y','size'),y=('y','sum')).rename(columns={'문헌연대ID':'문헌ID'})
                e['N']=e['문장유형'].eq('단순부정문').astype(int)
                cases.append((m+'_PN_type',label,e,'type'))
    for fn,suffix in [('M4_QP_연구자보완.csv',''),('M4_QP_명시연대대조.csv','_metadata'),('M4_QP_확장보수.csv','_expanded')]:
        b=pd.read_csv(ROOT/'data'/fn)
        for c,label in [('Q','（수사）의문문'),('P','부정명령문')]:
            d=b[b['문형'].eq(c)].copy()
            cases.append(('M2_'+c+suffix,label,d,False))
            if not suffix:cases.append(('M2_'+c+'_source',label,d,True))
        version={'':'연구자보완','_metadata':'명시연대대조','_expanded':'확장보수'}[suffix]
        neg=pd.read_csv(ROOT/'data'/f'M2_N_{version}.csv')
        for c,label,d in [('N','단순부정문',neg),('PN','부정명령문+단순부정문',pd.concat([b[b['문형'].eq('P')],neg],ignore_index=True))]:
            cases.append(('M2_'+c+suffix,label,d,False))
            if not suffix:cases.append(('M2_'+c+'_source',label,d,True))
            if not suffix and c=='PN':
                e=d.copy();e['N']=e['문형'].eq('N').astype(int)
                cases.append(('M2_PN_type',label,e,'type'))
    return cases

def fit(name,label,d,source):
    print('START',name,'n',d.n.sum(),'y',d.y.sum(),flush=True)
    d.to_csv(ROOT/'data'/('input_'+name+'.csv'),index=False)
    t=(d['대표연도'].to_numpy()-1750)/20
    idx,levels=pd.factorize(d['문헌ID']);path=OUT/(name+'.nc')
    if path.exists():tr=az.from_netcdf(path)
    else:
        with pm.Model() as model:
            a=pm.Normal('a',logit((d.y.sum()+.5)/(d.n.sum()+1)),3)
            b=pm.Normal('b',0,.6)
            sd=pm.HalfNormal('document_sd',1)
            z=pm.Normal('document_z',0,1,shape=len(levels))
            eta=a+b*t+sd*z[idx]
            if source=='type':eta=eta+pm.Normal('sentence_type',0,3)*d['N'].to_numpy(float)
            elif source:eta=eta+pm.Normal('source',0,1.5)*d['자료층'].eq('대역').to_numpy(float)
            pm.Binomial('y',n=d.n.to_numpy(int),logit_p=eta,observed=d.y.to_numpy(int))
            tr=pm.sample(draws=2000,tune=2000,chains=4,cores=2,random_seed=SEED,target_accept=.99,progressbar=False,quiet=True)
        tr.to_netcdf(path,engine='h5netcdf')
    diag=az.summary(tr,ci_prob=.95,round_to='none');diag.to_csv(OUT/(name+'_diagnostics.csv'))
    b=np.asarray(tr['posterior']['b']).ravel();lo,med,hi=np.quantile(b,[.025,.5,.975])
    row={'모형':name,'문형':label,'성공수':int(d.y.sum()),'시행수':int(d.n.sum()),'문헌수':len(levels),'최초연도':float(d['대표연도'].min()),'최종연도':float(d['대표연도'].max()),'b_중앙값':med,'b_하한':lo,'b_상한':hi,'OR20_중앙값':np.exp(med),'OR20_하한':np.exp(lo),'OR20_상한':np.exp(hi),'감소사후확률':float((b<0).mean()),'Rhat최대':float(diag.r_hat.max()),'ESS최소':float(diag.ess_bulk.min()),'발산':int(np.asarray(tr['sample_stats']['diverging']).sum())}
    print('DONE',row,flush=True)
    return row

if __name__=='__main__':
    rows=[]
    for args in inputs():
        rows.append(fit(*args));pd.DataFrame(rows).to_csv(OUT/'모형결과.csv',index=False,encoding='utf-8-sig')
