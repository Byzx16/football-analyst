from datetime import date, datetime, timedelta
import pytz
from app.config import COMPETITIONS, settings
from app.ingest import api_football, odds
from app.analysis.llm_analyzer import analyze_match, compute_value_bets
from app.analysis.prompt_templates import build_match_data
from app.storage.db import engine
from sqlmodel import Session, text
from app.utils.form import get_team_form, get_h2h, get_injuries
from app.ingest.news_rss import fetch_team_news

WIB = pytz.timezone("Asia/Jakarta")

async def sync_all_fixtures():
    """Fetch fixtures hari ini + besok untuk semua kompetisi. Simpan ke DB."""
    today = datetime.now(WIB).date()
    for slug in COMPETITIONS:
        for d in [today, today + timedelta(days=1)]:
            fixtures = await api_football.fixtures_for_date(d, slug)
            _upsert_fixtures(fixtures, slug)
        print(f"[sync] {slug}: done")

def _upsert_fixtures(fixtures, slug):
    with Session(engine) as s:
        for f in fixtures:
            home = f["teams"]["home"]; away = f["teams"]["away"]
            # upsert teams
            s.execute(text("""
                insert into teams (api_id, name, logo_url)
                values (:aid, :name, :logo)
                on conflict (api_id) do update set name=excluded.name, logo_url=excluded.logo_url
            """), {"aid": home["id"], "name": home["name"], "logo": home["logo"]})
            
            s.execute(text("""
                insert into teams (api_id, name, logo_url)
                values (:aid, :name, :logo)
                on conflict (api_id) do update set name=excluded.name, logo_url=excluded.logo_url
            """), {"aid": away["id"], "name": away["name"], "logo": away["logo"]})
            
            home_db = s.execute(text("select id from teams where api_id=:a"), {"a": home["id"]}).first()
            away_db = s.execute(text("select id from teams where api_id=:a"), {"a": away["id"]}).first()
            
            s.execute(text("""
                insert into matches (api_id, competition_slug, home_team_id, away_team_id, kickoff_at, status)
                values (:aid, :slug, :h, :a, :ko, :st)
                on conflict (api_id) do update set
                  status=excluded.status, kickoff_at=excluded.kickoff_at
            """), {
                "aid": f["fixture"]["id"], "slug": slug,
                "h": home_db[0], "a": away_db[0],
                "ko": f["fixture"]["date"], "st": f["fixture"]["status"]["short"],
            })
        s.commit()


async def run_pre_match_pipeline(competition_slug: str):
    """
    Analisa semua match kompetisi ini yang kickoff dalam 24 jam ke depan.
    """
    with Session(engine) as s:
        rows = s.execute(text("""
            select id, api_id, home_team_id, away_team_id, kickoff_at
            from matches
            where competition_slug = :slug
              and kickoff_at between now() and now() + interval '24 hours'
              and status = 'NS'
        """), {"slug": competition_slug}).all()

    if not rows:
        print(f"[{competition_slug}] Tidak ada match dalam 24 jam ke depan.")
        return

    # Ambil odds sekali untuk semua match kompetisi ini (1 call)
    odds_data = await odds.fetch_odds_for_competition(competition_slug)
    odds_by_teams = _index_odds_by_teams(odds_data)

    for row in rows:
        match_id, api_id, h_id, a_id, ko = row
        # Kumpulkan data
        h_form = await _get_form(h_id, competition_slug)
        a_form = await _get_form(a_id, competition_slug)
        h_inj  = await _get_injuries(h_id, competition_slug)
        a_inj  = await _get_injuries(a_id, competition_slug)
        h2h    = await _get_h2h(h_id, a_id)
        h_news = _get_news(h_id)
        a_news = _get_news(a_id)

        # Lookup odds untuk match ini
        key = (str(h_id), str(a_id))
        m_odds = odds_by_teams.get(key, {})

        data = build_match_data(
            match={"competition_slug": competition_slug, "home_team": h_id,
                   "away_team": a_id, "kickoff_wib": str(ko)},
            home_form=h_form, away_form=a_form,
            injuries_home=h_inj, injuries_away=a_inj,
            h2h=h2h, news_home=h_news, news_away=a_news, odds=m_odds,
        )

        try:
            print(f"⏳ Menganalisa match ID {match_id}...")
            analysis = await analyze_match(data)
        except Exception as e:
            print(f"[analysis fail] match {match_id}: {e}")
            continue

        value_bets = compute_value_bets(analysis, m_odds, settings.value_bet_min_edge)
        _save_analysis(match_id, analysis, value_bets)
        print(f"[ok] match {match_id} analyzed, {len(value_bets)} value bets ditemukan!")


def _index_odds_by_teams(odds_data):
    """Convert Odds API list -> dict keyed by (home,away) -> market odds."""
    indexed = {}
    for m in odds_data:
        key = (m["home_team"].lower(), m["away_team"].lower())
        markets = {"h2h": {}, "totals": {}, "spreads": {}}
        for bm in m.get("bookmakers", [])[:3]:
            for market in bm.get("markets", []):
                if market["key"] == "h2h":
                    for o in market["outcomes"]:
                        markets["h2h"].setdefault(o["name"].lower(), o["price"])
                elif market["key"] == "totals":
                    for o in market["outcomes"]:
                        pt = o.get("point")
                        if pt == 2.5: markets["totals"].setdefault(f"totals_2.5", {})[o["name"].lower()] = o["price"]
                        if pt == 3.5: markets["totals"].setdefault(f"totals_3.5", {})[o["name"].lower()] = o["price"]
        indexed[key] = markets
    return indexed


def _save_analysis(match_id, a, value_bets):
    import json
    with Session(engine) as s:
        s.execute(text("""
            insert into analyses (
                match_id, model, home_win_prob, draw_prob, away_win_prob,
                predicted_score, over_25_prob, under_25_prob, over_35_prob, under_35_prob,
                handicap_line, handicap_side, value_bets, key_factors, risks,
                news_summary, injury_impact, confidence
            ) values (
                :mid, 'gemini-3.8-flash', :hw, :dr, :aw, :ps,
                :o25, :u25, :o35, :u35, :hl, :hs, :vb, :kf, :rk, :ns, :ii, :cf
            )
        """), {
            "mid": match_id, "hw": a["1x2"]["home"], "dr": a["1x2"]["draw"], "aw": a["1x2"]["away"],
            "ps": a["predicted_score"],
            "o25": a["totals"]["over_2_5"], "u25": a["totals"]["under_2_5"],
            "o35": a["totals"]["over_3_5"], "u35": a["totals"]["under_3_5"],
            "hl": a["handicap"]["line"], "hs": a["handicap"]["side"],
            "vb": json.dumps(value_bets), "kf": json.dumps(a["key_factors"]),
            "rk": json.dumps(a["risks"]), "ns": a["news_summary"],
            "ii": a["injury_impact"], "cf": a["confidence"],
        })
        s.commit()


# Ambil data pendukung
async def _get_form(team_id, slug):
    return get_team_form(team_id, slug)

async def _get_injuries(team_id, slug):
    return get_injuries(team_id)

async def _get_h2h(h, a):
    return get_h2h(h, a)

def _get_news(team_id):
    with Session(engine) as s:
        row = s.execute(text("select name from teams where id = :tid"), {"tid": team_id}).first()
    if not row:
        return []
    return fetch_team_news(row[0])