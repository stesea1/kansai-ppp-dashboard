"""Parse 総務省 地方公営企業年鑑 個表 (.xls): returns long records (sheet, col, pref, entity, label, value, meta_*)."""
import xlrd
def parse(path):
    b = xlrd.open_workbook(path); recs = []
    for s in b.sheets():
        if s.nrows < 20: continue
        hr = None
        for r in range(min(15, s.nrows)):
            if any(str(v).strip() == '項目' for v in s.row_values(r)[:8]): hr = r; break
        if hr is None: continue
        prow = [str(v).strip() for v in s.row_values(hr - 1)]
        nrow = [str(v).strip() for v in s.row_values(hr)]
        cols = [c for c in range(s.ncols) if c > 2 and (prow[c] or nrow[c]) and prow[c] not in ('団体名',) and nrow[c] != '項目']
        if not cols: continue
        c0 = min(cols)
        meta = {}
        for r in range(0, hr - 1):
            lab = ''.join(str(v).strip() for v in s.row_values(r)[:c0])
            if lab and any(str(s.cell_value(r, c)).strip() for c in cols): meta[r] = lab
        for r in range(hr + 1, s.nrows):
            lab = ''.join(str(v).strip() for v in s.row_values(r)[:c0]).replace('\n', '').replace(' ', '')
            if not lab: continue
            for c in cols:
                ent = (nrow[c] or prow[c]).replace(' ', '').replace('\u3000', '')
                recs.append(dict(sheet=s.name, col=c, pref=prow[c].replace(' ', ''), entity=ent, label=lab, value=s.cell_value(r, c),
                                 **{f'meta_{meta[k]}': s.cell_value(k, c) for k in meta}))
    return recs
