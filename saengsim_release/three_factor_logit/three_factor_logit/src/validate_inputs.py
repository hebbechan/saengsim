"""Validate analysis scope and denominator integrity before interpreting trends."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1]
a=pd.read_csv(R/'data/annotated_G_date_corrected.csv')
assert a['분석ID'].is_unique
assert not a[a['통계 문헌·판본'].fillna('').str.contains('계축일기|서궁일기',regex=True)]['세기'].dropna().astype(str).str.contains('19').any()
b=pd.read_csv(R/'data/M4_QP_연구자보완.csv')
assert not b['문헌ID'].eq('K0228').any(), 'Mixed-century anthology must be excluded as a whole'
assert b.loc[b['문헌ID'].eq('K0949'),'대표연도'].eq(1750.5).all()
assert b.loc[b['문형'].eq('Q'),'n'].sum()==19217
assert b.loc[b['문형'].eq('P'),'n'].sum()==3167
for p in (R/'data').glob('input_*.csv'):
    d=pd.read_csv(p)
    assert ((d.y>=0)&(d.y<=d.n)&(d.n>=1)).all(),p
    assert d['대표연도'].between(1500,1955).all(),p
    assert ((d.y%1==0)&(d.n%1==0)).all(),p
print('PASS: unique target IDs, diary centuries, mixed-date exclusion, full-corpus denominators, binomial count integrity')
neg=pd.read_csv(R/'data/negative_candidates.csv.gz')
assert neg['구간ID'].is_unique
from add_negative import ordinary_negative
assert not ordinary_negative('님금이 命이 잇디 아니커시든 감히 먹디 말올디니라')
assert not ordinary_negative('감히 하지 못하게 하였다')
assert ordinary_negative('감히 나아오디 몯ᄒᆞ더라')
idx=pd.read_csv(R/'data/unit_index_labels.csv.gz',usecols=['구간ID','후보문형'])
assert neg.merge(idx,on='구간ID',validate='one_to_one')['후보문형'].eq('기타').all()
n=pd.read_csv(R/'data/M2_N_연구자보완.csv')
assert (int(n.n.sum()),int(n.y.sum()))==(30849,586)
print('PASS: N candidate uniqueness, prohibitive/causative exclusion, historical negative recognition, Q/P disjointness, new denominator totals')
