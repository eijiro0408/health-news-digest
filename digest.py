"""毎朝のニュースダイジェストを作る。

1. Google ニュース等の RSS から候補記事を集める
2. Claude が重要な記事を選び、注目ポイントを書く
3. docs/ にスマホ向けページを、out/ にメール本文を書き出す

使い方:
    python digest.py            # 通常実行（ANTHROPIC_API_KEY が必要）
    python digest.py --no-ai    # AI を使わずキーワード採点で選ぶ（テスト用）
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import config

JST = timezone(timedelta(hours=9))
ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
OUT = ROOT / "out"
HISTORY_FILE = DOCS / "data" / "history.json"
USER_AGENT = "Mozilla/5.0 (compatible; health-news-digest/1.0)"


# ---------------------------------------------------------------- 収集

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(el: ET.Element, name: str) -> str:
    for c in el:
        if local(c.tag) == name:
            return (c.text or "").strip()
    return ""


def parse_date(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return parsedate_to_datetime(s).astimezone(JST)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(JST)
    except ValueError:
        return None


def parse_feed(data: bytes, default_source: str) -> list[dict]:
    items = []
    root = ET.fromstring(data)
    for el in root.iter():
        if local(el.tag) != "item":
            continue
        title = child_text(el, "title")
        link = child_text(el, "link") or el.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", "")
        source = child_text(el, "source") or default_source
        source_url = next((c.get("url", "") for c in el if local(c.tag) == "source"), "")
        # Google ニュースのタイトル末尾の「 - 媒体名」を取り除く
        if source and title.endswith(f" - {source}"):
            title = title[: -len(f" - {source}")]
        published = parse_date(child_text(el, "pubDate") or child_text(el, "date"))
        if title and link:
            items.append({"title": title, "link": link, "source": source, "source_url": source_url, "published": published})
    return items


def google_news_url(query: str) -> str:
    q = urllib.parse.quote(f"{query} when:1d")
    return f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"


def normalize(title: str) -> str:
    title = re.sub(r"[（(][^（()）]*[)）]\s*$", "", title)  # 末尾の「（媒体名）」を無視
    return re.sub(r"[\s　「」『』【】（）()・、。!！?？:：\-－―]", "", title)


def is_paywalled(item: dict) -> bool:
    """有料会員限定の記事が多いメディアや、見出しに「会員限定」などとある記事を判定する。"""
    where = " ".join([item["source"], item["source_url"], urllib.parse.urlparse(item["link"]).netloc])
    return any(p in where for p in config.PAYWALL_SOURCES) or any(
        w in item["title"] for w in config.PAYWALL_TITLE_WORDS
    )


def collect(seen_links: set[str], seen_titles: set[str]) -> list[dict]:
    feeds = [("Googleニュース", google_news_url(q)) for q in config.GOOGLE_NEWS_QUERIES]
    feeds += config.EXTRA_FEEDS
    now = datetime.now(JST)
    cutoff = now - timedelta(hours=config.LOOKBACK_HOURS)

    found: dict[str, dict] = {}
    skipped = 0
    for name, url in feeds:
        try:
            items = parse_feed(fetch(url), name)
        except Exception as e:  # 1つのフィードが落ちても他は続ける
            print(f"[warn] {name} の取得に失敗: {e}", file=sys.stderr)
            continue
        for it in items:
            if it["published"] and it["published"] < cutoff:
                continue
            if is_paywalled(it):
                skipped += 1
                continue
            key = normalize(it["title"])
            if it["link"] in seen_links or key in seen_titles or key in found:
                continue
            found[key] = it

    print(f"有料メディアの記事を {skipped} 件除外しました")
    items = sorted(found.values(), key=lambda x: x["published"] or now, reverse=True)
    return items[: config.MAX_CANDIDATES]


# ---------------------------------------------------------------- 選定

SYSTEM_PROMPT = f"""あなたは、医療・健康・福祉・自治体行政に携わる人向けの朝刊ニュースの編集者です。
候補の見出し一覧から、今朝読むべきニュースを{config.DAILY_COUNT}本選んでください。

選び方:
- 現場や住民の暮らしに影響する制度改正・予算・通知・調査結果・新しい取り組みを優先する
- 国の動きだけでなく、各地の自治体のユニークな取り組みも入れ、地域が偏らないようにする
- 同じ出来事を扱う記事は1本にまとめる
- 芸能・スポーツ・事件事故のみの話題、広告的な記事は避ける
- 読者は無料で読める記事だけを求めている。有料会員限定と思われる記事は選ばない
- カテゴリは次から選ぶ: {"、".join(config.CATEGORIES)}

注目ポイントについて:
- 見出しから読み取れる事実だけを使い、見出しにない数字や固有名詞を作らない
- 「なぜ現場や自治体にとって大事か」を1〜2文、です・ます調で書く
"""


def schema() -> dict:
    item = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "description": "候補の番号"},
            "category": {"type": "string", "enum": config.CATEGORIES},
            "region": {"type": "string", "description": "「全国」または都道府県名"},
            "headline": {"type": "string", "description": "読みやすく整えた見出し"},
            "point": {"type": "string", "description": "注目ポイント（1〜2文）"},
        },
        "required": ["id", "category", "region", "headline", "point"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "overview": {"type": "string", "description": "今朝のニュース全体を1文でまとめた導入"},
            "items": {"type": "array", "items": item},
        },
        "required": ["overview", "items"],
        "additionalProperties": False,
    }


def select_with_claude(candidates: list[dict]) -> dict:
    import anthropic

    lines = []
    for i, c in enumerate(candidates):
        when = c["published"].strftime("%m/%d %H:%M") if c["published"] else "日時不明"
        lines.append(f"[{i}] {c['title']}（{c['source']}・{when}）")

    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=config.MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "候補一覧:\n" + "\n".join(lines)}],
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema()}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude が応答を拒否しました")
    text = next(b.text for b in response.content if b.type == "text")
    result = json.loads(text)

    picked, used = [], set()
    for it in result["items"]:
        if 0 <= it["id"] < len(candidates) and it["id"] not in used:
            used.add(it["id"])
            picked.append({**candidates[it["id"]], **it})
    result["items"] = picked[: config.DAILY_COUNT]
    return result


KEYWORDS = {
    "医療": ["医療", "病院", "医師", "看護", "診療", "薬"],
    "健康": ["健康", "健診", "感染", "ワクチン", "予防", "がん"],
    "福祉・介護": ["介護", "福祉", "障害", "生活保護", "高齢", "認知症"],
    "自治体": ["市", "町", "村", "県", "自治体", "知事", "議会"],
    "子育て・保健": ["子育て", "こども", "子ども", "母子", "保健", "出産"],
}


def select_without_ai(candidates: list[dict]) -> dict:
    """AI が使えないときの予備。キーワード一致数で採点する。"""
    scored = []
    for c in candidates:
        hits = {cat: sum(k in c["title"] for k in kws) for cat, kws in KEYWORDS.items()}
        cat = max(hits, key=hits.get)
        if hits[cat]:
            scored.append((sum(hits.values()), cat, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    items = [
        {**c, "category": cat, "region": "", "headline": c["title"], "point": ""}
        for _, cat, c in scored[: config.DAILY_COUNT]
    ]
    return {"overview": "キーワードで自動選定したニュースです。", "items": items}


# ---------------------------------------------------------------- 出力

def render_items(items: list[dict]) -> str:
    parts = []
    for n, it in enumerate(items, 1):
        meta = " ・ ".join(x for x in [it["region"], it["source"]] if x)
        point = f'<p class="point">{html.escape(it["point"])}</p>' if it["point"] else ""
        parts.append(f"""
<article class="card">
  <div class="tags"><span class="num">{n}</span><span class="cat">{html.escape(it["category"])}</span></div>
  <h2><a href="{html.escape(it["link"])}" target="_blank" rel="noopener">{html.escape(it["headline"])}</a></h2>
  {point}
  <p class="meta">{html.escape(meta)}</p>
</article>""")
    return "".join(parts)


PAGE_CSS = """
:root{--bg:#f6f7f5;--card:#fff;--ink:#1d2320;--sub:#5d6862;--line:#e3e7e4;--accent:#1f7a5c;--chip:#e6f2ed}
@media (prefers-color-scheme:dark){:root{--bg:#141816;--card:#1d2320;--ink:#e8ece9;--sub:#9aa69f;--line:#2c3430;--accent:#5cc49c;--chip:#23332c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.7}
main{max-width:680px;margin:0 auto;padding:24px 16px 48px}
header h1{font-size:1.35rem;margin:0}
header .date{color:var(--sub);margin:4px 0 0;font-size:.9rem}
.overview{margin:16px 0 20px;color:var(--sub)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:12px}
.tags{display:flex;gap:8px;align-items:center;margin-bottom:6px}
.num{font-weight:700;color:var(--accent)}
.cat{background:var(--chip);color:var(--accent);font-size:.75rem;padding:2px 8px;border-radius:99px}
.card h2{font-size:1.05rem;margin:0 0 6px;line-height:1.5}
.card h2 a{color:var(--ink);text-decoration:none}
.card h2 a:hover{text-decoration:underline}
.point{margin:0 0 6px;font-size:.93rem}
.meta{margin:0;color:var(--sub);font-size:.8rem}
nav{margin-top:28px;font-size:.9rem}
nav a{color:var(--accent);margin-right:12px}
footer{margin-top:24px;color:var(--sub);font-size:.75rem}
"""


def render_page(date: datetime, result: dict, back: str) -> str:
    d = f"{date.year}年{date.month}月{date.day}日"
    return f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>医療・福祉ニュース {date:%Y-%m-%d}</title>
<link rel="manifest" href="{back}manifest.json"><meta name="theme-color" content="#1f7a5c">
<style>{PAGE_CSS}</style></head>
<body><main>
<header><h1>けさの医療・福祉ニュース</h1><p class="date">{d}</p></header>
<p class="overview">{html.escape(result["overview"])}</p>
{render_items(result["items"])}
<nav><a href="{back}index.html">最新号</a><a href="{back}archive/index.html">過去の号</a></nav>
<footer>見出しは各報道機関のものです。注目ポイントはAIが見出しをもとに作成しています。詳しくは元記事をご確認ください。</footer>
</main></body></html>
"""


def render_email(date: datetime, result: dict, page_url: str) -> str:
    rows = []
    for n, it in enumerate(result["items"], 1):
        meta = " ・ ".join(x for x in [it["category"], it["region"], it["source"]] if x)
        point = f'<p style="margin:4px 0;color:#333;font-size:14px">{html.escape(it["point"])}</p>' if it["point"] else ""
        rows.append(f"""
<tr><td style="padding:14px 0;border-bottom:1px solid #e3e7e4">
<div style="color:#1f7a5c;font-size:12px">{n}. {html.escape(meta)}</div>
<a href="{html.escape(it["link"])}" style="color:#1d2320;font-size:16px;font-weight:bold;text-decoration:none">{html.escape(it["headline"])}</a>
{point}
</td></tr>""")
    link = f'<p style="margin-top:20px"><a href="{page_url}" style="color:#1f7a5c">Webで見る・過去の号</a></p>' if page_url else ""
    return f"""<!doctype html><html><body style="margin:0;background:#f6f7f5">
<div style="max-width:620px;margin:0 auto;padding:20px 16px;font-family:sans-serif;background:#fff">
<h1 style="font-size:20px;margin:0 0 4px">けさの医療・福祉ニュース</h1>
<div style="color:#5d6862;font-size:13px">{date:%Y/%m/%d}</div>
<p style="color:#5d6862;font-size:14px">{html.escape(result["overview"])}</p>
<table width="100%" cellpadding="0" cellspacing="0">{"".join(rows)}</table>
{link}
<p style="color:#8a948e;font-size:11px;margin-top:16px">注目ポイントはAIが見出しをもとに作成しています。</p>
</div></body></html>"""


def write_archive_index() -> None:
    days = sorted((p.stem for p in (DOCS / "archive").glob("20*.html")), reverse=True)
    links = "".join(f'<li><a href="{d}.html">{d}</a></li>' for d in days)
    (DOCS / "archive" / "index.html").write_text(f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>過去の号</title><style>{PAGE_CSS} li{{margin:6px 0}} li a{{color:var(--accent)}}</style></head>
<body><main><header><h1>過去の号</h1></header><ul>{links}</ul>
<nav><a href="../index.html">最新号</a></nav></main></body></html>
""", encoding="utf-8")


# ---------------------------------------------------------------- 履歴

def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_history(history: list[dict], date: datetime, items: list[dict]) -> None:
    cutoff = (date - timedelta(days=config.HISTORY_DAYS)).strftime("%Y-%m-%d")
    history = [h for h in history if h["date"] >= cutoff]
    history += [{"date": date.strftime("%Y-%m-%d"), "link": it["link"], "title": it["title"]} for it in items]
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ai", action="store_true", help="AI を使わずに選ぶ")
    args = parser.parse_args()

    today = datetime.now(JST)
    history = load_history()
    candidates = collect({h["link"] for h in history}, {normalize(h["title"]) for h in history})
    print(f"候補: {len(candidates)} 件")
    if not candidates:
        sys.exit("候補の記事が見つかりませんでした")

    if args.no_ai or not os.environ.get("ANTHROPIC_API_KEY"):
        print("キーワード採点で選定します")
        result = select_without_ai(candidates)
    else:
        try:
            result = select_with_claude(candidates)
        except Exception as e:
            print(f"[warn] AI 選定に失敗したためキーワード採点に切り替えます: {e}", file=sys.stderr)
            result = select_without_ai(candidates)

    stamp = today.strftime("%Y-%m-%d")
    (DOCS / "archive").mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(render_page(today, result, ""), encoding="utf-8")
    (DOCS / "archive" / f"{stamp}.html").write_text(render_page(today, result, "../"), encoding="utf-8")
    write_archive_index()
    save_history(history, today, result["items"])

    base = os.environ.get("SITE_URL", "").rstrip("/")
    OUT.mkdir(exist_ok=True)
    (OUT / "email.html").write_text(render_email(today, result, f"{base}/archive/{stamp}.html" if base else ""), encoding="utf-8")
    (OUT / "subject.txt").write_text(f"【けさの医療・福祉ニュース】{today:%m/%d} {result['items'][0]['headline'][:30]} ほか", encoding="utf-8")

    for n, it in enumerate(result["items"], 1):
        print(f"{n}. [{it['category']}] {it['headline']}")


if __name__ == "__main__":
    main()
