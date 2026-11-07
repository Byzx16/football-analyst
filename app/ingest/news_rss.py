import feedparser
import json
from datetime import datetime, timezone, timedelta
from typing import List
import google.generativeai as genai
from app.config import settings
from app.utils.cache import get_cache, set_cache

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel("gemini-2.0-flash-exp")

# RSS feeds (semua publik, legal)
GENERAL_FEEDS = [
    ("BBC Football", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("Guardian Football", "https://www.theguardian.com/football/rss"),
    ("ESPN Soccer", "https://www.espn.com/espn/rss/soccer/news"),
]

TEAM_FEEDS = {
    "Arsenal": "https://www.arsenal.com/rss/news",
    "Chelsea": "https://www.chelseafc.com/en/rss-feed",
    "Manchester United": "https://www.manutd.com/en/rss/news",
    "Liverpool": "https://www.liverpoolfc.com/news.rss",
    "Real Madrid": "https://www.realmadrid.com/en/rss/news",
    "Barcelona": "https://www.fcbarcelona.com/en/rss/news",
    "Juventus": "https://www.juventus.com/en/news/feed",
    "Bayern Munich": "https://fcbayern.com/en/news/rss",
    "PSG": "https://en.psg.fr/rss/news",
}

def _classify_sentiment(title: str, summary: str, team_name: str) -> str:
    """Klasifikasi sentimen untuk 1 tim (positive/negative/neutral)."""
    prompt = f"""Klasifikasi berita berikut untuk tim {team_name}.
Berita ini POSITIVE jika: kemenangan, transfer masuk bagus, pemain pulih, kontrak baru.
Berita ini NEGATIVE jika: kekalahan, cedera, konflik, transfer gagal.
Berita ini NEUTRAL jika: informasi umum, jadwal, rumor netral.

Judul: {title}
Ringkasan: {summary}

Balas SATU KATA saja: positive, negative, atau neutral."""

    try:
        resp = _model.generate_content(prompt, generation_config={"temperature": 0})
        out = resp.text.strip().lower()
        return out if out in ("positive", "negative", "neutral") else "neutral"
    except Exception:
        return "neutral"


def fetch_team_news(team_name: str, hours_back: int = 72) -> List[dict]:
    """Ambil berita terkini untuk tim tertentu dari RSS."""
    cache_key = f"news:{team_name}"
    if cached := get_cache(cache_key):
        return json.loads(cached)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    all_news = []

    # Feed umum
    for source_name, url in GENERAL_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined = f"{title} {summary}".lower()
                if team_name.lower() not in combined:
                    continue
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue
                all_news.append({
                    "title": title,
                    "summary": summary[:500],
                    "url": entry.get("link", ""),
                    "source": source_name,
                    "published_at": published.isoformat() if published else None,
                })
        except Exception as e:
            print(f"[news] {source_name} failed: {e}")

    # Feed klub
    if team_name in TEAM_FEEDS:
        try:
            feed = feedparser.parse(TEAM_FEEDS[team_name])
            for entry in feed.entries[:15]:
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue
                all_news.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:500],
                    "url": entry.get("link", ""),
                    "source": f"{team_name} Official",
                    "published_at": published.isoformat() if published else None,
                })
        except Exception as e:
            print(f"[news] official {team_name} failed: {e}")

    # Ambil top 5, klasifikasi sentimen
    all_news = all_news[:5]
    for n in all_news:
        n["sentiment"] = _classify_sentiment(n["title"], n["summary"], team_name)

    set_cache(cache_key, json.dumps(all_news), 3600)
    return all_news


def _parse_date(entry) -> datetime | None:
    """Parse berbagai format RSS date."""
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            import time
            return datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
    except Exception:
        pass
    return None