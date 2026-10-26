"""Week-3 step 1: collect candidate signals from structured public lists -> raw/signals/candidates_structured.csv
+ dated PRE snapshot (data/snapshots/). Read-only, polite (scripts/polite.py)."""
import re, sys, html, io, datetime as dt
import pandas as pd
sys.path.insert(0, '/workspace/ppp-dashboard/scripts')
import polite
from signals_common import *
SNAP = TODAY.isoformat()
rows = []
def add(code6, title, url, source, date=None, basis='', list_cat='', type_=None, fy=''):
    rows.append(dict(code6=code6, title=re.sub(r'\s+', ' ', title).strip(), url=url, source=source, date=date.isoformat() if date else '',
                     date_basis=basis, list_category=list_cat, type=type_ or '', fy=fy))

# A. 国交省 PRE portal current listings (166 売却・貸付け / 167 総合評価・プロポーザル / 168 民間提案窓口)
PRE = 'https://www.mlit.go.jp/totikensangyo/totikensangyo_tk5_000%s.html'
snap = []
for pid, cat in [('166','売却・貸付け'), ('167','総合評価一般競争入札/公募型プロポーザル'), ('168','民間提案窓口')]:
    h, _, st = polite.get(PRE % pid)
    pref = None; pref_left = 0; cur = None; left = 0
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S):
        tds = re.findall(r'<td([^>]*)>(.*?)</td>', tr, re.S)
        if not tds: continue
        pref_left -= 1; left -= 1
        if pref_left < 0: pref = None
        if left < 0: cur = None
        for attr, body in tds:
            if re.search(r'<a ', body): continue
            txt = text_of(body).replace('\n', ' ').strip()
            rs = re.search(r'rowspan="(\d+)"', attr); span = int(rs.group(1)) if rs else 1
            pm = re.match(PREF_RE + r'[・\s]*(.*)', txt)
            if pm:
                pref = pm.group(1); pref_left = span - 1; rest = pm.group(2)
                cur = None; left = 0
                if rest:
                    cur = find_muni(rest, pref) if pref in PREFS else None; left = span - 1
                    if cur is None and pref in PREFS: cur = 'PREF:' + pref
                elif pref in PREFS: cur = 'PREF:' + pref; left = span - 1
            elif pref in PREFS and len(txt) <= 12 and re.search(r'[市町村]$', txt):
                c = find_muni(txt, pref)
                if c: cur = c; left = span - 1
        links = re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S)
        for href, a in links:
            t = text_of(a).replace('\n', '')
            if cur and pref in PREFS:
                own = not cur.startswith('PREF')
                snap.append(dict(snapshot=SNAP, page=pid, category=cat, code6=cur if own else '', entity=NAME[cur][1] if own else cur[5:],
                                 pref=NAME[cur][0] if own else cur[5:], title=t, url=html.unescape(href)))
        # a pref-only row (colspan link, no muni cell) resets muni
        if cur and not cur.startswith('PREF') and left < 0: cur = None
snap = pd.DataFrame(snap); snap.to_csv(D+f'snapshots/pre_{SNAP}_listings_kansai.csv', index=False)
for r in snap[snap.code6 != ''].itertuples():
    add(r.code6, r.title, r.url, 'mlit_pre_portal_'+r.page, list_cat=r.category)
# PRE dated update log (103): keep full Kansai log as snapshot; in-window entries become 'pre_update'
h, _, _ = polite.get(PRE % '103'); log = []
for l in text_of(h).split('\n'):
    g = re.match(r'令和(\d+)年(\d+)月(\d+)日\s*'+PREF_RE+r'(\S+?)\s*の(.+?)の掲載を(\S+?)しました', l)
    if g and g[4] in PREFS:
        d = dt.date(2018+int(g[1]), int(g[2]), int(g[3])); c = find_muni(g[4]+g[5], g[4])
        log.append(dict(snapshot=SNAP, date=d.isoformat(), pref=g[4], entity=g[5], code6=c or '', category=g[6], action=g[7], line=l))
log = pd.DataFrame(log); log.to_csv(D+f'snapshots/pre_{SNAP}_updatelog_kansai.csv', index=False)
for r in log[(log.code6 != '')].itertuples():
    d = dt.date.fromisoformat(r.date)
    if in24(d): add(r.code6, r.line, PRE % '103', 'mlit_pre_portal_103', d, 'pre_log', r.category, 'pre_update')
print('PRE listings', len(snap), 'muni', (snap.code6 != '').sum(), '| log Kansai', len(log))

# B. 国交省 官民連携 サウンディング(官民対話) registered cases; date = dialogue date (近畿 block)
MB = 'https://www.mlit.go.jp/sogoseisaku/kanminrenkei/sosei_kanminrenkei_rd1_%s.html'
for pid, d in [('000155', dt.date(2024,11,8)), ('000197', dt.date(2025,7,28)), ('000210', dt.date(2025,11,21)), ('000252', dt.date(2026,7,28))]:
    h, _, _ = polite.get(MB % pid); n = 0
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S):
        tds = [text_of(x).replace('\n', ' ') for x in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if len(tds) < 3: continue
        pm = re.match(r'\s*'+PREF_RE+r'\s*(\S*)', tds[0]); pm2 = re.match(r'\s*(\S+?)（'+PREF_RE+r'）', tds[0])
        if pm2: pref, ent = pm2.group(2), pm2.group(1)
        elif pm: pref, ent = pm.group(1), pm.group(2)
        else: continue
        if pref not in PREFS or not ent: continue
        c = find_muni(pref + ent, pref)
        if c: add(c, f'{tds[1]}（国交省サウンディング 官民対話・{tds[2]}）', MB % pid, 'mlit_kanmin_sounding', d, 'event_date', type_='sounding'); n += 1
    print('MLIT sounding', pid, n)

# C. 日本PFI・PPP協会 public notice board (国・自治体等からのお知らせ, non-member page; we keep only date/entity/title + link to the original)
h, _, _ = polite.get('https://www.pfikyokai.or.jp/about/about-membersnews.html'); n = 0
PS = {p[:-1] if p != '京都府' and p != '大阪府' else p[:2]: p for p in PREFS}
for tr in re.findall(r'<tr>(.*?)</tr>', h, re.S):
    tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
    if len(tds) < 3: continue
    d = wa2date(text_of(tds[0])); ent = text_of(tds[1]); a = re.search(r'href="([^"]+)"', tds[2]); t = text_of(tds[2]).replace('\n', '')
    pm = re.match(r'(.+?)\((.+?)\)', ent)
    if not pm or pm.group(2) not in PS: continue
    c = find_muni(pm.group(1), PS[pm.group(2)])
    if c and norm(NAME[c][1]) == norm(pm.group(1)) and a:
        add(c, t, html.unescape(a.group(1)), 'pfikyokai_public_notices', d, 'list_posted_date'); n += 1
print('協会 notices Kansai municipal (live page)', n)
# C2. older notices (live page only keeps ~12 months): Internet Archive snapshots of the same public page, monthly
cdx, _, _ = polite.get('https://web.archive.org/cdx/search/cdx?url=pfikyokai.or.jp/about/about-membersnews.html&output=json&from=2024&to=2026&filter=statuscode:200&collapse=timestamp:6')
import json as _j
seen = {(r['code6'], r['title']) for r in rows if r['source'] == 'pfikyokai_public_notices'}; n = 0
for ts, orig in [(x[1], x[2]) for x in _j.loads(cdx)[1:] if x[1] >= '20241101']:
    wb = f'https://web.archive.org/web/{ts}id_/{orig}'
    h, _, st = polite.get(wb)
    if st != 200 or not h: continue
    for tr in re.findall(r'<tr>(.*?)</tr>', h, re.S):
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
        if len(tds) < 3: continue
        d = wa2date(text_of(tds[0])); ent = text_of(tds[1]); a = re.search(r'href="([^"]+)"', tds[2]); t = text_of(tds[2]).replace('\n', '')
        pm = re.match(r'(.+?)\((.+?)\)', ent); pm2 = re.match(PREF_RE + r'(.+)$', ent)
        if pm and pm.group(2) in PS: pref, mu = PS[pm.group(2)], pm.group(1)
        elif pm2 and pm2.group(1) in PREFS: pref, mu = pm2.group(1), pm2.group(2)
        else: continue
        if not a: continue
        c = find_muni(mu, pref)
        if c and norm(NAME[c][1]) == norm(mu) and (c, t) not in seen:
            u = html.unescape(a.group(1))
            if u.startswith('/'): u = 'https://www.pfikyokai.or.jp' + u
            seen.add((c, t)); add(c, t, u, 'pfikyokai_public_notices', d, 'list_posted_date(archived:'+ts[:8]+')'); n += 1
print('協会 notices Kansai municipal (archive.org snapshots)', n)

# D. 内閣府 PFI事業 基礎データベース: 実施方針公表日 inside window (DB current to 2025-03-31)
b, _, _ = polite.get('https://www8.cao.go.jp/pfi/pfi_jouhou/jigyou/data/pfijigyo_database.xlsx', binary=True)
f = pd.read_excel(io.BytesIO(b), header=None).iloc[2:]; n = 0
for r in f.itertuples(index=False):
    d = pd.to_datetime(r[18], errors='coerce')
    if pd.isna(d) or not in24(d.date()): continue
    for c in set(re.findall(r'\d{6}', str(r[4]))):
        if c in NAME: add(c, f'{r[1]}（実施方針公表）', 'https://www8.cao.go.jp/pfi/pfi_jouhou/jigyou/jigyou_index.html', 'cao_pfi_database', d.date(), 'db_jisshi_houshin_date', type_='jisshi_houshin'); n += 1
print('内閣府DB in window', n)

# E. 内閣府 令和7年度 実施方針公表 PFI事業一覧 (fiscal-year only; date resolved later if a dated public page is found)
URL7 = 'https://www8.cao.go.jp/pfi/pfi_jouhou/pfi_joukyou/pdf/jigyoukensuu_kr7b01.pdf'
for l in open('/workspace/ppp-dashboard/raw/signals/kr7b01.txt', encoding='utf-8'):
    g = re.match(r'\s*\d+\s+(\S.*?\S)\s{2,}'+PREF_RE+r'(\S+)\s*$', l)
    if g and g[2] in PREFS:
        c = find_muni(g[2]+g[3], g[2])
        if c: add(c, g[1] + '（実施方針公表・令和7年度）', URL7, 'cao_jisshi_houshin_list_r7', None, 'fiscal_year', type_='jisshi_houshin', fy='2025')
out = pd.DataFrame(rows); out.to_csv('/workspace/ppp-dashboard/raw/signals/candidates_structured.csv', index=False)
print(out.source.value_counts())
