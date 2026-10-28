# 技術説明 / Technical notes

関西 PPP/PFI × 公共施設老朽化ダッシュボード（v0 + 任意の v1 / v1+、第3週時点）

**English version: [jump to Technical notes (English)](#technical-notes-english)**

---

## 技術説明（日本語）

無料・オフラインで利用できる静的ダッシュボードです。関西の各市町村について、透明性のある「PPP パイプライン・スコア」（早期シグナル層）を算出します。`web/index.html` を開くだけで使え、インターネット接続は不要です。

### ディレクトリ構成
- `raw/`：官公庁の原データ（未加工）
- `data/municipalities_raw.csv`：団体マスタ（244 団体：関西 6 府県 198 + 三重 29 + 福井 17）
- `data/kansai_municipalities.csv`：統合済みのワイド表。1 団体 1 行で、全指標と各成分スコアを含む
- `data/scores.csv`：総合スコア、データ充足率、順位
- `data/sources_inventory.csv`：データソース一覧（URL、形式、時点、更新頻度、利用条件、ダウンロード済みか否か）
- `data/kansai_muni.geojson`：国土数値情報 N03 の行政区域境界を市町村単位に統合・簡略化したもの
- `scripts/geo.py`：境界データを生成。`scripts/build.py`：データを統合してスコアを算出し、`web/data.js` と `web/geo.js` を生成
- （W2）`scripts/extract_shisetsu.py`：財政状況資料集 xlsx のグラフ内テキストボックスから施設類型別の有形固定資産減価償却率を抽出 → `data/shisetsu_long_raw.csv`。団体全体の減価償却率 → `data/overall_ageing_zaisei.csv`（ログ：`data/shisetsu_extract_log.csv`）
- （W2）`scripts/nenkan.py`、`scripts/water.py`：地方公営企業年鑑の個表を解析 → `data/water_nenkan_r06_raw.csv`、`data/sewer_nenkan_r06_raw.csv`、`data/water_sewer_r06.csv`
- （W2）`scripts/preview.py`：すべてのネットワーク通信を遮断した状態でスクリーンショットを撮影 → `preview.png`（既定表示）、`preview_facility.png`（v1 + 一般廃棄物処理施設の表示）
- `web/index.html`：ダッシュボード本体。ローカルの echarts.min.js 5.6.0（Apache-2.0）を使用
- `preview.png`：ヘッドレスブラウザによるスクリーンショット。撮影時にすべてのネットワーク通信を遮断しており、オフラインで動作することを示す

- （W3）`scripts/polite.py`（読み取り専用の取得処理：robots.txt を遵守、同一ホストへのアクセス間隔は 3 秒以上、ローカルキャッシュ、身元を明示した UA。本環境では 80 番ポートに接続できないため、http のリンクはまず同じアドレスの https を試す）、`scripts/signals_common.py`（分類ルール）、`scripts/signals_collect.py`（構造化されたソース → `raw/signals/candidates_structured.csv`）、`scripts/signals_resolve.py`（ページごとに日付を確認 → `data/signals.csv`、除外した記録 → `raw/signals/dropped.csv`）
- （W3）`data/signals.csv`、`data/signals_seed_urls.csv`（サイト内検索で得た市町村ページ）、`data/snapshots/pre_2026-10-26_*.csv`（PRE ポータルのスナップショット。履歴として保存）
- （W3）`LICENSE`（コード：MIT）、`LICENSE-DATA.md`（データ：CC BY 4.0）

再構築：`python3 scripts/geo.py && python3 scripts/extract_shisetsu.py && python3 scripts/water.py && python3 scripts/signals_collect.py && python3 scripts/signals_resolve.py && python3 scripts/build.py && python3 scripts/preview.py`（signals の 2 ステップはネット接続を使用。キャッシュがあればオフラインで再実行可能）

### データソース（詳細は sources_inventory.csv）
- 総務省
  - 全国地方公共団体コード（R6.1.1）
  - 統一的な基準による財務書類の指標 R6（有形固定資産減価償却率）
  - 主要財政指標 R6（財政力指数）
- 内閣府
  - PFI 事業データベース（R7.3.31）
  - 地方公共団体 PPP 情報リスト R7
  - 優先的検討規程の策定状況（R7.3 末、PDF、手作業で読み取り）
- 国土交通省
  - PRE ポータル（HTML 取得、2026-10-26）
  - 国土数値情報 N03 2024
- 国立社会保障・人口問題研究所（社人研）：R5 日本の地域別将来推計人口
- （W2）総務省 財政状況資料集（令和6年度決算）：施設類型別ストック情報分析表①②（16 類型、R06 当該値・類似団体平均・類似団体内順位）、および公会計指標分析表の団体全体の有形固定資産減価償却率
- （W2）総務省 地方公営企業年鑑 R6（令和6年度決算）：水道事業・公共下水道の個表

### 年度の確認（W2）
- 財務書類指標 R6（`ageing_rate`）＝令和6年度決算。根拠：財政状況資料集 R06 当該値と比較すると、両方にデータがある 213 団体のうち 122 団体が完全一致し、差の中央値は 0。R05 と一致したのは 2 団体のみ。残りは小さな差（大半は ±1 以内。吹田市 59.6 対 66.1 など一部に大きな差があるが、原因は未確認）。
- 財政状況資料集：ファイル名が「令和6年度」で、グラフ横軸の最新年度が R06 → 令和6年度決算。
- 地方公営企業年鑑：ページタイトルが「令和6年度地方公営企業年鑑」 → 令和6年度決算。
- 主要財政指標 R6 の決算年度は未確認（W1 からの持ち越し）。

### スコア算出方法 v0
各成分をまず 0–100 点に換算し、加重平均します。

| 成分 | 重み | 算出方法 |
|---|---|---|
| 老朽化 | 30 | 有形固定資産減価償却率の 244 団体中のパーセンタイル |
| PFI 実績 | 20 | log(1+PFI 総件数) + 2×log(1+2020 年 4 月以降に実施方針を公表した件数)。最大値で正規化 |
| 優先的検討規程 | 15 | R7.3 末時点で策定済みなら 100、未策定なら 0 |
| PPP 体制 | 10 | 次の 3 項目のうち ○ の割合：公共施設等総合管理計画への PPP 方針の記載、民間提案の一元的窓口、事業リストの公表 |
| PRE ポータル | 10 | log(1+現在の掲載件数+直近 12 か月の更新回数)。最大値で正規化 |
| 財政力 | 5 | 財政力指数のパーセンタイル。「実施能力と民間にとっての魅力」として正の向きに算入。「ニーズ」とみなして逆向きにする考え方もあるが、v0 では正の向きを採用 |
| 人口規模 | 10 | log(2020 年人口) のパーセンタイル |

- 欠損値は補完しません。ある成分が欠損している場合はその成分を算入せず、残りの重みを正規化し直し、データ充足率（coverage）を表示します。充足率が 60% 未満の団体はスコアを出しません（現時点で該当団体なし）。
- 「PFI 件数＝0」は、PFI 法に基づく事業データベースにその団体の事業がないという意味であり、他の PPP（指定管理者制度など）がないことを意味しません。
- 参考列（スコアには算入しない）：
  - 2026–2030 年度に PFI 契約が満了する件数（再公募のシグナルとなり得る）
  - 2050 年人口増減率
  - 経常収支比率、将来負担比率

### W2 の追加内容
- ワイド表に追加した列：
  - `fac_<類型>`（R06 値）、`fac_<類型>_ruiji`（類似団体平均）、`fac_<類型>_rank`
    - 類型：road、bridge、housing、port、nursery、school、jidokan、kominkan、library、gym、welfare、hall、waste、health、fire、cityhall
  - `ageing_rate_all`、`ageing_src`、`ageing_rate_zaisei_R05_ref`（参考のみ、スコアには算入しない）
  - `w_pipe_ageing`、`w_dep_rate`、`w_src`、`s_pipe_ageing`、`s_dep_rate`、`s_src`
  - `s_ageing_v1`、`score_v1`、`rank_v1_*`、`worst_facility`、`n_fac_above_ruiji`、`untapped`、`untapped_rank`
- 団体全体の有形固定資産減価償却率：もともと 12 団体が欠損していたため、財政状況資料集 R06 当該値で 4 団体を補完（海南市 65.8、洲本市 67.2、丹波篠山市 50.7、かつらぎ町 68.8）し、236/244 をカバー。残る 8 団体（箕面、名張、八幡、播磨、南あわじ、小浜、福崎、御浜）は R06 値が「-」のため補完しない。v0 は W1 の定義を維持して財務書類指標のみを使用し、v1 は補完後の値を使用。
- 水道管路経年化率・下水道管渠老朽化率：年鑑個表の延長から独自に算出（経営比較分析表と同じ定義）。抜き取り確認では JWWA の R5 版の数値と近い値。
  - 水道：
    - 自団体の上水道 196 団体、簡易水道（法適用）25 団体
    - 企業団全体の値 22 団体：大阪広域 14（構成団体は推定）、淡路広域 3、磯城郡 3、長浜 1、西播磨 1
    - 欠損 1 団体：愛荘町
  - 下水道（公共下水道、法適用）：187 団体
- v1（任意）：
  - 老朽化成分 = 50% 団体全体の減価償却率パーセンタイル + 50%「重点分野の類型別パーセンタイルの平均」。類型平均は 3 類型以上にデータがある場合のみ算出。
  - 対象とする類型は 14 項目：庁舎、学校施設、公営住宅、体育館・プール、一般廃棄物処理施設、図書館、公民館、市民会館、福祉施設、保育所等、道路、橋りょう、水道管路（簡易水道を除く）、下水道管渠。
  - その他の重みは v0 と同じ。v0 と v1 のスピアマン順位相関係数は 0.97。
  - 火葬場・病院は利用可能なデータがないため対象外。
- 「未開拓」（untapped）の判定：以下の条件をすべて満たす団体
  - 2020 年人口 2 万〜20 万で、政令指定都市ではない
  - v1 老朽化成分 ≥ 60（244 団体中の上位 40%）
  - R7.3 末時点で優先的検討規程が未策定
  - PFI 件数 0〜1
  - 現在 33 団体。v1 老朽化成分の順に並べる。
- ダッシュボード：
  - バージョン切替（v0/v1）と、地図・一覧表の色分け指標の選択（団体全体の減価償却率、16 施設類型、水道、下水道）を追加。
  - 施設類型を選ぶと、一覧表にその類型の値・類似団体平均・順位が追加される。
  - 未開拓団体は地図上で赤枠、一覧表で薄い赤の背景色で表示。
  - 未開拓リストを追加。

### W3 の追加：直近 24 か月のシグナル層（2024-10-26 – 2026-10-26）
- 収録する種類（`type`）：
  - `sounding` サウンディング型市場調査の実施、`sounding_result` 結果の公表
  - `jisshi_houshin` 実施方針の公表
  - `fs` 導入可能性調査（FS 委託の公告を含む）
  - `minkan_teian` 民間提案の募集・窓口
  - `procurement` PPP/PFI の入札・公募・優先交渉権者の決定
  - 参考：`shitei_kanri` 指定管理者、`pre_update` PRE ポータルの掲載更新
  - 土地売却・ネーミングライツ・セミナー等は other とし、収録しない
- 分類方法：件名をキーワードルールで判定（`signals_common.classify` 参照）。判定前に NFKC 正規化を行う。
- 日付：ページ上の 更新日 / 公開日 / 掲載日、または一覧上の掲載日を採用（`date_basis` 列）。
  - 日付のないページはすべて除外。
  - 例外：件名に「令和N年度」と明記されているものは年度単位の行（`fy`）として記録し、FY2025・FY2026 のみ収録。
  - 推測や創作による項目は一切ない。
- ソース（詳細は sources_inventory）：
  - 国土交通省 PRE ポータル（スナップショット付き）
  - 国土交通省 官民連携サウンディング支援・登録案件
  - 内閣府 PFI 事業データベース（2025-03 まで）および R7 実施方針一覧
  - 日本PFI・PPP協会が公開する「お知らせ」欄：非会員向けページのみ使用（一部は web.archive.org で遡及）。**発見の手がかりとなる索引としてのみ使用**し、協会が書いた件名・概要は一切保存しない（後述「協会由来の行の扱い」参照）
  - 市町村公式サイトのサイト内検索（未開拓団体と、約 17 の大都市）
  - 大阪府のサウンディング一覧
- 重複除去：同一団体・URL・種類は 1 行のみ残し、同一団体・件名・日付も 1 行のみ残す。ソースの優先順位：市町村公式サイト（サイト内検索・一覧）> 協会の手がかりから見つけた市町村の原ページ > 国土交通省 > 内閣府 > 市町村の文書リンクのみの行 > 事実のみの行。自動ラベルの行は誤った統合を避けるため件名では統合しない。
- v1+（任意。v0 / v1 は変更なし）：
  - 算出方法：種類ごとの重み付き件数を用い、s_signal = log1p(重み付き合計) / 最大値 × 100 とし、重み 10 で v1 に加える。
  - 種類別の重み：
    - 実施方針・入札：3
    - FS・サウンディング・サウンディング結果・民間提案：2
    - 指定管理者・PRE 更新：0.5
  - 確認済み：v0 / v1 のすべての列は git 上の旧版 scores.csv と完全に一致し、列が追加されたのみ。
- ダッシュボードに「直近24ヶ月シグナル」カードを追加：
  - 月別の積み上げ時系列グラフ
  - 一覧（府県・市町村・種類・「未開拓のみ」で絞り込み可能。件名から原典に直接リンク）
  - スコアのバージョンとして v1+ を選択可能
- シグナルの限界：
  - 「0 件」は見つからなかったという意味であり、存在しないことを意味しない。
  - PRE ポータルは任意掲載で、古いリンクの多くは 404。こうした項目は除外した。
  - 協会の欄は自主投稿であり、全件ではない。
  - 内閣府データベースは 2025-03 までで、R7 一覧は年度単位のみ。
  - 兵庫県のプラットフォームの案件一覧は準備中のため未使用。
  - 大阪府の一覧は府自身の案件が中心。
  - サイト内検索は一部の団体のみ対象。
  - 分類は件名のキーワードによるため、procurement の範囲はやや広く、PPP ではない通常の公募型プロポーザルが少数含まれる可能性がある。
- 協会由来の行の扱い（W3 公開前の修正、2026-10-26）：
  - 期間内の協会の手がかり（重複除去前 172 件）ごとに、その団体自身の公式ページを次の順に探す：手がかりの URL 自体が行政ドメイン（`.lg.jp`、`city.` など）であればそのまま使用。そうでなければ協会ページ内の行政ドメインへのリンクを使用（HTML を PDF より優先）。
  - そのページを取得し（リンク切れの場合は web.archive.org にある**市町村の元 URL**のアーカイブを使用）、件名が取得でき、かつページ内に当該団体名が含まれる場合に限り、その件名と URL を採用。
  - 結果（重複除去前）：
    - 市町村の原ページに置換：122 件（現存 109、アーカイブ 13）。`source=municipal_page_via_board`。件名は市町村ページから取得し、`title_basis` に `municipal page live/archived` を記録。種類は市町村の件名で再分類；
    - 市町村の文書（PDF 等）のみ、または原ページがリンク切れ：32 件。`url` は市町村のリンク、件名は当方で生成した中立的なラベル（例：「サウンディング型市場調査（公園・案件名不明）」）。`source=municipal_document_via_board`；
    - 市町村のページが一切見つからない：18 件。団体・日付・種類・施設類型のみ保持し、件名は中立的なラベル、`url` は空、`ref_url` には協会ページへのリンクのみ（その件名や概要は含まない）。`source=pfikyokai_board_fact`。
  - 重複除去後の最終データ：107 + 31 + 18 = 156 行が協会の手がかり由来（ほかに 16 件が市町村のサイト内検索等による既存行と重複して統合）。シグナル総数は 284 → 279。
  - 日付は引き続き協会欄の掲載日（`date_basis=pfikyokai_board_posted_date`）で、事実情報にあたる。
  - 確認：最終的な `data/signals.csv` の件名を協会の元の件名と 1 件ずつ照合したところ、完全一致した 22 件はすべて市町村ページ自体から取得したもの（協会が市町村の件名をそのまま転記していた）で、協会の文章ではない。`web/data.js` で pfikyokai の文字列を含むのは `ref_url` と `date_basis` のみ。
  - 限界：事実のみの行には案件名がないため、サイト内検索で得た同一案件と二重に数えている可能性がある。中立的なラベル内の施設類型は、当方が元の件名のキーワードから判定した分類である。
  - 記録：`raw/signals/municipalize_log.csv`（raw/ はコミットしない）。
- PRE 更新ログの正規表現（修正済み、2026-10-26）：
  - `build.py` 第 7 ステップの元の正規表現 `(\S+?[都道府県])` は「京都府宇治市」を「京都」+「府宇治市」に分割してしまう。現在は `北海道|東京都|京都府|大阪府|..県` を明示的に照合するよう変更。
  - 再実行後の確認：キーは「府県+市町村」を単純に連結したものであるため、旧方式で連結されたキーも同じく「京都府宇治市」となり、京都府内団体の `pre_updates_12m` はもともと正しく集計されていた（宇治市・京都市が各 1 件で修正前と同じ）。0 件ではなかった。以前の「既知の問題」にあった「京都が 0 件と集計される」という判断は誤りであり、訂正する。
  - したがって、v0 / v1 のスコア・順位・上位 10 団体・未開拓リスト（33 団体）は修正前と完全に一致する。「京都府」自体（府レベル）のログ行は、新旧いずれの方式でもどの市町村にも算入されない。
  - v1+ の変化は上記の協会由来行の置換（シグナル 284 → 279）によるもののみ：大阪市・岸和田市・福知山市・泉南市・串本町が各 1 件減、芦屋市は正規化の影響で s_signal がわずかに上昇。v1+ の上位 10 団体は変わらない（大阪市 71.4 → 71.0）。

### ライセンス（W3）
- コード：MIT（`LICENSE`）。`web/echarts.min.js` は引き続き Apache-2.0。
- データ：CC BY 4.0（`LICENSE-DATA.md`）。対象は `data/`、`web/data.js`、`web/geo.js`。
- 原データ：
  - 総務省・内閣府・国土交通省（PRE ポータルを含む）・社人研はいずれも PDL1.0。PDL1.0 は CC BY 4.0 と互換（第 1.7 条）。
  - 国土数値情報 N03 は CC BY 4.0。原典は国土地理院で、測量法に基づく承認を取得（R 5JHf 357）。
- CC BY の許諾対象外：
  - 協会欄の内容。協会サイトは同意のない複製・転載を禁じているため、データには協会が書いた件名や概要を含まない。見つかったものは市町村の原ページに置き換え、見つからなかったものは事実と自動生成ラベルのみを残し、協会ページは参照リンク（`ref_url`）としてのみ使用。
  - 各シグナルの件名とリンク。権利は各団体に帰属。

### 限界
1. スコアは大都市に有利な傾向がある。人口・PFI 実績・優先的検討規程はいずれも規模と強く相関する。人口成分を除いても上位 10 団体はほぼ変わらない。v0 は「発注の可能性がある団体」の一次スクリーニングに適しており、ビジネス機会のランキングとして扱うべきではない。
2. 団体全体の減価償却率はまだ 8 団体が欠損。施設類型別データは滋賀県の 19 団体（県が公表する xlsx に施設類型の表がなく、概要版 PDF にもない）と箕面市が欠損しているため、滋賀県内団体の v1 は実質的に団体全体の値・水道・下水道のみを使用（例：日野町は類型別データが 2 項目のみ）。火葬場・病院はデータなし。
   - 公営企業に関する限界：
     - 企業団の値は企業団全体の数値であり、個別団体の値ではない。
     - 大阪広域水道企業団の構成団体は「自団体の事業がない」ことから推定したもの。
     - 簡易水道や小規模事業は数値の変動が大きく、一部に 0 や 99.9 があるが、そのまま残している。
     - 下水道は公共下水道（法適用）のみを集計。特定環境保全公共下水道・農業集落排水のみの町村や、流域下水道は未収録。
     - 下水道の減価償却率は法適用の時期に左右される（法適用に移行したばかりの団体は低めに出る）ため、表示のみでスコアには算入しない。
3. PRE ポータルは団体の任意掲載であり、網羅的ではない。情報一覧は更新ログにすぎず、正確な公表日は得られない。明石市だけで 43 件を掲載しており、スコアを押し上げている。
4. 優先的検討規程は PDF の地図と一覧から手作業で転記したため、読み漏れの可能性がある。転記結果は PPP 情報リストの R6.3 欄の 40 団体と矛盾せず、R7.3 は 42 団体。
5. 各データソースの時点が揃っていない（2024–2026）。財務書類指標と財政指標が対応する決算年度は、さらに個別の確認が必要。
6. 重みは主観的に設定したもので、実際の入札結果による検証は行っていない。

### 第 2–6 週の計画
- W2（完了：施設類型、上下水道、v1、未開拓）
  - 未着手：PRE ポータルの定期取得と履歴スナップショット
  - 未着手：滋賀県内各市町の公式サイトからの財政状況資料集の補完取得
- W3（完了：直近 24 か月のシグナル層、v1+、ライセンスファイル。PRE スナップショットの保存を開始）
- W4
  - 2015–2024 年の PFI データベースでバックテスト：v0 スコアがその後 2 年間の実施方針公表を予測できるかを検証し、重みを調整
- W5
  - 団体詳細ページ（時系列、契約満了、原典リンク）
  - 英語版
- W6
  - 公開前にライセンスと出典表示を確認し、GitHub Pages で公開

### 公開と更新（GitHub Pages）
- 公開 URL：https://stesea1.github.io/kansai-ppp-dashboard/ （main ブランチのルートから GitHub Pages で配信）
- ルートの `index.html` は `web/` へ転送するだけのページで、看板本体は `web/index.html` です。
- データを更新するときは、上記の再構築コマンドで `web/data.js` と `web/geo.js` を作り直し、main に push すれば数分で公開サイトに反映されます。
- `raw/` の原データファイルはリポジトリに含めていません。取得元の URL は `data/sources_inventory.csv` に、取得手順は `scripts/` にあります。

---

<a id="technical-notes-english"></a>

## Technical notes (English)

Kansai PPP/PFI × Public-Facility Ageing Dashboard (v0 + optional v1 / v1+, as of week 3)

A free static dashboard that works offline. It calculates a transparent "PPP pipeline score" (an early-signal layer) for every municipality in Kansai. Just open `web/index.html`; no internet connection is needed.

### Directory layout
- `raw/`: original official files (unmodified)
- `data/municipalities_raw.csv`: master list of local governments (244: 198 in the six Kansai prefectures + 29 in Mie + 17 in Fukui)
- `data/kansai_municipalities.csv`: merged wide table, one row per municipality, with every indicator and component score
- `data/scores.csv`: total score, data coverage and rank
- `data/sources_inventory.csv`: source inventory (URL, format, reference date, update frequency, licence, whether downloaded)
- `data/kansai_muni.geojson`: N03 administrative boundaries, dissolved by municipality and simplified
- `scripts/geo.py`: builds the boundaries; `scripts/build.py`: merges the data, computes the scores, and writes `web/data.js` and `web/geo.js`
- (W2) `scripts/extract_shisetsu.py`: extracts facility-type depreciation rates (有形固定資産減価償却率) from the chart text boxes in the 財政状況資料集 xlsx files → `data/shisetsu_long_raw.csv`; and the municipality-wide depreciation rate → `data/overall_ageing_zaisei.csv` (log: `data/shisetsu_extract_log.csv`)
- (W2) `scripts/nenkan.py`, `scripts/water.py`: parse the individual tables of the Local Public Enterprise Yearbook (地方公営企業年鑑) → `data/water_nenkan_r06_raw.csv`, `data/sewer_nenkan_r06_raw.csv`, `data/water_sewer_r06.csv`
- (W2) `scripts/preview.py`: takes screenshots with all network requests blocked → `preview.png` (default view), `preview_facility.png` (v1 + general waste-treatment facility view)
- `web/index.html`: the dashboard, using a local echarts.min.js 5.6.0 (Apache-2.0)
- `preview.png`: headless-browser screenshot taken with all network requests blocked, demonstrating that it works offline

- (W3) `scripts/polite.py` (read-only fetching: respects robots.txt, ≥3 seconds between requests to the same host, local cache, a UA that identifies itself; port 80 is unreachable in this environment, so http links are first tried as https at the same address), `scripts/signals_common.py` (classification rules), `scripts/signals_collect.py` (structured sources → `raw/signals/candidates_structured.csv`), `scripts/signals_resolve.py` (confirms the date page by page → `data/signals.csv`; dropped records → `raw/signals/dropped.csv`)
- (W3) `data/signals.csv`, `data/signals_seed_urls.csv` (municipal pages found via site search), `data/snapshots/pre_2026-10-26_*.csv` (PRE portal snapshot, kept as history)
- (W3) `LICENSE` (code: MIT), `LICENSE-DATA.md` (data: CC BY 4.0)

Rebuild: `python3 scripts/geo.py && python3 scripts/extract_shisetsu.py && python3 scripts/water.py && python3 scripts/signals_collect.py && python3 scripts/signals_resolve.py && python3 scripts/build.py && python3 scripts/preview.py` (the two signals steps go online; with a cache they can be re-run offline)

### Data sources (see sources_inventory.csv for details)
- Ministry of Internal Affairs and Communications (MIC, 総務省)
  - Local government codes (R6.1.1)
  - Unified-standard financial statement indicators R6 (有形固定資産減価償却率, depreciation rate of tangible fixed assets)
  - Key fiscal indicators R6 (財政力指数, fiscal capacity index)
- Cabinet Office (内閣府)
  - PFI project database (R7.3.31)
  - Local government PPP information list R7
  - Status of priority-review rules (優先的検討規程) (end of R7.3, PDF, read manually)
- Ministry of Land, Infrastructure, Transport and Tourism (MLIT, 国土交通省)
  - PRE portal (HTML scrape, 2026-10-26)
  - National Land Numerical Information N03 2024
- National Institute of Population and Social Security Research (IPSS, 社人研): R5 regional population projections
- (W2) MIC 財政状況資料集 (FY2024 / 令和6年度 settled accounts): facility-type stock information analysis tables ① and ② (16 types; R06 value, similar-municipality average, rank within similar municipalities), plus the municipality-wide depreciation rate from the public-accounting indicator analysis table
- (W2) MIC 地方公営企業年鑑 R6 (FY2024 settled accounts): individual tables for water supply and public sewerage

### Fiscal-year verification (W2)
- Financial statement indicators R6 (`ageing_rate`) = FY2024 (令和6年度) settled accounts. Evidence: compared with the 財政状況資料集 R06 values, 122 of the 213 municipalities present in both match exactly, with a median difference of 0; only 2 match R05. The rest differ slightly (mostly within ±1; a few differ more, e.g. Suita 59.6 vs 66.1, cause not yet investigated).
- 財政状況資料集: the file title says "令和6年度" and the latest year on the chart axis is R06 → FY2024 settled accounts.
- Local Public Enterprise Yearbook: the page title is "令和6年度地方公営企業年鑑" → FY2024 settled accounts.
- The settlement year of key fiscal indicators R6 is still to be verified (carried over from W1).

### Scoring method v0
Each component is first converted to a 0–100 score, then a weighted average is taken:

| Component | Weight | Method |
|---|---|---|
| Ageing | 30 | Percentile of the depreciation rate of tangible fixed assets among the 244 municipalities |
| PFI track record | 20 | log(1+total PFI projects) + 2×log(1+projects whose implementation policy was published since April 2020), normalised by the maximum |
| Priority-review rule | 15 | 100 if adopted by end of R7.3, otherwise 0 |
| PPP organisation | 10 | Share of these 3 items marked ○: PPP policy stated in the comprehensive facility management plan, a single contact point for private proposals, a published project list |
| PRE portal | 10 | log(1+current listings+updates in the last 12 months), normalised by the maximum |
| Fiscal capacity | 5 | Percentile of the fiscal capacity index. Counted as positive ("capacity to deliver and attractiveness to the private sector"); it could also be read as "need" and inverted, but v0 uses the positive direction |
| Population size | 10 | Percentile of log(2020 population) |

- Missing values are not imputed. If a component is missing it is left out, the remaining weights are re-normalised, and data coverage is shown. No score is given when coverage is below 60% (currently no municipality falls below this line).
- "PFI projects = 0" means the PFI Act database has no project for that municipality; it does not mean there is no other PPP (e.g. designated management / 指定管理).
- Additional reference columns (not scored):
  - Number of PFI contracts ending in FY2026–2030 (a possible re-tender signal)
  - Population change rate to 2050
  - Ordinary balance ratio (経常収支比率), future burden ratio (将来負担比率)

### Added in W2
- New columns in the wide table:
  - `fac_<type>` (R06 value), `fac_<type>_ruiji` (similar-municipality average), `fac_<type>_rank`
    - Types: road, bridge, housing, port, nursery, school, jidokan, kominkan, library, gym, welfare, hall, waste, health, fire, cityhall
  - `ageing_rate_all`, `ageing_src`, `ageing_rate_zaisei_R05_ref` (reference only, not scored)
  - `w_pipe_ageing`, `w_dep_rate`, `w_src`, `s_pipe_ageing`, `s_dep_rate`, `s_src`
  - `s_ageing_v1`, `score_v1`, `rank_v1_*`, `worst_facility`, `n_fac_above_ruiji`, `untapped`, `untapped_rank`
- Municipality-wide depreciation rate: 12 municipalities were originally missing; 4 were filled with the 財政状況資料集 R06 values (Kainan 65.8, Sumoto 67.2, Tamba-Sasayama 50.7, Katsuragi 68.8), giving 236/244 coverage. The other 8 (Minoh, Nabari, Yawata, Harima, Minamiawaji, Obama, Fukusaki, Mihama) have "-" as their R06 value and are not filled. v0 keeps the W1 definition and uses only the financial statement indicators; v1 uses the filled values.
- Water-pipe ageing rate (水道管路経年化率) and sewer-pipe ageing rate (下水道管渠老朽化率): calculated from the pipe lengths in the Yearbook's individual tables, using the same definition as the management comparison analysis tables (経営比較分析表). Spot checks are close to JWWA's R5 figures.
  - Water supply:
    - Own water-supply utilities: 196; small-scale water supply (Local Public Enterprise Act applied): 25
    - Whole-authority values for water-supply authorities (企業団): 22 — Osaka Wide-Area 14 (member municipalities inferred), Awaji Wide-Area 3, Shiki-gun 3, Nagahama 1, Nishi-Harima 1
    - Missing: 1 (Aisho)
  - Sewerage (public sewerage, Act applied): 187
- v1 (optional):
  - Ageing component = 50% percentile of the overall depreciation rate + 50% "average of the percentiles of priority facility types". The type average is calculated only when at least 3 types have data.
  - 14 types are included: city hall, schools, public housing, gyms and pools, general waste treatment, libraries, community centres (公民館), civic halls, welfare facilities, nurseries etc., roads, bridges, water pipes (excluding small-scale water supply), sewer pipes.
  - Other weights are the same as v0. The Spearman correlation between v0 and v1 is 0.97.
  - Crematoria and hospitals have no usable data and are not included.
- "Untapped" flag — all of the following must hold:
  - 2020 population 20,000–200,000 and not a designated city (政令指定都市)
  - v1 ageing component ≥ 60 (top 40% of the 244)
  - No priority-review rule adopted by end of R7.3
  - 0–1 PFI projects
  - Currently 33 municipalities, sorted by the v1 ageing component.
- Dashboard:
  - Added a version switch (v0/v1) and a choice of colouring indicator for the map/table: overall depreciation rate, 16 facility types, water supply, sewerage.
  - When a facility type is selected, the table adds that type's value, similar-municipality average and rank.
  - Untapped municipalities get a red outline on the map and a light-red background in the table.
  - Added the untapped list.

### Added in W3: signals layer for the last 24 months (2024-10-26 – 2026-10-26)
- Types collected (`type`):
  - `sounding` sounding-type market research (サウンディング型市場調査) held, `sounding_result` results published
  - `jisshi_houshin` implementation policy published
  - `fs` feasibility study (including calls for commissioned FS)
  - `minkan_teian` call for or contact point for private proposals
  - `procurement` PPP/PFI tenders, public calls, selection of preferred negotiator
  - Reference types: `shitei_kanri` designated management, `pre_update` PRE portal listing update
  - Land sales, naming rights, seminars etc. are classed as other and not collected
- Classification: keyword rules on the title (see `signals_common.classify`), after NFKC normalisation.
- Dates: the 更新日 / 公開日 / 掲載日 on the page, or the posting date in a list (`date_basis` column).
  - Pages with no date are always dropped.
  - Exception: titles that state "令和N年度" are recorded as fiscal-year rows (`fy`); only FY2025 and FY2026 are kept.
  - No entry is guessed or invented.
- Sources (see sources_inventory for details):
  - MLIT PRE portal (with snapshot)
  - MLIT public–private sounding support / registered projects
  - Cabinet Office PFI project DB (to 2025-03) and the R7 implementation-policy list
  - The public "お知らせ" notices of the Japan PFI/PPP Association (日本PFI・PPP協会): non-member pages only (some retrieved via web.archive.org), **used only as a discovery index**; no title or summary written by the Association is stored (see "Handling of Association-sourced rows" below)
  - Site search on municipal websites (untapped municipalities plus about 17 large cities)
  - Osaka Prefecture's sounding list
- De-duplication: one row per municipality + URL + type, and one row per municipality + title + date. Source priority: municipal website (site search / lists) > municipal original page found via an Association lead > MLIT > Cabinet Office > rows with only a municipal document link > fact-only rows. Rows with auto-generated labels are not merged by title, to avoid false merges.
- v1+ (optional; v0 / v1 unchanged):
  - Method: type-weighted count, s_signal = log1p(weighted sum) / maximum × 100, then added to v1 with weight 10.
  - Type weights:
    - Implementation policy, procurement: 3
    - FS, sounding, sounding result, private proposal: 2
    - Designated management, PRE update: 0.5
  - Verified: every v0 / v1 column matches the previous scores.csv in git exactly; only columns were added.
- New "直近24ヶ月シグナル" (recent 24-month signals) card on the dashboard:
  - Monthly stacked timeline
  - List, filterable by prefecture, municipality, type and "untapped only", with titles linking directly to the source
  - v1+ selectable as the score version
- Limitations of the signals:
  - "0" means none found, not none existing.
  - The PRE portal is voluntary and many old links return 404; such entries were dropped.
  - The Association's notices are self-submitted and not exhaustive.
  - The Cabinet Office DB only goes to 2025-03, and the R7 list only gives fiscal years.
  - Hyogo Prefecture's platform project list is still being prepared and was not used.
  - The Osaka Prefecture list mainly covers the prefecture's own projects.
  - Site search covered only some municipalities.
  - Classification relies on title keywords; the procurement class is fairly broad and may include a few ordinary (non-PPP) proposal-type calls.
- Handling of Association-sourced rows (pre-publication fix in W3, 2026-10-26):
  - For each Association lead in the period (172 before de-duplication), look for the municipality's own official page in this order: if the lead URL itself is on a government domain (`.lg.jp`, `city.` etc.), use it; otherwise take a link to a government domain from the Association page (HTML preferred over PDF).
  - Fetch that page (if dead, use the web.archive.org capture of the **municipal original URL**); its title and URL are adopted only if a usable title exists and the municipality's name appears on the page.
  - Results (before de-duplication):
    - Replaced with the municipal original page: 122 (109 live, 13 archived), `source=municipal_page_via_board`; title from the municipal page, `title_basis` recorded as `municipal page live/archived`, type re-classified from the municipal title;
    - Only a municipal document (PDF etc.) or the original page is dead: 32, `url` is the municipal link, title is a neutral label we generate (e.g. 「サウンディング型市場調査（公園・案件名不明）」), `source=municipal_document_via_board`;
    - No municipal page found at all: 18, keeping only municipality, date, type and facility type; the title is a neutral label, `url` is empty, and `ref_url` holds only the link to the Association page (not its title or summary), `source=pfikyokai_board_fact`.
  - Final data after de-duplication: 107 + 31 + 18 = 156 rows come from Association leads (another 16 duplicated existing rows from municipal site search etc. and were merged). Total signals 284 → 279.
  - Dates remain the Association notice posting date (`date_basis=pfikyokai_board_posted_date`), which is factual information.
  - Check: comparing every title in the final `data/signals.csv` with the Association's original titles, the 22 exact matches all come from the municipal pages themselves (the Association copied the municipal titles verbatim), not from Association text; in `web/data.js` only `ref_url` and `date_basis` contain the string pfikyokai.
  - Limitations: fact-only rows have no project name and may double-count a project also found via site search; the facility type in neutral labels is our own classification from keywords in the original title.
  - Log: `raw/signals/municipalize_log.csv` (raw/ is not committed).
- PRE update-log regex (fixed, 2026-10-26):
  - The original regex in step 7 of `build.py`, `(\S+?[都道府県])`, splits "京都府宇治市" into "京都" + "府宇治市". It now matches `北海道|東京都|京都府|大阪府|..県` explicitly.
  - Verified after re-running: because the key is a plain concatenation of prefecture + municipality, the old method produced the same key "京都府宇治市", so `pre_updates_12m` for Kyoto Prefecture municipalities was already counted correctly (Uji and Kyoto City 1 each, same as before the fix), not 0. The earlier "known issue" stating "Kyoto counted as 0" was wrong and is hereby corrected.
  - Therefore the v0 / v1 scores, ranks, top 10 and untapped list (33) are exactly the same as before the fix. Only log rows for "京都府" itself (prefecture level) are not counted towards any municipality, under either the old or the new pattern.
  - Changes in v1+ come only from the Association-row replacement above (signals 284 → 279): Osaka City, Kishiwada, Fukuchiyama, Sennan and Kushimoto each lose 1; Ashiya's s_signal rises slightly due to normalisation; the v1+ top 10 is unchanged (Osaka City 71.4 → 71.0).

### Licences (W3)
- Code: MIT (`LICENSE`). `web/echarts.min.js` remains Apache-2.0.
- Data: CC BY 4.0 (`LICENSE-DATA.md`), covering `data/`, `web/data.js`, `web/geo.js`.
- Original data:
  - MIC, Cabinet Office, MLIT (including the PRE portal) and IPSS are all PDL1.0. PDL1.0 is compatible with CC BY 4.0 (Article 1.7).
  - National Land Numerical Information N03 is CC BY 4.0; the original source is the Geospatial Information Authority of Japan, with approval obtained under the Survey Act (R 5JHf 357).
- Not covered by the CC BY grant:
  - Content of the Association's notices. The Association's site prohibits copying or reproduction without consent, so the data contains no title or summary written by the Association: where possible these were replaced with the municipal original page; otherwise only facts and self-generated labels are kept, and the Association page is used only as a reference link (`ref_url`).
  - The titles and links of individual signals; rights belong to each municipality.

### Limitations
1. The score leans towards large cities. Population, PFI track record and priority-review rules are all strongly correlated with size. Removing the population component leaves the top 10 almost unchanged. v0 is suitable as a first screen for "likely to procure", not as a ranking of business opportunities.
2. The overall depreciation rate is still missing for 8 municipalities. Facility-type data is missing for 19 municipalities in Shiga (the prefecture's published xlsx has no facility-type tables, and neither does the summary PDF) and for Minoh, so v1 for Shiga municipalities effectively uses only the overall value, water supply and sewerage (e.g. Hino has only 2 types of data). No data for crematoria and hospitals.
   - Limitations on public enterprises:
     - Values for water-supply authorities (企業団) are for the whole authority, not for individual municipalities.
     - The member municipalities of the Osaka Wide-Area Water Supply Authority are inferred from "the municipality has no water utility of its own".
     - Small-scale water supply and small utilities vary a lot; some show 0 or 99.9, which are kept as-is.
     - Sewerage counts only public sewerage (Act applied); towns and villages with only specific environmental conservation sewerage (特環) or rural community sewerage (農集排), and regional sewerage (流域下水道), are not yet included.
     - The sewer depreciation rate depends on when the Act was applied (recently converted municipalities show low values), so it is shown but not scored.
3. The PRE portal relies on voluntary listings and is incomplete. Its information list is only an update log, so exact publication dates cannot be obtained; Akashi alone lists 43 items, which raises its score.
4. Priority-review rules were transcribed by hand from PDF maps and lists and may contain omissions. The transcription is consistent with the 40 municipalities in the R6.3 column of the PPP information list; R7.3 has 42.
5. Reference dates differ across sources (2024–2026). The settlement years behind the financial statement and fiscal indicators still need to be checked one by one.
6. Weights are set by judgement and have not been validated against actual tender outcomes.

### Plan for weeks 2–6
- W2 (done: facility types, water and sewerage, v1, untapped)
  - Not yet done: regular PRE portal scraping and historical snapshots
  - Not yet done: fetching 財政状況資料集 from each Shiga municipality's website to fill gaps
- W3 (done: 24-month signals layer, v1+, licence files; PRE snapshots now being saved)
- W4
  - Back-test with the 2015–2024 PFI DB: does the v0 score predict implementation-policy announcements in the following 2 years? Adjust weights accordingly
- W5
  - Municipality detail page (timeline, contract expiries, source links)
  - English version
- W6
  - Check licences and attributions before release, publish on GitHub Pages

### Publishing and updates (GitHub Pages)
- Live site: https://stesea1.github.io/kansai-ppp-dashboard/ (served by GitHub Pages from the root of the main branch)
- The root `index.html` only redirects to `web/`; the dashboard itself is `web/index.html`.
- To update the data, run the rebuild command above to regenerate `web/data.js` and `web/geo.js`, then push to main; the live site updates within a few minutes.
- The original files under `raw/` are not committed. Their source URLs are listed in `data/sources_inventory.csv`, and the download steps are in `scripts/`.
