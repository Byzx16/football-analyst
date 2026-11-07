import httpx, json, hashlib
from datetime import date, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings, COMPETITIONS
from app.utils.cache import get_cache, set_cache

def _cache_key(path: str, params: dict) -> str:
    raw = path + json.dumps(params, sort_keys=True)
    return "apif:" + hashlib.md5(raw.encode()).hexdigest()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def _get(path: str, params: dict, ttl: int = 6 * 3600):
    key = _cache_key(path, params)
    if cached := get_cache(key):
        return json.loads(cached)
    async with httpx.AsyncClient(timeout=20) as c:
        resp = await c.get(
            f"{settings.api_football_base}/{path}",
            params=params,
            headers={"x-apisports-key": settings.api_football_key},
        )
        resp.raise_for_status()
        data = resp.json()
    set_cache(key, json.dumps(data), ttl)
    return data

async def fixtures_for_date(d: date, competition_slug: str) -> list[dict]:
    comp = COMPETITIONS[competition_slug]
    # Ambil tahun berjalan secara dinamis
    season = d.year if d.month >= 7 else d.year - 1
    
    data = await _get("fixtures", {
        "league": comp["api_id"],
        "season": season,
        "date": d.isoformat(),
    }, ttl=6 * 3600)
    return data.get("response", [])

async def team_last_matches(team_id: int, competition_slug: str, n: int = 5) -> list[dict]:
    comp = COMPETITIONS[competition_slug]
    data = await _get("fixtures", {
        "team": team_id, "league": comp["api_id"], "last": n,
    }, ttl=24 * 3600)
    return data.get("response", [])

async def injuries(team_id: int, competition_slug: str) -> list[dict]:
    comp = COMPETITIONS[competition_slug]
    data = await _get("injuries", {
        "team": team_id, "league": comp["api_id"], "season": 2023
    }, ttl=12 * 3600)
    return data.get("response", [])

async def sync_injuries_for_match(team_api_id: int, competition_slug: str) -> list[dict]:
    """Fetch injuries dari API & simpan ke DB."""
    from sqlmodel import Session, text
    from app.storage.db import engine

    injuries_data = await injuries(team_api_id, competition_slug)
    with Session(engine) as s:
        team_row = s.execute(text("select id from teams where api_id = :a"), {"a": team_api_id}).first()
        if not team_row:
            return []
        team_db_id = team_row[0]
        s.execute(text("delete from injuries where team_id = :tid"), {"tid": team_db_id})
        for inj in injuries_data[:20]:
            player = inj.get("player", {})
            s.execute(text("""
                insert into injuries (team_id, player_name, position, status, reason)
                values (:tid, :name, :pos, :st, :rs)
            """), {
                "tid": team_db_id,
                "name": player.get("name", ""),
                "pos": player.get("position", ""),
                "st": "out" if inj.get("type") == "Missing Fixture" else "doubtful",
                "rs": player.get("reason", ""),
            })
        s.commit()
    return injuries_data