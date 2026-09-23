# けさの医療・福祉ニュース

健康・医療・福祉・自治体のニュースを全国から集め、AI（Claude）が毎朝7本選んで
**7:00 に Gmail で配信**し、**スマホで見られる Web ページ**（GitHub Pages）にも載せます。

## しくみ

```
6:30  GitHub Actions が起動
      ├ Google ニュース（9つの検索語）＋厚労省の RSS から直近30時間の記事を集める
      ├ Claude が7本を選び、カテゴリ・地域・注目ポイントを付ける
      ├ docs/ の Web ページを更新（過去の号も残る）
7:00  └ Gmail でメールを送信
```

- 過去14日間に配信した記事は再配信しません
- AI が使えないときは、キーワード採点で選んで配信を続けます

## セットアップ（初回だけ・約20分）

### 1. GitHub にリポジトリを作る
1. https://github.com/new で新しいリポジトリを作る（例: `health-news-digest`）
2. このフォルダの中身をアップロードする（`.github` フォルダも忘れずに）

### 2. 鍵を用意する
| 名前 | 取得方法 |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → API Keys で作成（クレジットの購入が必要） |
| `GMAIL_ADDRESS` | 送信に使う Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Google アカウントで2段階認証をオンにしてから https://myaccount.google.com/apppasswords で作成（16桁） |
| `MAIL_TO` | 配信先。カンマ区切りで複数可（例: `a@example.com,b@example.com`） |

### 3. GitHub に鍵を登録する
リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で、上の4つを登録する。

### 4. Web ページを公開する
**Settings → Pages** で Source を「Deploy from a branch」、Branch を `main` / `/docs` にして保存する。
数分後に `https://<ユーザー名>.github.io/health-news-digest/` で見られるようになります。
スマホのブラウザで開き「ホーム画面に追加」すると、アプリのように使えます。

### 5. 試しに動かす
**Actions → 毎朝のニュース配信 → Run workflow** を押すと、その場でメールが届きます。
その後は毎朝 7:00 に自動で届きます。

## カスタマイズ
`config.py` を書き換えるだけで変更できます。

- `DAILY_COUNT` … 配信本数
- `GOOGLE_NEWS_QUERIES` … 集める記事のキーワード
- `EXTRA_FEEDS` … 追加の RSS（自治体や業界紙など）
- `CATEGORIES` … カテゴリ名

## 手元で試す
```bash
pip install -r requirements.txt
python digest.py --no-ai     # AI なし（無料）で動作確認
```
結果は `docs/index.html`（Web ページ）と `out/email.html`（メール本文）に出力されます。

## 費用の目安
- GitHub Actions / Pages：無料（公開リポジトリの場合。非公開でも無料枠内に収まります）
- Claude API：1日あたり数円〜十数円程度（候補120件の見出しを読み込むため）
- Gmail：無料

## 注意
- 注目ポイントは AI が**見出しだけをもとに**書いています。記事本文は読んでいないので、詳しくは元記事でご確認ください。
- 記事の見出し・リンクは各報道機関のものです。
