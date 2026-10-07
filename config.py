"""設定ファイル。キーワードや配信本数はここを書き換えるだけで調整できます。"""

# 1日に配信するニュースの本数
DAILY_COUNT = 7

# AI に選ばせる予備の本数（有料記事だった場合の入れ替え用）
SPARE_COUNT = 5

# 何時間前までのニュースを候補にするか
LOOKBACK_HOURS = 30

# Claude に渡す候補の最大数（多いほど精度は上がるが料金も増える）
MAX_CANDIDATES = 120

# 過去に配信した記事を何日間覚えておくか（同じ記事を再配信しないため）
HISTORY_DAYS = 14

# 使う Claude モデル
MODEL = "claude-opus-5"

# カテゴリ（メールとWebページの見出しに使います）
CATEGORIES = ["医療", "健康", "福祉・介護", "自治体", "子育て・保健"]

# Google ニュースの検索クエリ（日本語・全国）
GOOGLE_NEWS_QUERIES = [
    "医療 OR 病院 OR 医師 OR 看護",
    "健康 OR 健診 OR 感染症 OR ワクチン",
    "介護 OR 福祉 OR 障害者 OR 生活保護",
    "厚生労働省 OR こども家庭庁",
    "自治体 OR 市役所 OR 町役場 OR 県庁 福祉",
    "自治体 医療 OR 保健所 OR 地域包括ケア",
    "子育て支援 OR 母子保健 OR 少子化対策",
    "高齢者 OR 認知症 OR フレイル",
    "診療報酬 OR 介護報酬 OR 医療DX OR マイナ保険証",
]

# 有料会員限定の記事が多いメディア（ここに載っているメディアの記事は配信しません）
# 読めない記事が届いたら、そのメディアのドメインか名前をここに追加してください
PAYWALL_SOURCES = [
    # 全国紙・経済紙
    "nikkei.com", "日本経済新聞", "yomiuri.co.jp", "読売新聞", "asahi.com", "朝日新聞",
    "mainichi.jp", "毎日新聞", "sankei.com", "産経新聞",
    # 地方紙
    "hokkaido-np.co.jp", "北海道新聞", "hokkoku.co.jp", "北國新聞", "tokyo-np.co.jp", "東京新聞",
    "chunichi.co.jp", "中日新聞", "nishinippon.co.jp", "西日本新聞", "kahoku.news", "河北新報",
    "shinmai.co.jp", "信濃毎日新聞", "kyoto-np.co.jp", "京都新聞", "kobe-np.co.jp", "神戸新聞",
    "chugoku-np.co.jp", "中国新聞", "at-s.com", "静岡新聞", "niigata-nippo.co.jp", "新潟日報",
    "kochinews.co.jp", "高知新聞", "kumanichi.com", "熊本日日新聞", "373news.com", "南日本新聞",
    "okinawatimes.co.jp", "沖縄タイムス", "ryukyushimpo.jp", "琉球新報", "sanyonews.jp", "山陽新聞",
    "ehime-np.co.jp", "愛媛新聞", "tokushima-np.co.jp", "徳島新聞", "fukuishimbun.co.jp", "福井新聞",
    "shimotsuke.co.jp", "下野新聞", "jomo-news.co.jp", "上毛新聞", "ibaraki-np.co.jp", "茨城新聞",
    "yamagata-np.jp", "山形新聞", "iwate-np.co.jp", "岩手日報", "toonippo.co.jp", "東奥日報",
    "sakigake.jp", "秋田魁新報", "sanin-chuo.co.jp", "山陰中央新報", "the-miyanichi.co.jp", "宮崎日日新聞",
    "oita-press.co.jp", "大分合同新聞", "nagasaki-np.co.jp", "長崎新聞", "gifu-np.co.jp", "岐阜新聞",
    "kanaloco.jp", "神奈川新聞", "saitama-np.co.jp", "埼玉新聞", "chibanippo.co.jp", "千葉日報",
    # 医療・業界専門紙
    "medical.nikkeibp.co.jp", "日経メディカル", "nikkeibp.co.jp", "日経BP", "m3.com",
    "mixonline.jp", "ミクスOnline", "jiho.jp", "じほう", "business.nikkei.com", "日経ビジネス",
    "nikkei.co.jp", "日経Gooday", "carenet.com", "CareNet",
    # 2026-09-29 に混ざった地方紙と、同じように有料会員制の多い地方紙・専門紙
    "nankainn.com", "hokuroku.co.jp", "minato-yamaguchi.co.jp", "ubenippo.co.jp",
    "kushironews.jp", "tokachi.co.jp", "tomamin.co.jp", "muromin.jp", "daily-tohoku.co.jp",
    "mutusinpou.co.jp", "iwanichi.co.jp", "shonai-nippo.co.jp", "minpo.jp", "minyu-net.com",
    "webun.jp", "sannichi.co.jp", "shimintimes.co.jp", "nara-np.co.jp", "agara.co.jp",
    "isenp.co.jp", "nnn.co.jp", "shikoku-np.co.jp", "saga-s.co.jp", "y-mainichi.co.jp",
    "yaeyama-nippo.co.jp", "hakodate-np.co.jp", "hokuu.co.jp", "senyonews.jp",
    "agrinews.co.jp", "yakuji.co.jp", "jmedj.co.jp", "fukushishimbun.com", "nikkan.co.jp",
    "kensetsunews.com", "decn.co.jp", "silver-news.com", "上越タイムス", "joetsutj.com",
    # 2026-10 に混ざったもの
    "daily-tohoku", "デーリー東北", "jbpress.ismedia.jp", "JBpress",
]

# 記事ページにこの表示があれば「冒頭だけ無料・続きは会員登録や有料」とみなして除外する
# （47NEWS は冒頭だけ載せて「記事全文を読む」で地方紙の有料サイトへ飛ばす形）
PAYWALL_PAGE_MARKERS = [
    "記事全文を読む", "この記事は会員限定", "会員限定記事", "有料会員限定", "有料会員になると",
    "続きは会員", "続きをお読みいただくには", "この続きを読むには", "この記事の続きを読むには",
    "この続きをみるには", "購読者限定", "会員登録すると続き", "ログインすると続き",
    "ログインして続きを読む", "無料会員登録で続き", "有料記事",
]

# メディア名にこの言葉が入っていれば、新聞社のサイトとみなして除外する
# （同じ記事でも Yahoo!ニュースや47NEWS経由なら無料で読めるので、そちらは残る）
PAYWALL_NAME_WORDS = ["新聞", "日報", "新報", "民報"]

# 見出しにこの言葉があれば有料記事とみなして除外する
PAYWALL_TITLE_WORDS = ["会員限定", "有料会員", "有料記事", "プレミアム記事", "購読者限定"]

# そのほかの RSS フィード（公式発表など）
EXTRA_FEEDS = [
    ("厚生労働省", "https://www.mhlw.go.jp/stf/news.rdf"),
]
