"""財政状況資料集（令和6年度決算）の描画オブジェクト(テキストボックス)から抽出。
(1) 施設類型別ストック情報分析表①②: 【施設】有形固定資産減価償却率 -> data/shisetsu_long_raw.csv
(2) 公会計指標分析・財政指標組合せ分析表: 団体全体の有形固定資産減価償却率 -> data/overall_ageing_zaisei.csv
規則: 文字色 FF0000 = 当該団体値, 000080 = 類似団体平均, 年度は最も近い 'R0x' 軸ラベルの x 座標で判定。
値が '-' や空欄の場合は NaN（補完しない）。団体名は図中の赤字「都道府県名+市町村名」から特定。"""
import re, zipfile, glob, csv, os
import pandas as pd
FILES = sorted(glob.glob('/workspace/ppp-dashboard/raw/zaisei/files/*.xls*'))
_m = pd.read_csv('/workspace/ppp-dashboard/data/municipalities_raw.csv', dtype=str)
KNOWN = set(_m.pref + _m.muni)
NUM = re.compile(r'-?\d+(\.\d+)?')
def shapes_of(d):
    sh = []
    for m in re.finditer(r'<xdr:sp\b.*?</xdr:sp>', d, re.S):
        s = m.group(0); t = ''.join(re.findall(r'<a:t>([^<]*)</a:t>', s)).strip()
        if not t: continue
        off = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"', s)
        rcol = re.findall(r'<a:rPr[^>]*>.*?<a:solidFill><a:(?:srgbClr|schemeClr) val="([^"]+)"', s, re.S)
        sh.append((t, int(off.group(1)) if off else None, int(off.group(2)) if off else None, rcol[0] if rcol else None))
    return sh
def series(blk):
    labels = {s[0]: s[1] for s in blk if re.fullmatch(r'R0\d|H\d\d', s[0])}
    def yr(x): return min(labels, key=lambda k: abs(labels[k] - x)) if labels and x is not None else None
    vals, avg = {}, {}
    for t, x, y, c in blk:
        if NUM.fullmatch(t) and c in ('FF0000', '000080'):
            (vals if c == 'FF0000' else avg).setdefault(yr(x), float(t))
    rank = next((blk[k + 1][0] for k, s in enumerate(blk[:-1]) if s[0] == '類似団体内順位'), None)
    return vals, avg, rank
out, overall, log = [], [], []
for fn in FILES:
    try: z = zipfile.ZipFile(fn)
    except Exception as e: log.append((fn, 'not-zip', 0, 0)); continue
    entity = None; year_title = None; got = 0; got_o = 0
    drawings = sorted((n for n in z.namelist() if re.match(r'xl/drawings/drawing\d+\.xml$', n)), key=lambda n: int(re.findall(r'\d+', n)[-1]))
    parsed = []
    for dn in drawings:
        d = z.read(dn).decode('utf-8', 'ignore')
        sh = shapes_of(d); parsed.append((d, sh))
        if not entity:
            entity = next((t for t, *_ in sh if t in KNOWN), None)
        if not year_title:
            year_title = next((t for t, *_ in sh if re.fullmatch(r'令和\d+年度', t)), None)
    for d, shapes in parsed:
        if '施設類型別ストック情報分析表' in d:
            idx = [i for i, s in enumerate(shapes) if s[0].startswith('【') and '有形固定資産減価償却率' in s[0]]
            allt = [i for i, s in enumerate(shapes) if s[0].startswith('【')]
            for i in idx:
                nxt = min([j for j in allt if j > i] + [len(shapes)])
                vals, avg, rank = series(shapes[i + 1:nxt])
                fac = re.match(r'【(.+?)】', shapes[i][0]).group(1)
                out.append({'file': os.path.basename(fn), 'entity': entity, 'title_year': year_title, 'facility': fac,
                            'rate_R06': vals.get('R06'), 'rate_R05': vals.get('R05'), 'rate_R02': vals.get('R02'),
                            'ruiji_avg_R06': avg.get('R06'), 'ruiji_rank': rank, 'years_found': ','.join(sorted(k for k in vals if k))})
                got += 1
        elif '債務償還比率' in d and '有形固定資産減価償却率' in d:
            ii = [i for i, s in enumerate(shapes) if s[0] == '有形固定資産減価償却率']
            jj = [i for i, s in enumerate(shapes) if '債務償還比率' in s[0]]
            if not ii or not jj: continue
            blk = shapes[ii[0] + 1: min(j for j in jj if j > ii[0])]
            vals, avg, rank = series(blk)
            head = next((s[0] for s in blk if s[0].startswith('[')), None)
            hv = re.search(r'-?\d+(\.\d+)?', head or ''); 
            overall.append({'file': os.path.basename(fn), 'entity': entity, 'title_year': year_title,
                            'overall_R06_header': float(hv.group(0)) if hv else None,
                            **{f'overall_{k}': vals.get(k) for k in ['R02', 'R03', 'R04', 'R05', 'R06']},
                            'ruiji_avg_R06': avg.get('R06'), 'ruiji_rank': rank})
            got_o += 1
    log.append((fn, entity, got, got_o))
pd.DataFrame(out).to_csv('/workspace/ppp-dashboard/data/shisetsu_long_raw.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(overall).to_csv('/workspace/ppp-dashboard/data/overall_ageing_zaisei.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(log, columns=['file', 'entity', 'n_facility_blocks', 'n_overall']).to_csv('/workspace/ppp-dashboard/data/shisetsu_extract_log.csv', index=False)
print(len(out), 'facility rows;', len(overall), 'overall rows')
