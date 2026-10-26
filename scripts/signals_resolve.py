"""Week 3 step 2: resolve candidates -> data/signals.csv
- structured candidates (raw/signals/candidates_structured.csv from signals_collect.py)
- municipal pages found by site search (data/signals_seed_urls.csv; kind=list pages are expanded one level)
Undated PRE listing pages are fetched (polite.get) and dated from on-page 更新日/掲載日 labels.
Nothing is invented: rows without a verifiable date (and not fiscal-year-dated) are dropped and counted."""
import re, html, urllib.parse, datetime as dt
import pandas as pd
import polite
from signals_common import *

out, dropped = [], []
def add(code6, date, basis, title, url, source, typ=None, fy='', via=''):
    typ = typ or classify(title)
    out.append(dict(code6=code6, date=date.isoformat() if date else '', date_basis=basis or '', type=typ,
                    facility_type=facility(title), title=title.strip()[:200], url=url, source=source, fy=fy, via_url=via))

# 1. structured candidates
C = pd.read_csv(D.replace('data/', 'raw/signals/') + 'candidates_structured.csv', dtype=str).fillna('')
for r in C.itertuples():
    if r.date:
        add(r.code6, dt.date.fromisoformat(r.date), r.date_basis, r.title, r.url, r.source, r.type or None, r.fy)
    elif r.fy:
        add(r.code6, None, r.date_basis or 'fiscal_year', r.title, r.url, r.source, r.type or None, r.fy)
    else:  # PRE 166/167/168 listing pages: date from page label
        h, fu, st = polite.get(r.url)
        d, b = page_date(h) if h and st == 200 else (None, None)
        if d: add(r.code6, d, b, r.title, r.url, r.source)
        else: dropped.append((r.source, r.code6, r.title, r.url, f'no page date (status {st})'))

# 2. seed pages from municipal site search
KW = r'サウンディング|市場調査|対話|民間提案|提案募集|導入可能性|PFI|PPP|官民連携|公民連携|利活用|跡地活用'
S = pd.read_csv(D + 'signals_seed_urls.csv', dtype=str).fillna('')
def do_page(url, code6, pref, src, via=''):
    h, fu, st = polite.get(url)
    if not h or st != 200: dropped.append((src, code6, '', url, f'status {st}')); return
    full = title_of(h); segs = [x.strip() for x in re.split(r'[｜|／]| - ', full) if x.strip()]
    t = segs[0] if segs else full
    if len(t) <= 8:  # site-name-only first segment (e.g. '赤穂市｜…'): use <h1> or the longest segment
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
        h1 = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', '', h1.group(1)))).strip() if h1 else ''
        t = h1 if len(h1) > 8 else max(segs, key=len, default=t)
    c = code6 or find_muni(t + ' ' + text_of(h)[:600], pref)
    if not c: dropped.append((src, '', t, url, 'no municipality')); return
    d, b = page_date(h)
    if not d:
        fyg = re.search(r'令和\s*(\d+|元)\s*年度', t)  # undated page whose title names a fiscal year -> fiscal-year row
        if fyg:
            add(c, None, 'title_fiscal_year', t, url, src, fy=str(2018 + (1 if fyg[1] == '元' else int(fyg[1]))), via=via); return
        dropped.append((src, c, t, url, 'no page date')); return
    add(c, d, b, t, url, src, via=via)
for s in S.itertuples():
    code6 = BY_PM.get((s.pref, norm(s.muni))) if s.muni else None
    if s.kind == 'page':
        do_page(s.url, code6, s.pref, 'municipal_site_search'); continue
    h, fu, st = polite.get(s.url)
    if not h or st != 200: dropped.append(('municipal_list', code6, '', s.url, f'status {st}')); continue
    host = urllib.parse.urlparse(fu).netloc; seen = set(); n = 0
    for m in re.finditer(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', h, re.S):
        href, txt = m.group(1), re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', '', m.group(2)))).strip()
        u = urllib.parse.urljoin(fu, href)
        if urllib.parse.urlparse(u).netloc != host or u in seen or u == fu or not re.search(KW, txt) or u.lower().endswith(('.pdf', '.xlsx', '.docx', '.doc')): continue
        if not s.muni:  # prefectural list: only items naming a municipality (joint items)
            c2 = find_muni(txt, s.pref)
            if not c2: continue
        seen.add(u); n += 1
        if n > 25: break
        do_page(u, code6 if s.muni else c2, s.pref, 'municipal_site_list', via=s.url)

df = pd.DataFrame(out)
df = df[df.type != 'other']
df['pref'] = df.code6.map(lambda c: NAME[c][0]); df['muni'] = df.code6.map(lambda c: NAME[c][1])
def inwin(r):
    if r.date: return in24(dt.date.fromisoformat(r.date))
    return r.fy in ('2025', '2026')  # FY2025 (2025-04..2026-03) and FY2026 (2026-04..) lie inside the window; FY2024 only partly -> excluded
df['in_24m'] = df.apply(inwin, axis=1)
# dedupe: same municipality + url (prefer dated/most specific source order), then same muni+title+date
pri = {'municipal_site_search': 0, 'municipal_site_list': 1, 'mlit_kanmin_sounding': 2, 'cao_pfi_database': 3, 'pfikyokai_public_notices': 4}
df['_p'] = df.source.map(lambda s: pri.get(s, 5))
df['_t'] = df.title.map(norm)
df = df.sort_values(['_p', 'date']).drop_duplicates(['code6', 'url', 'type']).drop_duplicates(['code6', '_t', 'date'])
win = df[df.in_24m].drop(columns=['_p', '_t', 'in_24m']).sort_values(['date', 'code6'], ascending=[False, True])
cols = ['code6', 'pref', 'muni', 'date', 'date_basis', 'fy', 'type', 'facility_type', 'title', 'url', 'source', 'via_url']
win[cols].to_csv(D + 'signals.csv', index=False)
pd.DataFrame(dropped, columns=['source', 'code6', 'title', 'url', 'reason']).to_csv('/workspace/ppp-dashboard/raw/signals/dropped.csv', index=False)
print('signals', len(win), 'dropped', len(dropped), 'out-of-window', (~df.in_24m).sum())
print(win.type.value_counts()); print(win.pref.value_counts()); print(win.source.value_counts())
