from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
d=pd.read_csv(ROOT/'results/모형결과.csv')
main=d[~d['모형'].str.contains('_source|_metadata|_expanded|_type',regex=True)].sort_values(['모형'])
main.to_csv(ROOT/'results/주분석결과.csv',index=False,encoding='utf-8-sig')
added=d[d['모형'].str.match(r'M[123]_(?:N|PN)(?:_|$)')]
added.to_csv(ROOT/'results/생심도_추가분석결과.csv',index=False,encoding='utf-8-sig')
checks=[]
for path in sorted((ROOT/'data').glob('input_*.csv')):
    x=pd.read_csv(path)
    assert ((x.y>=0)&(x.y<=x.n)&(x.n>=1)).all()
    assert ((x.y%1==0)&(x.n%1==0)).all()
    assert x['대표연도'].notna().all()
    checks.append({'입력':path.name,'행수':len(x),'성공수':int(x.y.sum()),'시행수':int(x.n.sum())})
assert len(d)==27 and len(main)==12
assert (d['Rhat최대']<1.01).all()
assert (d['ESS최소']>=400).all()
assert (d['발산']==0).all()
(ROOT/'results/검증.json').write_text(json.dumps({'입력검사':checks,'모형수':len(d),'진단통과':True},ensure_ascii=False,indent=2))
lines=['# 세 가지 통시 검정 결과','',
'연도 단위는20년이다. 아래 수치는 사후중앙값과95%등꼬리 신용구간이다. OR20<1은 해당 목표비율의 감소를 뜻하며 확률의 퍼센트포인트 변화가 아니다.','',
'|모형|문형|성공/시행|문헌수|OR20 [95% 신용구간]|감소 사후확률|',
'|---|---|---:|---:|---|---:|']
for _,r in main.iterrows():
    lines.append(f"|{r['모형']}|{r['문형']}|{r['성공수']}/{r['시행수']}|{r['문헌수']}|{r['OR20_중앙값']:.3f} [{r['OR20_하한']:.3f}, {r['OR20_상한']:.3f}]|{r['감소사후확률']:.4f}|")
lines+=['','M1: 해당 문형의생심류 내부에서 생심이나(Q) 또는생심도(P/N/PN)의 점유율. M2: 해당 문형의 전체 후보구간 중 생심류·감히를 포함한 구간 비율. M3: 해당 문형의DARE용례 중생심류 비율. N은단순부정문, PN은부정명령문+단순부정문이다.','',
'## 민감도 분석','',
'|모형|문형|성공/시행|OR20 [95% 신용구간]|','|---|---|---:|---|']
for _,r in d[~d['모형'].isin(main['모형'])].iterrows():
    lines.append(f"|{r['모형']}|{r['문형']}|{r['성공수']}/{r['시행수']}|{r['OR20_중앙값']:.3f} [{r['OR20_하한']:.3f}, {r['OR20_상한']:.3f}]|")
clear=main.loc[main['OR20_상한']<1,'모형'].tolist()
lines+=['','95%신용구간이OR=1아래에 있는 주분석: '+', '.join(clear)+'. 단순부정문 생심류는10예(생심도8예)에 불과하므로 내부모형 추정은 특히 희소자료·사전분포에 주의한다. PN합계는단순부정문과부정명령문의 구성비 변화에도 영향을 받는다. M2의주분석·자료층통제·연대확장 결과를 함께 비교하고 유리한 결과만 선택하지 않는다.','',f"{len(d)}개 적합 모두 발산0, 최대Rhat={d['Rhat최대'].max():.5f}, 최소bulk ESS={d['ESS최소'].min():.0f}.",'',
'_source는대역 자료층 통제, _metadata는원 명시단일년 범위, _expanded는추정 대표연도 포함 범위이다. _type은PN합계에서문형(N=1/P=0)을통제한다. 자세한 비율 정의·사전분포·자료범위·귀년 제한은README를 참조한다.','',
'95%신용구간이1아래에 있으면 이 모형에서 감소 근거가 비교적 명확하다. 포함하면 감소 여부가 불확실하며 변화가 없다는 증거와 구별한다. 수사/진성 의문을 분리하지 않았으며4000예 전체가 수동확정된 것은 아니다. 신규M2_N은일반부정표지 자동후보로,200예 검토표도 수동확정 이전이다. 서로 다른분모의OR로 원인강도를 직접 비교하거나 경쟁의 인과성을 확정하지 않는다.']
lines+=['','## 생심도 추가 분석의 해석','',
'단순부정문 단독 M1은8/10예로 생심도 내부점유율 감소를 보이지만 표본이 매우 작다. 단순부정문 단독 M3의생심류 대감히 감소는 불확실하다. 부정명령문+단순부정문을 합치고 문형을 통제한 결과는 다음과 같다.','',
'|문형 통제 모형|OR20 [95% 신용구간]|','|---|---|']
for name in ['M1_PN_type','M2_PN_type','M3_PN_type']:
    r=d.set_index('모형').loc[name]
    lines.append(f"|{name}|{r['OR20_중앙값']:.3f} [{r['OR20_하한']:.3f}, {r['OR20_상한']:.3f}]|")
lines+=['','합계 범위에서 생심도의 내부점유율 감소와 생심류 전체의감히 대비점유율 감소가 관찰된다. 후자의구간 상한은1에 가까워 제한적인 근거이다. 내부·외부 OR크기로 원인강도를 순위화하지 않는다. M2의단순부정 및 합계선택률은 주분석·자료층통제·확장연대에서 상승하므로 이 확대 범위의 환경축소 가설을 지지하지 않는다. 좁은 문형계수 사전분포와의 비교도 별도CSV에 보존했다.']
(ROOT/'results/결과보고서_ko.md').write_text('\n'.join(lines)+'\n')
print(main[['모형','성공수','시행수','OR20_중앙값','OR20_하한','OR20_상한']].to_string(index=False))
