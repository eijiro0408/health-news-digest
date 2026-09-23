"""設定ファイル。キーワードや配信本数はここを書き換えるだけで調整できます。"""

# 1日に配信するニュースの本数
DAILY_COUNT = 7

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

# そのほかの RSS フィード（公式発表など）
EXTRA_FEEDS = [
    ("厚生労働省", "https://www.mhlw.go.jp/stf/news.rdf"),
]
