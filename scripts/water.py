"""上下水道 indicators from 総務省 令和6年度地方公営企業年鑑 個表 (R6 = 令和6年度決算).
Water (水道事業, 法適用, 末端給水 + 簡易水道):
  管路経年化率 = 法定耐用年数を経過した管路延長 / 導送配水管延長 x100
  有形固定資産減価償却率 = 減価償却累計額 / 償却資産 x100
Sewer (公共下水道, 法適用):
  管渠老朽化率 = 法定耐用年数を超えた管渠延長 / 下水管布設延長 x100
  有形固定資産減価償却率 = 減価償却累計額 / 償却資産 x100
Ratios are computed from the published amounts (same definitions as 経営比較分析表), not copied.
"""
import sys, re, pandas as pd
sys.path.insert(0, '/workspace/ppp-dashboard/scripts'); import nenkan
R = '/workspace/ppp-dashboard/raw/water/'
m = pd.read_csv('/workspace/ppp-dashboard/data/municipalities_raw.csv', dtype=str)
def num(v):
    try: return float(v)
    except: return 0.0 if str(v).strip() == '-' else None
def pick(d, pat):
    x = d[d.label.str.contains(pat, regex=True)]
    return x.groupby(['sheet', 'col'])['value'].first().map(num)
def table(files, pats, extra=None):
    out = None
    for key, (f, pat) in pats.items():
        d = pd.DataFrame(nenkan.parse(R + f))
        base = d.groupby(['sheet', 'col']).first()[['pref', 'entity'] + [c for c in d.columns if c.startswith('meta_')]]
        s = pick(d, pat).rename(key)
        t = base.join(s, how='left')
        t = t.reset_index().set_index(['pref', 'entity'] + [c for c in d.columns if c.startswith('meta_')])[[key]]
        out = t if out is None else out.join(t, how='outer')
    return out.reset_index()
# --- water
w = table(None, {'len': ('001064895.xls', r'^（８）導送配水管延長'), 'old': ('001064895.xls', r'^うち法定耐用年数を経過した管路延長'),
                 'dep_asset': ('001064898.xls', r'^イ．償却資産'), 'dep_acc': ('001064898.xls', r'^ウ．減価償却累計額')})
w = w[w.meta_事業.isin(['末端給水事業', '簡易水道事業'])]
w.to_csv('/workspace/ppp-dashboard/data/water_nenkan_r06_raw.csv', index=False)
# --- sewer (公共下水道)
s = table(None, {'len': ('001065539.xls', r'^（16）下水管布設延長'), 'old': ('001065539.xls', r'法定耐用年数を超えた管渠延長'),
                 'dep_asset': ('001065592.xls', r'^イ.?償却資産'), 'dep_acc': ('001065592.xls', r'^ウ.?減価償却累計額')})
s.to_csv('/workspace/ppp-dashboard/data/sewer_nenkan_r06_raw.csv', index=False)
# union (企業団) membership for 末端給水 in Kansai, from 付表 一部事務組合構成団体一覧表 (001064899.xls)
UNION = {'長浜水道企業団': ('滋賀県', ['長浜市', '米原市']), '西播磨水道企業団': ('兵庫県', ['相生市', 'たつの市']),
         '淡路広域水道企業団': ('兵庫県', ['洲本市', '南あわじ市', '淡路市']), '磯城郡水道企業団': ('奈良県', ['川西町', '三宅町', '田原本町']),
         '大阪広域水道企業団': ('大阪府', None)}
def agg(df):
    g = df.groupby(['pref', 'entity'])[['len', 'old', 'dep_asset', 'dep_acc']].sum(min_count=1).reset_index()
    g['ageing_pipe'] = (g.old / g.len * 100).round(1)
    g['dep_rate'] = (g.dep_acc / g.dep_asset.where(g.dep_asset > 0) * 100).round(1)
    g['ageing_pipe'] = g.ageing_pipe.where(g.len > 0)
    return g
wa = agg(w[w.meta_事業 == '末端給水事業']); wk = agg(w[w.meta_事業 == '簡易水道事業'])
sa = agg(s)
SEIREI = {'京都市', '大阪市', '堺市', '神戸市'}
rows = []
for _, r in m.iterrows():
    pref, muni = r.pref, r.muni
    rec = dict(code6=str(r.code).zfill(6))
    x = wa[(wa.pref == pref) & (wa.entity == muni)]; src = '自団体(上水道)'
    if x.empty:
        x = wk[(wk.pref == pref) & (wk.entity == muni)]; src = '自団体(簡易水道・法適用)'
    if x.empty:
        for u, (up, members) in UNION.items():
            if up == pref and (members is None or muni in members):
                x = wa[wa.entity == u]; src = f'{u}(末端給水・企業団全体値)'
                if members is None: src += '※構成団体推定'
                break
    if not x.empty:
        rec.update(w_pipe_ageing=x.ageing_pipe.iloc[0], w_dep_rate=x.dep_rate.iloc[0], w_src=src)
    y = sa[((sa.pref == pref) | ((sa.pref.fillna('') == '') & muni.endswith('市') & (muni in SEIREI))) & (sa.entity == muni)]
    if not y.empty:
        rec.update(s_pipe_ageing=y.ageing_pipe.iloc[0], s_dep_rate=y.dep_rate.iloc[0], s_src='自団体(公共下水道・法適用)')
    rows.append(rec)
out = pd.DataFrame(rows)
out.to_csv('/workspace/ppp-dashboard/data/water_sewer_r06.csv', index=False)
print(out.notna().sum()); print(out.w_src.value_counts())
