komenasne について


【概要】
nasneの動画再生と合わせて、ニコ生のタイムシフトの実況コメントを再生します。

同じネットワーク上のnasneの動画を再生した状態でこのスクリプトを起動することにより、
ブラウザーで同チャンネル同時刻のニコ生実況タイムシフトが再生されます。
Windows環境以外にMac環境でも起動します※後述


【動作環境】
タイムシフトの再生のため、ニコニコのプレミアカウントが必要です。
ニコニコの制限により、3週間以内の動画しかコメントが再生できません。
動画再生はPS4+torneでもスマホ+torneでもWindows機でPC TV Plusでも構いません。
コメントビューワーはWindowsもしくはMacの環境が必要です。
iniの設定により、ブラウザーの代わりにコメントビューワーソフトのjkcommentviewerを起動することもできます。


【セットアップ】
Python3.x系のインストールが必要です。

※Windowsの場合、Microsoft Storeで最新版を入れておくのが構築が楽かもしれません。
https://www.microsoft.com/ja-jp/search?q=python

Pythonインストール後に、pipコマンドで以下のモジュールをインストールしてください。
pip install requests
pip install beautifulsoup4

その後、komenasne.iniを開き、nasne1～nasne4までのIPを記入してください。
例えば1台しかない場合はnasne1だけを記入し、その他は空白にしてください。
nasneのIPはtorneの設定画面で確認できます。

ブラウザーの代わりにjkcommentviewerでコメントを表示することも可能です。
その場合はiniファイルのjkcommentviewer_pathのコメントアウトを切り替えて、パスを自分の環境に修正してください。


【実行】
torne等で動画を再生した直後に一旦停止してから、このスクリプトを起動してください。
同じネットワーク上であればいいので、PS4でテレビに動画を再生しながらPCのコメントをチラ見する、といった事が可能です。
「PC TV Plus」と「jkcommentviewer」の組み合わせであれば、ニコ生のようにコメントをオーバーレイ表示することも可能です。

起動方法：
コマンドラインで "python komenasne.py" を入力
もしくはエクスプローラーで komenasne.py をダブルクリック

その後、コメントビューワーを全画面にするなどしてから、動画の一旦停止を解除してから続きを再生してください。
Windows機の場合、ALTキーを押しながらTABでタスクを切り替えるのが使いやすいです。


【Macでの動作】
Python公式サイトから最新版をインストールし、ターミナルで"python3 komenasne.py" と入力することで実行できました。
pipのインストールを忘れないように。
