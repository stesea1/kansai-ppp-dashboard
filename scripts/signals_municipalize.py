"""Week 3 fix: rows found via the 日本PFI・PPP協会 public board must not carry the association's text.
For each such row: locate the municipality's own page (the row URL if it is a municipal page; otherwise the municipal link
on the association's notice page), fetch it (polite.get; archived copy of the *municipal* URL via web.archive.org if the live page is gone)
and take the title from the municipal page itself. If no municipal page is found, keep facts only
(municipality, date, type, facility class) with a neutral label written by us; the association page is kept only as ref_url."""
import re, json, datetime as dt, urllib.parse as up
import polite
from signals_common import *
ASSOC = 'pfikyokai_public_notices'
def is_gov(u): return bool(re.search(GOV_HOST, up.urlparse(u).netloc))
_arch_fail = [0]
def archived(u, near):
    if _arch_fail[0] >= 3: return None, None  # archive.org unreachable from here: stop trying
    h, fu, st = polite.get('https://archive.org/wayback/available?url=' + up.quote(u, safe='') + '&timestamp=' + near.replace('-', ''))
    if h is None: _arch_fail[0] += 1; return None, None
    try: s = json.loads(h)['archived_snapshots']['closest']
    except Exception: return None, None
    if not s.get('available') or str(s.get('status')) != '200': return None, None
    au = f"https://web.archive.org/web/{s['timestamp']}id_/{u}"
    h, fu, st = polite.get(au)
    return (h, au) if h and st == 200 else (None, None)
def muni_links(u):
    h, fu, st = polite.get(u)
    if not h or st != 200: return []
    seen, out = set(), []
    for m in re.finditer(r'<a[^>]+href="([^"#]+)"', h):
        v = up.urljoin(fu, html.unescape(m.group(1)))
        if v in seen or not v.startswith('http') or not is_gov(v): continue
        seen.add(v); out.append(v)
    return sorted(out, key=lambda v: v.lower().endswith(('.pdf', '.docx', '.xlsx', '.doc', '.xls')))  # html first
def municipal_title(u, code6, near):
    """(title, how) from the municipal page itself, or (None, reason)"""
    if u.lower().endswith(('.pdf', '.docx', '.xlsx', '.doc', '.xls')): return None, 'document link (no page title)'
    h, fu, st = polite.get(u); how = 'live'
    if not h or st != 200:
        h, au = archived(u, near or '20250101'); how = 'archived'
        if not h: return None, f'municipal page gone (status {st}), no archive'
    t = page_title(h)
    if len(t) <= 8 or re.search(r'見つかりません|Not Found|エラー', t): return None, 'no usable page title'
    if norm(NAME[code6][1]) not in norm(text_of(h)) and norm(NAME[code6][1]) not in norm(t):
        return None, 'page does not name the municipality'
    return t, how
def municipalize(rows):
    """rows: list of dicts (signals). returns stats"""
    st = {'replaced_live': 0, 'replaced_archived': 0, 'muni_link_label': 0, 'facts_only': 0}; log = []
    for r in rows:
        if r['source'] != ASSOC: continue
        if r['date'] and not in24(dt.date.fromisoformat(r['date'])): continue  # out of window: dropped later anyway
        if not r['date'] and r.get('fy') not in ('2025', '2026'): continue
        assoc_ref = r['url'] if not is_gov(r['url']) else ''
        cands = [r['url']] if is_gov(r['url']) else muni_links(r['url'])
        r['date_basis'] = re.sub(r'^list_posted_date', 'pfikyokai_board_posted_date', r['date_basis'])
        done = False; first_doc = None
        for u in cands[:4]:
            t, how = municipal_title(u, r['code6'], r['date'])
            if t:
                typ = classify(t)
                r.update(title=t[:200], url=u, source='municipal_page_via_board', via_url='',
                         type=typ if typ != 'other' else r['type'], facility_type=facility(t) or r['facility_type'], title_basis='municipal page ' + how, ref_url='')
                st['replaced_archived' if how.startswith('archived') else 'replaced_live'] += 1; done = True; log.append((u, how)); break
            if how.startswith('document') and not first_doc: first_doc = u
            log.append((u, how))
        if done: continue
        if not first_doc and is_gov(r['url']): first_doc = r['url']  # municipal URL itself (page gone / unusable): keep the link, our own label
        if first_doc:
            r.update(title=neutral_label(r['type'], r['facility_type']), url=first_doc, source='municipal_document_via_board', via_url='',
                     title_basis='neutral label (own wording)', ref_url='')
            st['muni_link_label'] += 1; continue
        r.update(title=neutral_label(r['type'], r['facility_type']), url='', source='pfikyokai_board_fact', via_url='',
                 title_basis='neutral label (own wording)', ref_url=assoc_ref or 'https://www.pfikyokai.or.jp/about/about-membersnews.html')
        st['facts_only'] += 1
    return st, log
