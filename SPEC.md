# komenasne 今風化 — 要件定義 (SPEC)

nasne の再生に連動してニコニコ実況の過去ログを取得し、コメントビューア（komeview）を起動する Windows 向けツール。
2021年頃の構成（Python + PyInstaller / commenomi 連携 / Twitter 投稿）を現代化する。

- リポジトリ: https://github.com/nyumen/komenasne
- **ベースブランチ: `v3.0.0`**（main より新しい未リリースのWIP。後述の壊れた import を含む）
- 言語: **Python のまま**（保守者が読み書きできることを最優先。Electron 化はしない）
- 将来構想: 機能を [komeview](https://github.com/nyumen/komeview) 本体へ統合する（案A）。本 SPEC はその前段の単体リニューアル（案B）。

---

## 1. 現状の構成（v3.0.0 ブランチ・把握済み）

```
komenasne.ini            設定（nasne IP / commenomi パス / ログ保存先 / Twitter キー）
src/komenasne.py         本体 約650行
  - nasne API (http://<ip>:64210/status/dtcpipClientListGet) で視聴状態を取得
  - 録画視聴中 → 番組情報取得 → 過去ログAPI (jikkyo.tsukumijima.net) から XML 取得
    → vpos を番組開始基準に書き換え → commenomi を起動
  - ライブ視聴中 → jkcommentviewer をニコ生実況URLで起動
  - 直接取得モード / --fixrec / --fixlive / --mode_silent / --mode_monitoring
  - --recerror: nasne の recNgListGet から録画失敗リストを取得しXMLファイル名形式で表示（v3.0.0新機能）
  - Twitter 投稿（tweepy）
src/common/channel_list.py  地域別 service_id → jk** 変換テーブル（ChannelList クラス / v3.0.0で分離）
src/my_channel_list.py      上記と同一内容の重複ファイル（削除候補）
src/channellist.py          IPハードコードのデバッグ用ワンオフ（削除候補）
src/nx_kako_log.py       NX-Jikkyo 過去ログ取得（現状 import はコメントアウト）
src/get_twitter_key.py   Twitter OAuth 認証フロー
```

### 1.1 v3.0.0 の補足
- `common/channel_list.py` の commit 漏れがあったが解消済み（import は正常）。
  `src/my_channel_list.py` は同一内容の重複のため削除する（§2.8）。
- コメント流量制限（limit）は v3.0.0 で**ほぼ削除済み**。残骸の `-limit` argparse 定義のみ撤去する（§2.3）。
- beautifulsoup4 は v3.0.0 で削除済み。

---

## 2. 変更する項目

### 2.1 起動先を commenomi → komeview に変更
- ini キーを `[PLAYER] komeview_path` に変更。**旧キー `commenomi_path` も互換として読む**（komeview_path 優先）。
- **デタッチ起動**: `subprocess.Popen` に以下の creationflags を付け、DOSプロンプトを閉じても komeview が終了しないようにする:
  ```python
  DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB
  ```
  （`CREATE_BREAKAWAY_FROM_JOB` が権限エラーになる環境ではこのフラグだけ外してリトライ）
- README のショートカット説明も komeview の操作（Space / k,o,a,b,c,e / j / ホイール等）に書き換える。

### 2.2 Twitter 投稿 → Bluesky 投稿
- **tweepy・`get_twitter_key.py`・ini の `[TWITTER]` セクションを削除。**
- 公式 SDK **`atproto`** を使用。認証は ini に以下を書くだけ:
  ```ini
  [BLUESKY]
  handle = example.bsky.social
  app_password = xxxx-xxxx-xxxx-xxxx   ; Bluesky の設定画面で発行するアプリパスワード
  ```
- 未設定なら投稿しない（現行の Twitter と同じ「任意機能」の扱い）。
- 投稿内容は現行テンプレートを踏襲。ファイル名は `post_template.txt` に変更
  （プレースホルダ `{title} {ch_name} {total_minutes} {line_count} {min_count}` と strftime 書式は現行互換）。
- ハッシュタグはそのまま `#ニコニコ実況 #komenasne`（Bluesky でもハッシュタグは機能する）。

### 2.3 コメント流量制限（limit）機能の削除
komeview 側の「コメント最大表示数」が上位互換のため削除する。
- 本体は v3.0.0 で削除済み。**残骸の `-limit` argparse 定義を撤去**し、README からも記述を消す。

### 2.4 nasne の自動発見（SSDP）
IP 変更のたびに ini を編集させない。
- **SSDP（UPnP M-SEARCH）**で LAN 内の nasne を発見する。標準ライブラリ `socket` のみで実装（依存追加なし）:
  1. `239.255.255.250:1900` へ M-SEARCH（ST: **`urn:schemas-sony-com:service:X_Telepathy:1`**＝nasne固有サービス、待ち 2〜3秒）
     ※ MediaServer:1 だと**バッファロー製 nasne が応答しない**（スタンバイ中はDLNA機能が寝る）ため使わない。
       SONY製3台＋バッファロー製2台の計5台で実機検証済み。
  2. 応答した各IPへ nasne API（`:64210/status/boxNameGet`）を**並列**で叩き、応答したものだけを nasne と確定
     （本体名もここから取得。デバイス記述XMLはスタンバイ中に取得できないことがあるため使わない）
- **実行タイミング（毎回はやらない）**:
  - 通常起動時は ini の `ip =` をそのまま使う
  - **初回起動時（ini の ip が未設定）だけ自動探索**し、**結果を ini の `ip =` に書き込む**
    （configparser は使わず行単位置換で書き換え、**コメント行は保持**する）
  - **`--discover` オプション**で明示的に再探索して ini を更新（IPが変わった時にユーザーが実行）
- キャッシュファイルは持たない。設定の実体は常に ini の1箇所（ユーザーからも見える）。手動編集も従来どおり可能。
- Windows ファイアウォールが初回に許可を求める場合がある旨を README に記載。

### 2.5 nasne API の並列呼び出し
- 現状は IP を順番に照会し、`requests.get` に**タイムアウト未設定**（オフラインの nasne があると長時間ブロック）。
- `concurrent.futures.ThreadPoolExecutor` で**全 nasne に同時照会**し、**timeout=2秒**を設定。台数によらず最悪約2秒で確定させる。
- 過去ログAPI等その他の HTTP 呼び出しにも適切な timeout を付与する。

### 2.6 GitHub Actions によるビルド・リリース
komeview と同じタグ駆動のリリースフローにする。
- `v*` タグの push → PyInstaller ビルド → Release に添付
- **Windows**（`windows-latest`）: **onedir（フォルダ形式）+ zip**（`komenasne-win.zip`）。単一 exe より Windows Defender の誤検知率が下がるため。
- **macOS**（`macos-latest` / arm64）: onedir + zip（`komenasne-mac.zip`）。
  nasne API は LAN 照会のため、**PC TV Plus / PS5(torne) で再生中の番組を Mac 側の komenasne が検出して Mac の komeview と連動できる**（実機検証済み）。
- リポジトリに直接コミットされている `komenasne.exe` / `komenasne.zip` は削除し、配布は Releases に一本化。
- リリースノートに Defender 誤検知時の対処を自動記載（komeview の release.yml と同様の body 指定）。

### 2.7 依存・ツールチェーンの整理
- **Python 3.12 前提**に更新。
- `pyproject.toml` 化（requirements.txt 廃止）。
- 依存の整理:
  | 依存 | 処置 |
  |---|---|
  | tweepy | 削除（→ atproto を追加） |
  | configparser (pip) | 削除（標準ライブラリで足りる） |
  | pytz | 削除（標準の `zoneinfo` に置換） |
  | requests / python-dateutil | 維持 |
- リンタ/フォーマッタとして ruff を導入（任意）。

### 2.8 リポジトリの整理
- `src/my_channel_list.py`（`common/channel_list.py` と同一内容の重複）を削除。
- `src/channellist.py`（IPハードコードのデバッグ用ワンオフ）を削除。
- `src/get_twitter_key.py` を削除（Bluesky 化に伴い不要）。
- ルート直コミットの `komenasne.exe` / `komenasne.zip` を削除（配布は Releases へ / §2.6）。

### 2.9 録画済みリストの書き出し（新機能）
- `--reclist [絞り込みキーワード]` で、全 nasne の録画済み一覧を `reclist.txt`（exeと同じ場所）に書き出す。
- 各行は `--recerror` と同じ、**再生時に生成されるXMLファイル名と同一の形式**
  （`チャンネル名_YYYYMMDD_HHMMSS_分数_タイトル.xml`）。既取得のXMLとの突き合わせに使える。
- 全 nasne へ並列取得・重複除去・録画日時順ソート。
- 実装に伴い、`jk_names` に欠けていた jk10/jk11/jk12（テレ玉/tvk/チバテレ）を補完
  （欠けていると該当局の録画で通常再生フローもクラッシュする潜在バグだった）。

### 2.10 録画失敗（途中終了）した番組の抑止
ディスク容量不足等で録画が途中終了した番組（例: 30分番組が27分で終了）を再生した場合の動作。

- **判定**: nasne の `recNgListGet`（録画失敗リスト）と突き合わせる。
  実録画時間が予約と異なるためファイル名（分数入り）では一致せず、
  **タイトル完全一致（replace_title 正規化後）＋開始時刻±1分**で照合する。
  問い合わせは**再生中の録画を持つ nasne の1台のみ**（余分なリクエストを出さない）。
  リストが取得できない場合は失敗扱いにしない（従来動作）。
- **Bluesky投稿**: 録画失敗番組は**どのモードでも投稿しない**（中途半端な視聴情報を残さない）。
- **XML保存**:
  - **ポーリング時**（`--mode_silent` / `--mode_monitoring`）: **保存しない**（取得ごとスキップしログのみ）。
  - 通常起動（Win+1）・`--serve` キック: **保存する**（コメント再生に必要なため）。投稿だけ抑止。

---

## 3. 変更しない項目（現状維持）

- **jkcommentviewer 連動**（ライブ視聴時）: そのまま維持。
- 直接取得モード（channel + 日時 + 分数）、`--fixrec` / `--fixlive` / `--mode_silent` / `--mode_monitoring`。
- **`--recerror`（録画失敗リスト表示 / v3.0.0新機能）**: そのまま維持。
- 過去ログAPI（jikkyo.tsukumijima.net）からの取得と vpos 書き換えロジック。
- 地域別チャンネル変換テーブル。
- 取得 XML のファイル名規約（`チャンネル名_YYYYMMDD_HHMMSS_分数_タイトル.xml`）と `kakolog/` 保存。
- 「番組終了5分以内は取得しない」制約（過去ログAPI側の仕様）。

---

## 4. 検討事項

- **Nuitka への乗り換え**: 現状は PyInstaller（onedir+zip）。Nuitka は Python を C にコンパイルするため
  逆解析耐性と若干の実行速度向上があるが、komenasne はネットワーク待ちが支配的なため恩恵が薄く、
  CI ビルド時間が大幅に伸びる（Cコンパイル）・atproto(pydantic) の互換性検証が必要というコストがある。
  **Windows Defender の誤検知が実際に多発した場合に、コード署名と合わせて再検討する**（誤検知は Nuitka でも起きるため確実な解決策ではない）。

---

## 5. フェーズ2: Webプレイヤー / `--serve` モード

外出先で iPad の torne アプリで nasne の動画を再生しながら、**Split View のブラウザで実況コメントを再生する**ための機能。
自宅PCの komenasne がコメント配信サーバになり、iPad のブラウザがプレイヤー（komeview-lite）になる。

```
[自宅PC] komenasne --serve
   ├ GET /            … Webプレイヤー（komeview-lite）を配信
   └ GET /api/play    … アクセス時キック: nasneの再生を検出→過去ログ取得→XMLを返す
        ↑ Tailscale 経由（iPad にも Tailscale アプリ）
[iPad] torne で動画再生 ＋ Split View のブラウザでコメント再生（手動同期）
```

### 5.1 サーバ（`--serve [port]`）
- Python 標準ライブラリの `http.server`（ThreadingHTTPServer）で実装。**新規依存なし**。
- デフォルトポート 8765。`0.0.0.0` にバインド（LAN / Tailscale から到達可能）。
- エンドポイント:
  - `GET /` … プレイヤーページ（`web/` 配下の静的ファイル）
  - `GET /api/play` … **キックAPI**。既存の `playing_nasnes` 相当を1回実行し、
    再生中の録画があれば過去ログを取得（既存XMLがあれば再利用）して
    `{ title, filename, xml }` を JSON で返す。再生なし/取得失敗はエラー内容を返す。
- 認証は持たない。**Tailscale の閉域網に依存**する（LAN外に生で公開しない前提を README に明記）。
- 将来: ドメイン取得後に Cloudflare Tunnel + Access（無料・メール認証）での常設公開を検討（§5.3）。

### 5.2 Webプレイヤー（komeview-lite）
komeview の縮小版を素の HTML/JS 1ページで実装（ビルド工程なし）。niconicomments は UMD ビルドを `web/` にベンダリングする。

- **表示**: 黒背景（Split View で torne と並べる前提）に niconicomments でコメント描画。
- **再生**: komeview と同じ仮想クロック・手動同期。ロード完了で自動再生開始。
- **タッチUI**（iPad にキーボードは無い）:
  - 再生/一時停止・±1秒・±15秒 ボタン
  - 速度（1.0 / 1.25 / 1.5 / 1.75 / 2.0 の巡回ボタン）
  - **マーカーボタン**: ｷﾀ / OP / A / B / C / ED（検出できたものだけ表示。k/o/a/b/c/e キーの代替）
  - シークバー（ドラッグ対応・マーカー点表示）
- **マーカー検出**: komeview の `findMarkerOccurrences`（複数回検出・5分統合・閾値）を JS に移植。
- **フロー**: ページを開く →「コメント取得」ボタン（または自動で1回）→ `/api/play` → 再生開始
  → torne 側の再生開始に合わせて「ｷﾀ」ボタン等で頭出し。

### 5.3 初期スコープ外（検討事項）
- 自動追従（サーバがポーリングして再生開始を自動検出）… 今回は**アクセス時キックで十分**
- コメントの勢い波形・コメントリスト・NG機能（komeview 本体にある高度な機能）
- 過去に取得済みの kakolog 一覧からの選択再生
- ブラウザの Fullscreen API 対応（iPadOS Safari の挙動を実機確認してから）
- Cloudflare Tunnel + Access での公開（**ドメイン未所持のため後回し**。年千円程度で取得可）
  - ブラウザ（iPad等）は Google 認証/メールOTP でそのままアクセスできるが、
    **komeview からの取得（プログラムによる fetch）は対話ログインを通れないため素通しでは不可**。
  - 対応方法: Cloudflare Access の **Service Token** を使う。Zero Trust で Client ID/Secret を発行し
    Access ポリシーに Service Auth を追加、komeview 側は fetch に
    `CF-Access-Client-Id` / `CF-Access-Client-Secret` ヘッダを付与する（komeview に設定欄を追加、20行程度）。
  - 想定ユースケース: 外出先の Mac から komeview で自宅の komenasne サーバのコメントを取得する。
  - なお自宅内の komeview は従来どおり LAN 直（`http://192.168.x.x:8765`）でよく、
    Cloudflare 経由が必要なのは宅外クライアントのみ（経路は併存できる）。

---

## 6. 将来構想（本SPECのスコープ外）

- **komeview への統合（案A）**: nasne ポーリング・過去ログ取得を komeview（Electron main / TypeScript）へ移植し、
  XMLファイルを経由せず直接コメント再生する。「チャンネル+日時指定の取得」も komeview の UI に載せる。
  その際 komenasne は役目を終える。移植時は本リポジトリのロジック（チャンネルテーブル・vpos 書き換え・SSDP発見）を流用する。
