"""Rebuild the published M2 main-analysis Q/P candidate clauses from the audit population."""
from pathlib import Path
import hashlib,json
import pandas as pd
R=Path(__file__).resolve().parents[1]
D=R/'data'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    pop=D/'audit_population.csv.gz'
    a=pd.read_csv(pop)
    meta=pd.read_csv(D/'document_metadata_corrected.csv')
    a=a.drop(columns=['대표연도','연대수준']).merge(
        meta[['문헌ID','대표연도','연대수준']],on='문헌ID',how='left',validate='many_to_one')
    a=a[a['후보문형'].isin(['Q','P']) & a['대표연도'].between(1500,1955)
        & ~a['문헌ID'].eq('K0228')
        & (a['연대수준'].eq('명시 단일년')|a['문헌ID'].eq('K0949'))].copy()
    # M4 Q/P aggregates use a historical K0949 label different from N metadata.
    a.loc[a['문헌ID'].eq('K0949'),'연대수준']='사용자 지정18세기'
    cols=['구간ID','문헌ID','서명','대표연도','연대수준','자료층','목표형식포함','구간','후보문형']
    a=a[cols].copy()
    assert a['구간ID'].is_unique
    totals=a.groupby('후보문형').agg(n=('구간ID','size'),y=('목표형식포함','sum'))
    assert (int(totals.loc['Q','n']),int(totals.loc['Q','y']))==(19217,344)
    assert (int(totals.loc['P','n']),int(totals.loc['P','y']))==(3167,22)
    agg=a.rename(columns={'후보문형':'문형'}).groupby(
        ['문헌ID','서명','대표연도','연대수준','자료층','문형'],as_index=False
    ).agg(n=('구간ID','size'),y=('목표형식포함','sum'))
    expected=pd.read_csv(D/'M4_QP_연구자보완.csv')
    keys=['문헌ID','서명','대표연도','연대수준','자료층','문형']
    check=agg.merge(expected,on=keys,how='outer',suffixes=('_rebuild','_model'),indicator=True)
    assert check['_merge'].eq('both').all() and check['n_rebuild'].eq(check['n_model']).all() and check['y_rebuild'].eq(check['y_model']).all(), 'Q/P aggregate mismatch'
    target=D/'QP_candidates.csv.gz'
    a.to_csv(target,index=False,compression='gzip')
    provenance={
      'upstream_population_file':pop.name,'upstream_population_sha256':sha(pop),
      'published_file':target.name,'published_file_sha256':sha(target),
      'scope':'M2 main-analysis Q/P candidates only',
      'filter_description_ko':'Q/P 후보, 1500~1955년, 명시 단일년 또는 K0949 연구자 지정 1750.5, K0228 제외',
      'counts':{'Q':[19217,344],'P':[3167,22]},
      'unit':'기존 자동분절 구간; 연구자 문형 검토 미완료',
      'K0949_note':'Q/P 집계와 동일한 사용자 지정18세기 표기를 적용; N 집계의 연대수준 표기와 다름',
      'aggregate_check':'M4_QP_연구자보완.csv와 문헌·연대·자료층·문형별 n/y 전부 일치'
    }
    (D/'QP_candidates_provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    print('PASS: Q/P candidate IDs and all document-level n/y match M4 Q/P input')
if __name__=='__main__':main()
