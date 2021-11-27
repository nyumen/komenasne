# komenasne について
<img src="src/superkabuop.jpg" alt="スーパーカブOP" width="60%" height="60%">  
<span style="font-size: 80%; float: right;">＊画像は「PC TV Plus」と「commenomi」を組み合わせて再生させたイメージです</span>  
  
### [ダウンロードはこちら](https://github.com/nyumen/komenasne/releases)
  
  
## 概要
nasneの動画再生と合わせての実況コメントを再生します。  
*使用イメージは以下のnoteの記事を参照  
[komenasneでトルネっぽく実況コメント付きでnasneの動画を再生させる](https://note.com/kamm/n/n8a519502718c)*  
  
同じネットワーク上のnasneの動画を再生した状態でこのツールを起動することにより、  
コメント再生ソフトーのcommenomiやブラウザーで同チャンネル同時刻のニコ生実況タイムシフトが再生されます。  
Windows環境以外にMac環境でも起動します※後述  
  
  
## 説明
- nasneの再生に連動して、commenomi（こめのみ）もしくはニコ生を同期させるアプリです。
- Windows / Mac両対応、ただしMac環境で動作させる場合は「Python」の実行環境が必要です。
- 動作設定はiniファイル。事前に自分の環境に合わせてテキストエディタで書き換える必要あり（nasneのローカルIPやチャンネル設定など）
- nasneの再生環境は問いません、PS4 / スマホ / PC TV Plusどれでも可。
- 視聴したい録画番組を再生してまず一時停止、次にkomenasne.batを実行（Windowsの場合）。実況画面が開いたらフルスクリーンにしてnasneの再生を再開。するとnasneの再生に連動して実況が同期します。
- 関東・中部・関西のチャンネルに対応しています（プログラムが理解できる人は自分でチャンネルを登録することも可能です※後述）
- 過去ログAPIの取得タイミングのため、直近15分以内のコメントは取得できません。また、3時と15時に1～2分ほど再起動が行われるため、過去ログが取得できないタイミングがあります。
  
  
## 更新履歴

### 2021-11-27 v1.08
五輪や鬼滅を快適に見るために色々と改良
- サブチャンネル対応
- コメント流量調整対応　※下に使い方の説明
- しょぼいカレンダーをもとにコメントをシリーズ一括取得　※[使い方](https://docs.google.com/spreadsheets/d/1-yKaSDpg_NK4LM_LbpXG--3n21iLZopRcEW6_sTLE-Q/edit?)- - 動作ログ出力対応　※komenasne.log に出力されます
usp=sharing
### 2021-01-29 v1.07
- 直接指定モードでチャンネルの指定を"jk4"だけでなく"日テレ"などでも指定できるようにしました
### 2021-01-29 v1.06
- 日本全国のチャンネルに対応（キー局の系列のみ）
- 隠し機能としてNASNEの再生中情報を参照しない直接取得モード実装（「高度な使い方」を参照） *BDレコーダーの録画番組で便利*
- 過去ログAPIのサイトがダウンしているときにエラーを表示
- iniファイルに存在しないNASNEのIPが指定されているときにエラーを表示
### 2021-01-05 v1.05
- exe化してPythonのインストールを不要にしました
- 福岡の放送局を追加しました
### 2021-01-03 v1.04
- タイトルに[解]などが入った番組への対応
- デフォルトのコメント再生ソフトをcommeonからcommenomiに変更
- AT-Xチャンネルへの対応
- 香川・岡山エリアの放送局を追加
### 2020-12-31 v1.03
- 実況ログの取得先をニコ生のタイムシフトからTVRemotePlus様の過去ログAPIに変更（ニコニコアカウントが不要になりました。過去すべての期間の動画に対応）
- コメント再生ソフトをjkcommentviewerからcommeonに変更
### 2020-12-30 v1.02
- 中部、関西在住の方でもでも使用できるようにキー局と紐づけ
- 再生中の動画が見つからないときのメッセージ表示
- Windowsのセットアップをbatファイル化（pipモジュールをインストール）
- Windowsの起動をbatファイル化
- iniファイルのnasneの設定をカンマ区切りに変更
### 2020-12-28 v1.01
- リリース
  
  
## 動作環境
コメント再生ソフトのcommenomiのダウンロードが必要です。 → [commenomi (こめのみ) ](http://air.fem.jp/commenomi/)  
動画再生はPS4+torneでもスマホ+torneでもWindows機でPC TV Plusでも構いません。  
iniの設定により、commenomiの代わりにブラウザでニコ生のタイムシフトから表示することもできます※。    
Macでもブラウザからニコ生のタイムシフトで表示することが出来ます※。  
*※プレミアムアカウント必須、公式チャンネルの3週間以内の動画まで。*  
  
  
## セットアップ
komenasne.iniを開き、[NASNE]セクションの"ip"にカンマ区切りでIPを記入してください。  
nasneのIPはtorneの設定画面で確認できます。  
*バージョンの古いメモ帳を使っている場合は、改行されずに表示されます。Windows10を最新版にアップデートするか、テキストエディタで編集してください。*  
  
次に、commenomi_pathを自分の環境に修正してください。commenomi.exeのプロパティからパスをコピーできます。  
  
実況ログの保存先がデフォルトでtempディレクトリになっているため、ログを保存したい場合は kakolog_dir を変更してください。  
  
  
## 実行
torne等で動画を再生した直後に一旦停止してから、komenasne.batをダブルクリックで実行してください。  
その後、コメント再生画面を全画面にするなどしてから、動画の一旦停止を解除してから続きを再生してください。  
インストーラーの仕様上、ウィルス対策ソフトWindows Defenderの誤検知に引っかかりやすいため、都度許可するかディレクトリごと対象外としてください。  
参考：[Windows 10のWindows Defenderで特定のファイルやフォルダーをスキャンしないように設定する方法](https://faq.nec-lavie.jp/qasearch/1007/app/servlet/relatedqa?QID=018507)
  
  
## コメント流量設定
v1.08から実装されたコメント流量調整機能の説明です。
komenasne.iniに[COMMENT]という項目が追加されています。コメント流量が指定した値を超えると、オリジナルのxmlファイルとともに間引きされたlimitファイルが作成されます。
例：
```
TBSテレビ_20211121_205946_54_日曜劇場「日本沈没－希望のひと－」第６話「抗えない日本沈没」[字][デ].xml
↓↓↓
TBSテレビ_20211121_205946_54_日曜劇場「日本沈没－希望のひと－」第６話「抗えない日本沈没」[字][デ]_limit.xml
```
設定値について
"comment_limit": noneを指定すると流量調整機能は動作しません。middleにするとおおよそコメントが重ならない程度のコメント量となり、lowの場合は字幕が読める程度にまで減ります。
"aborn_or_delete": 間引きされたコメントの行を削除するか非表示コメントに置き換えるかが選択できます。勢いグラフを使用しない方は、commenomiの動作が軽くなるdeleteを指定してください。
"limit_ratio" 間引きされたコメントが少ない場合、limitファイルを作成しない条件を指定します。例として、5を指定した場合、本来のコメント数に対して間引きされたコメント数が5%未満であればlimitファイルを作成しません。
＝＝＝
ちなみに歌詞ニキさんのコメントについては必ず表示されるようになっています。

komenasne.iniのデフォルト設定値(推奨値)
```[COMMENT]
# コメント流量設定 none, low, middle, high
comment_limit = middle
# 間引きしたコメントの出力設定
# aborn: 透明あぼーん(勢いグラフはそのまま、ファイルサイズ大), delete: 削除(勢いグラフ不正確、ファイルサイズ小)
aborn_or_delete = aborn
# 間引きしたコメント数がこの数値の%以下の場合、limitファイルを作成しない(0-99で指定、0で必ずlimitファイルを作成)
limit_ratio = 5
```
  
## commenomiの便利なショートカット
- SPACE 一時停止/再生
- A 最初のAのコメントに移動
- B 最初のBのコメントに移動
- C 最初のCのコメントに移動
- 0 先頭に戻る
- Ctrl + F コメント検索
- → 早送り
- ← 早戻し
- Ctrl + → 高速早送り
- Ctrl + ← 高速早戻し
- マウスのホイールで微調整
  
同じネットワーク上であればいいので、PS4でテレビに動画を再生しながらPCのコメントをチラ見する、といった事が可能です。  
「PC TV Plus」と「commenomi」の組み合わせであれば、ニコ生のようにコメントをオーバーレイ表示することも可能です。  
Windows機の場合、ALTキーを押しながらTABでタスクを切り替えるのが使いやすいです。  
  
  
## MacやARM版Windowsでの動作
Pythonの最新版を[こちらのページから](https://pythonlinks.python.jp/ja/index.html)インストールしてください。  
次にコマンドラインで以下を実行してください。  
pip install requests  
pip install beautifulsoup4  
  
ターミナルで"python3 komenasne.py" と入力することでブラウザでニコ生のタイムシフトが開きます。  
  
  
## 高度な使い方

【直接取得モード】
再生中のNASNEの情報を参照せず、チャンネルと日時を指定してコメントログを取得する機能です。
```
komenasne.exe [channel] [yyyy-mm-dd HH:MM] [total_minutes] option:[title]
例1: komenasne.exe "jk181" "2021-01-25 02:00" 30 "＜アニメギルド＞ゲキドル　＃３"
例2: komenasne.exe "TBS" "2021-01-23 21:00" 60
チャンネルリスト: NHK Eテレ 日テレ テレ朝 TBS テレ東 フジ MX BS11 または以下のjk**を指定
jk1 NHK総合
jk2 NHK Eテレ
jk4 日本テレビ
jk5 テレビ朝日
jk6 TBSテレビ
jk7 テレビ東京
jk8 フジテレビ
jk9 TOKYO MX
jk101 NHK BS1
jk103 NHK BSプレミアム
jk141 BS日テレ
jk151 BS朝日
jk161 BS-TBS
jk171 BSテレ東
jk181 BSフジ
jk191 WOWOWプライム
jk211 BS11イレブン
jk222 BS12トゥエルビ
jk236 BSアニマックス
jk333 AT-X
```

【サイレントモード】
mode_silentをつけるとkommenomiが起動せず、xmlファイルのみが作成されます。
```
komenasne.exe mode_silent
```

【コメント流量調整指定】
コメント流量調整を指定します。iniファイルの指定より優先されます。
```
komenasne.exe mode_limit_none
komenasne.exe mode_limit_low
komenasne.exe mode_limit_middle
komenasne.exe mode_limit_high
```


  
## スペシャルサンクス
- commenomi (こめのみ) http://air.fem.jp/commenomi/
- ニコニコ実況 過去ログ API https://jikkyo.tsukumijima.net/
- チャンネルリスト　NicoJK　elaina/saya
