from sqlmodel import Session, text
from app.storage.db import engine

def get_team_form(team_db_id: int, competition_slug: str) -> dict:
    with Session(engine) as s:
        rows = s.execute(text("""
            select
                case
                    when m.home_team_id = :tid and m.home_score > m.away_score then 'W'
                    when m.away_team_id = :tid and m.away_score > m.home_score then 'W'
                    when m.home_score = m.away_score then 'D'
                    else 'L'
                end as result,
                case when m.home_team_id = :tid then m.home_score else m.away_score end as gf,
                case when m.home_team_id = :tid then m.away_score else m.home_score end as ga,
                m.kickoff_at
            from matches m
            where (m.home_team_id = :tid or m.away_team_id = :tid)
              and m.status = 'FT'
              and (m.competition_slug = :slug or :slug = 'ALL')
            order by m.kickoff_at desc
            limit 5
        """), {"tid": team_db_id, "slug": competition_slug}).all()

    if not rows:
        return {"last5": "", "goals_for": 0, "goals_against": 0,
                "wins": 0, "draws": 0, "losses": 0}

    results = [r[0] for r in rows]
    return {
        "last5": "".join(results),
        "goals_for": sum(r[1] for r in rows),
        "goals_against": sum(r[2] for r in rows),
        "wins": results.count("W"),
        "draws": results.count("D"),
        "losses": results.count("L"),
    }


def get_h2h(home_id: int, away_id: int, limit: int = 5) -> list[dict]:
    with Session(engine) as s:
        rows = s.execute(text("""
            select m.kickoff_at, m.home_score, m.away_score,
                   ht.name as home_name, at.name as away_name
            from matches m
            join teams ht on ht.id = m.home_team_id
            join teams at on at.id = m.away_team_id
            where m.status = 'FT'
              and ((m.home_team_id = :h and m.away_team_id = :a)
                or (m.home_team_id = :a and m.away_team_id = :h))
            order by m.kickoff_at desc
            limit :lim
        """), {"h": home_id, "a": away_id, "lim": limit}).all()

    return [
        {"date": r[0].isoformat(), "score": f"{r[1]}-{r[2]}",
         "home": r[3], "away": r[4]}
        for r in rows
    ]

def get_injuries(team_db_id: int) -> list[dict]:
    with Session(engine) as s:
        rows = s.execute(text("""
            select player_name, position, status, reason
            from injuries
            where team_id = :tid and updated_at > now() - interval '3 days'
            order by case status when 'out' then 1 when 'doubtful' then 2 else 3 end
        """), {"tid": team_db_id}).all()
    return [{"player": r[0], "position": r[1], "status": r[2], "reason": r[3]} for r in rows]