import unicodedata
"""Shared helpers for the week-3 signals layer (read-only; all fetching via polite.get)."""
import re, html, datetime as dt
import pandas as pd
D = '/workspace/ppp-dashboard/data/'
TODAY = dt.date(2026, 10, 26); START = dt.date(2024, 10, 26)
PREFS = ['大阪府','京都府','兵庫県','奈良県','和歌山県','滋賀県','三重県','福井県']
PREF_RE = '(' + '|'.join(PREFS) + '|東京都|北海道|[^\\s都道府県]{2,3}県)'
def norm(s): return re.sub(r'[\s\u3000]', '', str(s)).replace('ヶ','ケ').replace('ｹ','ケ')
M = pd.read_csv(D+'municipalities_raw.csv', dtype=str); M['code6'] = M['code'].str.zfill(6)
BY_PM = {(r.pref, norm(r.muni)): r.code6 for r in M.itertuples()}
BY_M = {}
for r in M.itertuples(): BY_M.setdefault(norm(r.muni), []).append(r.code6)
NAME = {r.code6: (r.pref, r.muni) for r in M.itertuples()}
def find_muni(text, pref_hint=None):
    """return code6 for the first Kansai municipality named in text (pref-qualified match preferred; ambiguous bare names need pref_hint)"""
    t = norm(text)
    for (p, mu), c in sorted(BY_PM.items(), key=lambda x: -len(x[0][1])):
        if p+mu in t: return c
    for mu, cs in sorted(BY_M.items(), key=lambda x: -len(x[0])):
        if mu in t:
            if len(cs) == 1 and (pref_hint is None or NAME[cs[0]][0] == pref_hint): return cs[0]
            if pref_hint:
                for c in cs:
                    if NAME[c][0] == pref_hint: return c
    return None
def wa2date(s):
    """first date in text: 令和X年M月D日 / 2026年M月D日 / 2026-M-D / 2026/M/D / R8.10.1"""
    s = s.replace('元年', '1年')
    s = s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    for pat, f in [(r'令和\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日', lambda g: (2018+int(g[0]), int(g[1]), int(g[2]))),
                   (r'(20\d\d)\s*年\s*(\d+)\s*月\s*(\d+)\s*日', lambda g: tuple(map(int, g))),
                   (r'(20\d\d)[/\-.](\d{1,2})[/\-.](\d{1,2})', lambda g: tuple(map(int, g))),
                   (r'R\s*(\d+)\.(\d{1,2})\.(\d{1,2})', lambda g: (2018+int(g[0]), int(g[1]), int(g[2])))]:
        g = re.search(pat, s)
        if g:
            try: return dt.date(*f(g.groups()))
            except ValueError: pass
    return None
def text_of(h):
    t = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', '', h or '', flags=re.S)
    t = re.sub(r'<(tr|br|p|li|h\d|td|th|div|dt|dd)[^>]*>', '\n', t); t = html.unescape(re.sub('<[^>]+>', ' ', t))
    return '\n'.join(re.sub(r'[ \t\u3000\xa0]+', ' ', l).strip() for l in t.split('\n') if l.strip())
LABELS = r'(?:最終更新日|更新日|掲載日|公開日|登録日|作成日|公表日|ページ更新日|更新)'
def page_date(h):
    """(date, basis) from a municipal page: labelled 更新日/掲載日 etc. ; else None"""
    t = text_of(h)
    for m in re.finditer(LABELS + r'\s*[:：]?\s*([^\n]{0,30})', t):
        d = wa2date(m.group(1))
        if d and dt.date(2015,1,1) <= d <= TODAY: return d, 'page_label:' + re.sub(r'\s', '', m.group(0))[:4]
    for m in re.finditer(r'([^\n]{0,25})\s*(?:更新|掲載|公開)', t):
        d = wa2date(m.group(1))
        if d and dt.date(2015,1,1) <= d <= TODAY: return d, 'page_label:更新(後置)'
    return None, None
def title_of(h):
    m = re.search(r'<title[^>]*>(.*?)</title>', h or '', re.S)
    return re.sub(r'\s+', ' ', html.unescape(m.group(1))).strip() if m else ''
def classify(title):
    """keyword rules (order matters). 'other' = not a PPP signal (land sale, naming rights, seminar...) -> excluded from signals.csv"""
    t = unicodedata.normalize('NFKC', title)
    if re.search(r'セミナー|研修|講演|勉強会|プラットフォーム(セミナー|会員|の開催)|ネーミングライツ', t): return 'other'
    if re.search(r'実施方針', t) and not re.search(r'サウンディング', t): return 'jisshi_houshin'
    if re.search(r'導入可能性|可能性調査|アドバイザリー|事業手法(の)?検討|官民連携(手法)?(の)?導入検討|事業者選定(発注)?支援|PPP/?PFI.{0,6}検討業務|調査検討業務|要件検討業務|フィージビリティ', t): return 'fs'
    if re.search(r'サウンディング|市場調査|対話|意見交換会|アイデア募集|マーケット|ヒアリング|ニーズ調査|事業者アンケート|企業アンケート|事業者様?向けアンケート|民間事業者.{0,8}アンケート', t):
        return 'sounding_result' if re.search(r'結果', t) else 'sounding'
    if re.search(r'民間提案|提案募集|提案制度|提案窓口|利活用案|事業提案', t): return 'minkan_teian'
    if re.search(r'指定管理', t) and not re.search(r'PFI|整備|改修|包括', t): return 'shitei_kanri'
    if re.search(r'売払|売却|売り払い|貸付|貸し付け|お貸しします|公有財産|市有地|町有地|保有地', t) and not re.search(r'利活用事業|整備|活用事業|プロポーザル', t): return 'other'
    if re.search(r'PFI|PPP|DBO|コンセッション|運営権|包括(的)?(民間)?(管理|委託)|プロポーザル|事業者(の)?(募集|公募|選定)|公募|募集要項|入札説明書|入札公告|優先交渉権者|契約候補者|設置等予定者|官民連携|民営化|整備(運営)?事業(について|に係る)?|整備等事業|利活用事業|跡地(の)?(利)?活用', t): return 'procurement'
    return 'other'
FAC = [('water_sewer', r'下水|上水|水道|浄水|配水|水再生|ウォーターPPP|処理場'), ('waste', r'ごみ|廃棄物|クリーンセンター|清掃|最終処分|リサイクル|環境センター'),
       ('school', r'学校|小学校|中学校|校舎|幼稚園|学校跡'), ('school_meal', r'給食'), ('housing', r'住宅|団地'), ('park', r'公園|緑地|Park-PFI|パーク'),
       ('cityhall', r'庁舎'), ('library', r'図書館'), ('gym_pool', r'体育館|プール|スポーツ|運動|アリーナ|武道館'), ('hall_culture', r'文化|会館|ホール|市民センター|公民館|交流'),
       ('crematorium', r'火葬|斎場|墓'), ('welfare', r'福祉|保育|こども|児童|介護|健康'), ('tourism', r'温泉|観光|宿泊|キャンプ|自然の家|城|道の駅'),
       ('lighting_energy', r'LED|照明|空調|エネルギー|太陽光'), ('land_reuse', r'跡地|用地|未利用|遊休|旧|市有地|町有地|財産')]
def facility(title):
    hits = [k for k, p in FAC if re.search(p, title)]
    return hits[0] if hits else ''
def in24(d): return d is not None and START <= d <= TODAY
def page_title(h):
    """the page's own item title: first <title> segment, or <h1>/longest segment when the first segment is only the site name"""
    full = title_of(h); segs = [x.strip() for x in re.split(r'[｜|／]| - ', full) if x.strip()]
    t = segs[0] if segs else full
    if len(t) <= 8:
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', h or '', re.S)
        h1 = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', '', h1.group(1)))).strip() if h1 else ''
        t = h1 if len(h1) > 8 else max(segs, key=len, default=t)
    return t
GOV_HOST = r'(\.lg\.jp$|^(www\d*\.)?(city|town|vill|pref)\.|\.(city|town|vill)\.|^www\.nishi\.or\.jp$)'
TYPE_JA = {'sounding': 'サウンディング型市場調査', 'sounding_result': 'サウンディング結果公表', 'jisshi_houshin': '実施方針公表',
           'fs': '導入可能性調査', 'minkan_teian': '民間提案募集', 'procurement': 'PPP/PFI等 事業者公募・選定',
           'shitei_kanri': '指定管理者公募', 'pre_update': 'PRE掲載更新'}
FAC_JA = {'water_sewer': '上下水道', 'waste': '廃棄物処理', 'school': '学校', 'school_meal': '給食', 'housing': '住宅', 'park': '公園',
          'cityhall': '庁舎', 'library': '図書館', 'gym_pool': 'スポーツ施設', 'hall_culture': '文化・交流施設', 'crematorium': '斎場',
          'welfare': '福祉施設', 'tourism': '観光施設', 'lighting_energy': 'エネルギー・照明', 'land_reuse': '未利用地・跡地'}
def neutral_label(typ, fac):
    """our own wording; contains no third-party text"""
    return f"{TYPE_JA.get(typ, typ)}（{FAC_JA[fac] + '・案件名不明' if fac in FAC_JA else '施設名不明'}）"
