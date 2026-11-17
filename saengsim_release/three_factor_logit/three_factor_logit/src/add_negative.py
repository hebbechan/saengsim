"""Add ordinary-negative candidate environments, keeping original Q/P units fixed."""
from pathlib import Path
import re,unicodedata,hashlib,json
import pandas as pd
R=Path(__file__).resolve().parents[1]
def nfc(s):return unicodedata.normalize('NFC',s)
NEG=re.compile(nfc(r'[디지티치]\s*(?:아니|않|못|몯)|(?:^|\s)(?:못|몯|아니)(?=\s|[ᄒ하])|(?:^|\s)안\s+(?!(?:에|에서|으로|쪽)(?:\s|$))\w'))
CAUS=re.compile(nfc(r'(?:못|몯|아니)\s*(?:ᄒᆞ|하|ᄒᆡ|해)(?:게|긔)\s*(?:ᄒᆞ|하|ᄒᆡ|해)'))
PROHIB=re.compile(nfc(r'[디지티치]\s*(?:말|마ᄅᆞ|마라|마오|마소)'))
def ordinary_negative(text):
    text=nfc(str(text))
    return bool(NEG.search(text)) and not CAUS.search(text) and not PROHIB.search(text)
def main():
    path=R.parent/'models/data/unit_index.csv.gz'
    u=pd.read_csv(path)
    meta=pd.read_csv(R/'data/document_metadata_corrected.csv')
    u=u.drop(columns=['대표연도','연대수준']).merge(meta[['문헌ID','대표연도','연대수준']],on='문헌ID',how='left',validate='many_to_one')
    # Exclude mixed-century anthology for every denominator version.
    u=u[u['대표연도'].between(1500,1955)&~u['문헌ID'].eq('K0228')].copy()
    u=u[u['후보문형'].eq('기타') & u['구간'].map(ordinary_negative)].copy()
    u['문형']='N'
    cols=['구간ID','문헌ID','서명','대표연도','연대수준','자료층','목표형식포함','구간']
    u[cols].to_csv(R/'data/negative_candidates.csv.gz',index=False,compression='gzip')
    versions=[('연구자보완',u['연대수준'].eq('명시 단일년')|u['문헌ID'].eq('K0949')),('명시연대대조',u['연대수준'].eq('명시 단일년')),('확장보수',pd.Series(True,index=u.index))]
    for version,mask in versions:
        d=u[mask].groupby(['문헌ID','서명','대표연도','연대수준','자료층','문형'],as_index=False).agg(n=('구간ID','size'),y=('목표형식포함','sum'))
        d.to_csv(R/'data'/f'M2_N_{version}.csv',index=False)
        print(version,int(d.n.sum()),int(d.y.sum()),flush=True)
    # Review material is a stratified, reproducible sample, not a gold standard.
    samples=[]
    for target in [0,1]:
        d=u[u['목표형식포함'].eq(target)]
        samples.append(d.sample(min(100,len(d)),random_state=20261116))
    review=pd.concat(samples)[cols].copy()
    for c in ['연구자 문형','연구자 목표형식 확인','연구자 메모']:review[c]=''
    review.to_csv(R/'results/단순부정문_후보검토.csv',index=False,encoding='utf-8-sig')
    (R/'data/negative_provenance.json').write_text(json.dumps({'source':'models/data/unit_index.csv.gz','source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'negative_regex':NEG.pattern,'negative_causative_exclusion_regex':CAUS.pattern,'prohibitive_exclusion_regex':PROHIB.pattern,'candidate_count':len(u),'target_candidate_count':int(u['목표형식포함'].sum()),'unit':'기존 자동분절 구간; 기존Q/P/P_모호 제외; 인간검토 미완료'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
