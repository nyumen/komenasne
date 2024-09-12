# komenasne について
<img src="src/superkabuop.jpg" alt="スーパーカブOP" width="60%" height="60%">  
<span style="font-size: 80%; float: right;">＊画像は「PC TV Plus」と「commenomi」を組み合わせて再生させたイメージです</span>  
  
### [ダウンロードはこちら](https://github.com/nyumen/komenasne/releases)
  
  
## 概要
nasneの動画再生と合わせての実況コメントを再生します。  
*使用イメージは以下のnoteの記事を参照  
[komenasneでトルネっぽく実況コメント付きでnasneの動画を再生させる](https://note.com/kamm/n/n8a519502718c)*  
  
  
## 動作に必要な環境
- Nasne
- Windows環境
- PC TV Plus
- commenomi
- jkcommentviewer（任意）
  
## 説明
- nasneの再生に連動して、commenomi（こめのみ）を実行アプリです。v1.1より視聴中のチャンネルに応じたjkcommentviewerの起動にも対応。
- Windowsのnasne動画再生ソフト「PC TV Plus」が必要です。
- 動作設定はiniファイル。事前に自分の環境に合わせてテキストエディタで書き換える必要あり（nasneのローカルIPやチャンネル設定など）
- 過去ログAPIの取得タイミングのため、直近5分以内のコメントは取得できません。
- PC TV Plusやtorneにニコニコ実況機能が搭載されたので存在意義が微妙になりましたが、BS民放のコメントも再生することができます。
- ニコニコ実況へのコメント投稿はNX-Jikkyoでニコニコアカウントと連動しての投稿がおすすめです。
  
## セットアップ
- commenomiをダウンロードして、背景を透明、常に最前面になるように設定します。  
- komenasne.ini.exampleをkomenasne.iniにリネームしてテキストエディタで開き、[NASNE]セクションの"ip"にカンマ区切りでIPを記入してください。nasneのIPはtorneの設定画面で確認できます。  
*バージョンの古いメモ帳を使っている場合は、改行されずに表示されます。Windows10を最新版にアップデートするか、テキストエディタで編集してください。*    
- 次に、commenomi_pathを自分の環境に修正してください。commenomi.exeのプロパティからパスをコピーできます。  
- jkcommentviewerと連動したい場合はインストールしたjkcommentviewer.exeのパスをiniファイルのjkcommentviewer_pathに設定してください。
- komenasne.exeを右クリックして「タスクバーに配置」を選び、そこからタスクバーの一番左に配置します。
  
## 実行
- （komenasneがタスクバーの一番左に配置されている状態で）PC TV Plusで番組を再生が開始された後にWindowsキーを押しながら数字の1を押すと、commenomiやjkcommentviewerが起動し再生中の番組に応じたコメントが流れます。アニメの場合、再生が始まると同時にキーボードの"k"を入力すると大体時間が合わせられます。アニメ以外はキーボードのカーソルの左右やマウスのホイールでタイミングを合わせてください。  
インストーラーの仕様上、ウィルス対策ソフトWindows Defenderの誤検知に引っかかりやすいため、都度許可するかディレクトリごと対象外としてください。  
参考：[Windows 10のWindows Defenderで特定のファイルやフォルダーをスキャンしないように設定する方法](https://faq.nec-lavie.jp/qasearch/1007/app/servlet/relatedqa?QID=018507)
  
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
- ダブルクリックで全画面とウインドウ表示の切り替え

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
jk211 BS11
jk222 BS12
jk236 BSアニマックス
jk333 AT-X
```
  
  
## スペシャルサンクス
- commenomi (こめのみ) http://air.fem.jp/commenomi/
- ニコニコ実況 過去ログ API https://jikkyo.tsukumijima.net/
- NX-Jikkyo https://nx-jikkyo.tsukumijima.net
- チャンネルリスト　NicoJK　elaina/saya
- アイコン提供 SW-326JKM様 https://www.nicovideo.jp/user/289866
<img src="src/logo_komenas1.png" alt="ロゴ1" width="8%" height="8%"> 
<img src="src/logo_komenas2.png" alt="ロゴ2" width="8%" height="8%">  
