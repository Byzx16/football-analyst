import httpx, json
from app.config import settings, COMPETITIONS
from app.utils.cache import get_cache, set_cache

async def fetch_odds_for_competition(competition_slug: str) -> list[dict]:
    comp = COMPETITIONS[competition_slug]
    key = f"odds:{competition_slug}"
    
    # Pakai fallback cache
    if cached := get_cache(key):
        return json.loads(cached)

    url = f"{settings.odds_api_base}/sports/{comp['odds_key']}/odds"
    params = {
        "apiKey": settings.odds_api_key,
        "regions": "eu",
        "markets": "h2h,totals,spreads",
        "oddsFormat": "decimal",
    }
    
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            resp = await c.get(url, params=params)
            if resp.status_code == 401:
                print("⚠️ Peringatan: API Key Odds (The Odds API) tidak valid atau limit habis. Lanjut analisa tanpa data odds.")
                return []
            resp.raise_for_status()
            data = resp.json()
        set_cache(key, json.dumps(data), 1800)
        return data
    except Exception as e:
        print(f"⚠️ Gagal mengambil odds: {e}. Lanjut analisa tanpa odds.")
        return []

def extract_best_odds(match_odds: dict, market: str, selection: str) -> float | None:
    best = None
    for bm in match_odds.get("bookmakers", []):
        for m in bm.get("markets", []):
            if m["key"] != market:
                continue
            for o in m.get("outcomes", []):
                if o["name"].lower() == selection.lower():
                    if best is None or o["price"] > best:
                        best = o["price"]
    return best