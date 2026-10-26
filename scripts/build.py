"""Week-1 build: join official sources -> data/kansai_municipalities.csv, data/scores.csv, web/data.js
No imputation: missing stays NaN and is excluded from the weighted average (weights re-normalised; coverage reported)."""
import re, html, json, math, datetime as dt
import pandas as pd, numpy as np
R = '/workspace/ppp-dashboard/raw/'; D = '/workspace/ppp-dashboard/data/'; W = '/workspace/ppp-dashboard/web/'
CORE = ['大阪府','京都府','兵庫県','奈良県','和歌山県','滋賀県']; OPT = ['三重県','福井県']

def norm(s):  # name normaliser for joins
    return re.sub(r'[\s　]', '', str(s)).replace('ヶ','ケ').replace('ｹ','ケ')

# 0. master list (総務省 全国地方公共団体コード R6.1.1)
m = pd.read_csv(D+'municipalities_raw.csv', dtype=str)
m['code6'] = m['code'].str.zfill(6); m['code5'] = m['code6'].str[:5]
m['region'] = np.where(m['pref'].isin(CORE), 'core', 'optional')
m['key'] = m['pref'] + m['muni'].map(norm)
m = m[['code6','code5','pref','muni','region','key']].copy()

# 1. 有形固定資産減価償却率 (総務省 統一的な基準 財務書類 指標 R6)
k = pd.read_excel(R+'kokaikei_r06_muni.xlsx', sheet_name='R6指標', header=None).iloc[4:]
k = pd.DataFrame({'code6': k[0].astype(str).str.split('.').str[0].str.zfill(6), 'ageing_rate': pd.to_numeric(k[12], errors='coerce'),
                  'pop_kokaikei': pd.to_numeric(k[5], errors='coerce')})
m = m.merge(k, on='code6', how='left')

# 2. 財政力指数 等 (総務省 主要財政指標 R6)
s = pd.read_excel(R+'shihyo_r6_muni.xlsx', header=None).iloc[1:]
s = pd.DataFrame({'code6': s[0].astype(str).str.split('.').str[0].str.zfill(6), 'fiscal_index': pd.to_numeric(s[3], errors='coerce'),
                  'keijo_ratio': pd.to_numeric(s[4], errors='coerce'), 'future_burden': pd.to_numeric(s[6], errors='coerce')})
m = m.merge(s.drop_duplicates('code6'), on='code6', how='left')

# 3. 人口 2020 実績 & 2050 推計 (社人研 R5推計)
p = pd.read_excel(R+'ipss_kekka1.xlsx', header=None).iloc[5:]
p = p[p[1].astype(str).isin(['1','2','3'])]
p = pd.DataFrame({'code5': p[0].astype(str).str.split('.').str[0].str.zfill(5), 'pop2020': pd.to_numeric(p[4], errors='coerce'), 'pop2050': pd.to_numeric(p[10], errors='coerce')})
m = m.merge(p, on='code5', how='left'); m['pop_change_2050_pct'] = (m['pop2050']/m['pop2020']-1)*100

# 4. PPP情報リスト R7 (内閣府) — join by pref+name (code formats inconsistent in source)
rows = []
for sh in ['市区町村','政令指定都市']:
    x = pd.read_excel(R+'ppp_list_r7.xlsx', sheet_name=sh, header=None).iloc[4:]
    x = x[x[1].notna()]
    for _, r in x.iterrows():
        rows.append({'key': str(r[0]).strip()+norm(r[1]), 'plan_ppp_policy': r[4]=='○', 'yuusen_r6_3': r[5]=='○',
                     'proposal_window': r[7]=='○', 'project_list_public': r[11]=='○', 'incentive': r[13]=='○'})
pl = pd.DataFrame(rows).drop_duplicates('key'); pl['in_ppp_list'] = True
m = m.merge(pl, on='key', how='left')

# 5. 優先的検討規程 R7.3末 (内閣府 PDF; read manually from pp.2-5, see README)
Y = {'大阪府':['大阪市','堺市','豊中市','吹田市','高槻市','枚方市','茨木市','八尾市','東大阪市','池田市','和泉市','羽曳野市','門真市','柏原市'],
     '京都府':['京都市','宇治市','京田辺市'], '兵庫県':['神戸市','姫路市','明石市','西宮市','伊丹市','尼崎市','宝塚市','三田市','三木市','高砂市','相生市'],
     '奈良県':['大和郡山市','桜井市','広陵町'], '和歌山県':['和歌山市'], '滋賀県':['大津市','彦根市','長浜市','草津市'],
     '三重県':['四日市市','津市','伊勢市','鈴鹿市'], '福井県':['福井市','若狭町']}
yk = {pf+n for pf, l in Y.items() for n in l}
m['yuusen_r7_3'] = m['key'].isin(yk)
m['yuusen_flag_mismatch'] = m['yuusen_r6_3'].fillna(False).astype(bool) & ~m['yuusen_r7_3']

# 6. PFI事業基礎DB (内閣府, R7.3.31) — count by 自治体コード
f = pd.read_excel(R+'pfi_db.xlsx', header=None).iloc[2:]
cnt, rec, ending = {}, {}, {}
for _, r in f.iterrows():
    codes = set(re.findall(r'\d{6}', str(r[4])))
    d = pd.to_datetime(r[18], errors='coerce'); e = pd.to_datetime(r[22], errors='coerce')
    for c in codes:
        cnt[c] = cnt.get(c, 0)+1
        if pd.notna(d) and d >= pd.Timestamp('2020-04-01'): rec[c] = rec.get(c, 0)+1
        if pd.notna(e) and pd.Timestamp('2026-04-01') <= e <= pd.Timestamp('2031-03-31'): ending[c] = ending.get(c, 0)+1
m['pfi_total'] = m['code6'].map(cnt).fillna(0).astype(int)   # 0 = not in DB (DB is comprehensive for PFI法 projects, not other PPP)
m['pfi_since_fy2020'] = m['code6'].map(rec).fillna(0).astype(int)
m['pfi_contract_end_fy2026_30'] = m['code6'].map(ending).fillna(0).astype(int)

# 7. PRE portal (国交省) — current listings + dated update log (last 12 months)
def lines(fn):
    h = open(R+fn, encoding='utf-8', errors='ignore').read()
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)
    t = re.sub(r'<(tr|br|p|li|h\d|td|th|div)[^>]*>', '\n', t); t = html.unescape(re.sub('<[^>]+>', ' ', t))
    return [re.sub(r'\s+', ' ', l).strip().replace('\u200b','') for l in t.split('\n') if l.strip()]
prefs = CORE+OPT; munis = {(r.pref, r.muni) for r in m.itertuples()}
pre_list, pre_sound = {}, {}
for fn in ['pre_166.html','pre_167.html','pre_168.html']:
    L = lines(fn); cur = None
    for i, l in enumerate(L):
        if l in prefs and i+1 < len(L) and (l, L[i+1]) in munis: cur = l+norm(L[i+1]); continue
        if l in prefs or (i > 0 and L[i-1] in prefs): 
            if l in prefs: cur = None
            continue
        if cur and len(l) > 12 and not re.search(r'(部|課|室|係|局|グループ|担当)$', l):
            pre_list[cur] = pre_list.get(cur, 0)+1
            if 'サウンディング' in l: pre_sound[cur] = pre_sound.get(cur, 0)+1
upd = {}
today = dt.date(2026, 10, 26)
for l in lines('pre_103.html'):
    g = re.match(r'令和(\d+)年(\d+)月(\d+)日 (\S+?[都道府県])(\S+?) の', l)
    if g:
        d = dt.date(2018+int(g[1]), int(g[2]), int(g[3]))
        if (today-d).days <= 365: upd[g[4]+norm(g[5])] = upd.get(g[4]+norm(g[5]), 0)+1
m['pre_listings_now'] = m['key'].map(pre_list).fillna(0).astype(int)
m['pre_sounding_listings_now'] = m['key'].map(pre_sound).fillna(0).astype(int)
m['pre_updates_12m'] = m['key'].map(upd).fillna(0).astype(int)


# 8. 施設類型別 有形固定資産減価償却率 (総務省 財政状況資料集 R6=令和6年度決算, 描画テキストから抽出 scripts/extract_shisetsu.py)
FAC = {'道路':'road','橋りょう・トンネル':'bridge','公営住宅':'housing','港湾・漁港':'port','認定こども園・幼稚園・保育所':'nursery',
       '学校施設':'school','児童館':'jidokan','公民館':'kominkan','図書館':'library','体育館・プール':'gym','福祉施設':'welfare',
       '市民会館':'hall','一般廃棄物処理施設':'waste','保健センター・保健所':'health','消防施設':'fire','庁舎':'cityhall'}
fl = pd.read_csv(D+'shisetsu_long_raw.csv')
fl['facility'] = fl['facility'].replace({'道路・橋りょう':'道路'})
fl['pri'] = fl['file'].str.startswith('seirei').astype(int)
fl = fl[fl.entity.notna()].sort_values('pri', ascending=False).drop_duplicates(['entity','facility'])
fl['key'] = fl['entity'].map(norm)
for col, suf in [('rate_R06',''), ('ruiji_avg_R06','_ruiji'), ('ruiji_rank','_rank')]:
    pv = fl.pivot(index='key', columns='facility', values=col).rename(columns=lambda c: 'fac_'+FAC[c]+suf)
    m = m.merge(pv, left_on='key', right_index=True, how='left')
m['fac_file_found'] = m['key'].isin(set(fl['key']))

# 9. 団体全体の減価償却率: 財政状況資料集 R06 当該値（財務書類指標R6が欠損の団体のみ補填; R05は参考表示のみ）
oz = pd.read_csv(D+'overall_ageing_zaisei.csv').dropna(subset=['entity']).sort_values('file', key=lambda x: x.str.startswith('seirei'), ascending=False).drop_duplicates('entity')
oz['key'] = oz['entity'].map(norm)
m = m.merge(oz[['key','overall_R06_header','overall_R05']].rename(columns={'overall_R06_header':'ageing_rate_zaisei_R06','overall_R05':'ageing_rate_zaisei_R05_ref'}), on='key', how='left')
m['ageing_rate_all'] = m['ageing_rate'].fillna(m['ageing_rate_zaisei_R06'])
m['ageing_src'] = np.where(m['ageing_rate'].notna(), '財務書類指標R6', np.where(m['ageing_rate_all'].notna(), '財政状況資料集R06当該値', None))

# 10. 上下水道 (地方公営企業年鑑 R6=令和6年度決算 個表から算出, scripts/water.py)
ws = pd.read_csv(D+'water_sewer_r06.csv', dtype={'code6':str})
m = m.merge(ws, on='code6', how='left')

# ---------- v0 PPP pipeline score ----------
WEIGHTS = {'s_ageing':30, 's_pfi':20, 's_yuusen':15, 's_ready':10, 's_pre':10, 's_fiscal':5, 's_pop':10}
pr = lambda x: x.rank(pct=True)*100  # percentile within the 244 set (NaN stays NaN)
m['s_ageing'] = pr(m['ageing_rate'])
pfi_raw = np.log1p(m['pfi_total']) + np.log1p(m['pfi_since_fy2020'])*2
m['s_pfi'] = pfi_raw/pfi_raw.max()*100
m['s_yuusen'] = m['yuusen_r7_3'].astype(float)*100
rd = m[['plan_ppp_policy','proposal_window','project_list_public']]
m['s_ready'] = np.where(m['in_ppp_list'].fillna(False).astype(bool), rd.fillna(False).astype(float).mean(axis=1)*100, np.nan)
pre_raw = np.log1p(m['pre_listings_now'] + m['pre_updates_12m'])
m['s_pre'] = pre_raw/pre_raw.max()*100
m['s_fiscal'] = pr(m['fiscal_index'])
m['s_pop'] = pr(np.log(m['pop2020'].fillna(m['pop_kokaikei'])))
cols = list(WEIGHTS); w = pd.Series(WEIGHTS)
avail = m[cols].notna()
m['coverage_pct'] = (avail*w).sum(axis=1)/w.sum()*100
m['score_v0'] = (m[cols].fillna(0)*w).sum(axis=1)/(avail*w).sum(axis=1)
m.loc[m['coverage_pct'] < 60, 'score_v0'] = np.nan  # too little data -> no score
m['rank_core'] = m['score_v0'].where(m['region']=='core').rank(ascending=False, method='min')
m['rank_all'] = m['score_v0'].rank(ascending=False, method='min')

# ---------- v1 (optional): 老朽化成分を施設類型別で置換 ----------
# 重点分野のうちデータがある類型: 庁舎, 学校, 公営住宅, 体育館・プール, 廃棄物処理, 図書館/公民館/市民会館(文化・社会教育), 福祉施設, 保育所等, 道路, 橋りょう, 水道(管路経年化率), 下水道(管渠老朽化率)
# 火葬場・病院・空港・公園等は財政状況資料集の類型に無く欠損扱い。簡易水道の値は規模が小さく不安定なため v1 では不使用。
V1F = ['fac_cityhall','fac_school','fac_housing','fac_gym','fac_waste','fac_library','fac_kominkan','fac_hall','fac_welfare','fac_nursery','fac_road','fac_bridge']
m['w_pipe_ageing_v1'] = m['w_pipe_ageing'].where(~m['w_src'].fillna('').str.contains('簡易水道'))
V1 = V1F+['w_pipe_ageing_v1','s_pipe_ageing']
fac_pct = pd.concat({c: pr(m[c]) for c in V1}, axis=1)
m['n_fac_v1'] = fac_pct.notna().sum(axis=1)
m['s_fac_mean'] = fac_pct.mean(axis=1).where(m['n_fac_v1'] >= 3)
m['s_ageing_v1'] = pd.concat([pr(m['ageing_rate_all']), m['s_fac_mean']], axis=1).mean(axis=1)  # 全体50%+類型平均50%（片方のみなら片方）
W1 = dict(WEIGHTS); W1['s_ageing_v1'] = W1.pop('s_ageing')
c1 = list(W1); w1 = pd.Series(W1); a1 = m[c1].notna()
m['coverage_v1_pct'] = (a1*w1).sum(axis=1)/w1.sum()*100
m['score_v1'] = ((m[c1].fillna(0)*w1).sum(axis=1)/(a1*w1).sum(axis=1)).where(m['coverage_v1_pct'] >= 60)
m['rank_v1_core'] = m['score_v1'].where(m['region']=='core').rank(ascending=False, method='min')
m['rank_v1_all'] = m['score_v1'].rank(ascending=False, method='min')
# 最も老朽化した類型（R06値, 類似団体平均との差つき）
def worst(r):
    best = None
    for c in V1F:
        v = r[c]
        if pd.notna(v) and (best is None or v > best[1]): best = (c, v, r[c+'_ruiji'])
    return best
INV = {('fac_'+v): k for k, v in FAC.items()}
wv = m.apply(worst, axis=1)
m['worst_facility'] = wv.map(lambda b: INV[b[0]] if b else None)
m['worst_facility_rate'] = wv.map(lambda b: b[1] if b else np.nan)
m['n_fac_above_ruiji'] = sum((m[c] > m[c+'_ruiji']).astype(int) for c in V1F)
# ---------- untapped（未開拓）フラグ ----------
# 中小都市(2020人口 2万〜20万, 政令市除く) かつ 老朽化(v1老朽化成分)が244団体中上位40% かつ 優先的検討規程なし(R7.3末) かつ PFI実績 0〜1件
SEIREI = ['大阪市','堺市','京都市','神戸市']
pop = m['pop2020'].fillna(m['pop_kokaikei'])
m['midsmall'] = pop.between(20000, 200000) & ~m['muni'].isin(SEIREI)
m['untapped'] = m['midsmall'] & (m['s_ageing_v1'] >= 60) & ~m['yuusen_r7_3'] & (m['pfi_total'] <= 1)
m['untapped_rank'] = m['s_ageing_v1'].where(m['untapped']).rank(ascending=False, method='first')
m = m.sort_values('score_v0', ascending=False)
m.drop(columns=['key']).to_csv(D+'kansai_municipalities.csv', index=False, encoding='utf-8-sig')
m[['code6','pref','muni','region','score_v0','coverage_pct','rank_core','rank_all']+cols+['score_v1','coverage_v1_pct','rank_v1_core','rank_v1_all','s_ageing_v1','untapped','untapped_rank']].round(1).to_csv(D+'scores.csv', index=False, encoding='utf-8-sig')
out = m.drop(columns=['key']).replace({np.nan: None}).round(2).to_dict('records')
open(W+'data.js','w').write('window.PPP_DATA='+json.dumps(out, ensure_ascii=False, default=lambda o: o.item() if hasattr(o,'item') else str(o))+
    ';\nwindow.PPP_WEIGHTS='+json.dumps(WEIGHTS)+';\nwindow.PPP_WEIGHTS_V1='+json.dumps(W1)+';\nwindow.PPP_FAC='+json.dumps(FAC, ensure_ascii=False)+';\nwindow.PPP_BUILT="'+str(today)+'";\n')
geo = json.load(open(D+'kansai_muni.geojson'))
open(W+'geo.js','w').write('window.PPP_GEO='+json.dumps(geo, ensure_ascii=False, separators=(',',':'))+';\n')
# diagnostics
print('rows', len(m), m.groupby('pref').size().to_dict())
for c in ['ageing_rate','fiscal_index','pop2020','in_ppp_list']: print(c, 'missing', m[c].isna().sum())
print('yuusen r6.3 true', m['yuusen_r6_3'].sum(), 'r7.3 true', m['yuusen_r7_3'].sum(), 'mismatch', m.loc[m.yuusen_flag_mismatch,'muni'].tolist())
print('pfi>0', (m.pfi_total>0).sum(), 'pre>0', (m.pre_listings_now>0).sum(), 'upd>0', (m.pre_updates_12m>0).sum())
print('unmatched pre keys', set(pre_list)-set(m.key), set(upd)-set(m.key))
print('no score', m.loc[m.score_v0.isna(),'muni'].tolist())
print(m[m.region=='core'].head(15)[['pref','muni','score_v0','coverage_pct','ageing_rate','pfi_total','pfi_since_fy2020','yuusen_r7_3','s_ready','pre_listings_now','pre_updates_12m','fiscal_index','pop2020']].round(1).to_string())

print('--- week2 ---')
print('fac coverage', {c: int(m[c].notna().sum()) for c in V1F}, 'files', int(m.fac_file_found.sum()))
print('ageing_all', m.ageing_rate_all.notna().sum(), m.ageing_src.value_counts().to_dict())
print('water', m.w_pipe_ageing.notna().sum(), 'water_v1', m.w_pipe_ageing_v1.notna().sum(), 'sewer', m.s_pipe_ageing.notna().sum(), m.s_dep_rate.notna().sum())
print('v1 scored', m.score_v1.notna().sum(), 'untapped', int(m.untapped.sum()), 'midsmall', int(m.midsmall.sum()))
u = m[m.untapped].sort_values('untapped_rank')
print(u.head(15)[['pref','muni','pop2020','s_ageing_v1','ageing_rate_all','ageing_src','n_fac_v1','worst_facility','worst_facility_rate','n_fac_above_ruiji','w_pipe_ageing','s_pipe_ageing','pfi_total','plan_ppp_policy','score_v0','score_v1']].round(1).to_string())
