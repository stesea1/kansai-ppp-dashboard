# Data license / データのライセンス

## Scope / 対象
Processed data in this repository — `data/*.csv`, `data/snapshots/*.csv`, `data/kansai_muni.geojson`, `web/data.js`, `web/geo.js` — is licensed under the
**Creative Commons Attribution 4.0 International (CC BY 4.0)** license: https://creativecommons.org/licenses/by/4.0/
(exceptions in "Not covered" below).

本リポジトリの加工データ（`data/`、`web/data.js`、`web/geo.js`）は **CC BY 4.0** で提供します（下記「対象外」を除く）。

## Required attribution / 必要なクレジット表示
> 関西PPP/PFIパイプライン・ダッシュボード (Hao Yue), CC BY 4.0 — https://github.com/stesea1/kansai-ppp-dashboard

When you reuse the data you must **also credit the underlying official sources** (see table) and state that the data was processed
(e.g. 「○○（総務省）を加工して作成」). Do not present the processed data as if it had been produced by the government.

再利用の際は、上記に加えて **原典（下表）の出典** と、加工したことを必ず記載してください。加工データを国・自治体が作成したかのように公表しないでください。

## Underlying sources / 原典と利用条件 (checked 2026-10-26)
| Source | Publisher | Terms | CC BY 4.0 compatible? |
|---|---|---|---|
| 全国地方公共団体コード, 財務書類指標, 主要財政指標, 公共施設状況調, 地方公営企業年鑑 | 総務省 | PDL1.0 (https://www.soumu.go.jp/menu_kyotsuu/policy/tyosaku.html) | Yes — PDL1.0 §1.7(3) states compatibility with CC BY 4.0 |
| 財政状況資料集 (施設類型別) | 総務省 (files hosted on prefectural / city sites) | 総務省 PDL1.0; host sites have own terms | Yes for 総務省 content; numerical data is not copyrightable (PDL1.0 §1) |
| PFI事業DB, PPP情報リスト, 優先的検討規程, 実施方針一覧 | 内閣府 | PDL1.0 (https://www.cao.go.jp/notice/rule.html) | Yes |
| PREポータル, 官民連携サウンディング (近畿ブロック) | 国土交通省 | PDL1.0 (https://www.mlit.go.jp/link.html) | Yes (MLIT's own content; linked municipal pages are third-party, see below) |
| 国土数値情報 行政区域 N03 (2024) | 国土交通省 | "オープンデータ（CC_BY_4.0）" (https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2024.html); 原典: 国土地理院 数値地図(国土基本情報), 測量法に基づく国土地理院長承認（複製）R 5JHf 357 | Yes. Credit: 「国土数値情報（行政区域データ）（国土交通省）を加工して作成」 |
| 日本の地域別将来推計人口 (R5推計) | 国立社会保障・人口問題研究所 | PDL1.0 unless noted (https://www.ipss.go.jp/site-ad/link/anlink.html) | Yes |
| Municipal web pages (signal titles/URLs/dates) | 各市町村 | Each site's own terms (many PDL1.0 / 政府標準; some "無断転載禁止") | **Not covered** — see below |
| 日本PFI・PPP協会 「国・自治体・企業等からのお知らせ」 | 日本PFI・PPP協会 | Site policy: all rights reserved, no reproduction without consent (https://www.pfikyokai.or.jp/faq/privacy.html) | **No** — see below |

## Not covered by CC BY 4.0 / CC BY 4.0 の対象外
- `data/signals.csv` / `window.PPP_SIGNALS` columns `title` and `url`: titles are quoted from the originating public bodies' pages
  and are provided **for reference/linking only**; their copyright stays with each body. The factual columns (municipality, date, type, facility type, source) are CC BY 4.0.
- Rows with `source = pfikyokai_public_notices`: the Association's site prohibits reproduction without consent. We store only facts
  (municipality, date posted, the municipal page title and the link to the municipal/original page), not the Association's own text.
  Before redistributing, prefer replacing these with the municipal page (date/URL) or obtain the Association's consent.
- `web/echarts.min.js` (Apache-2.0) and code (MIT, see `LICENSE`).
- Logos and symbol marks of any public body (none are included).

No warranty. Data may contain errors; check the original sources.
