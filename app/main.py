from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, text
from app.storage.db import engine
from app.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app):
    start_scheduler()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/matches/today")
def matches_upcoming():
    with Session(engine) as s:
        rows = s.execute(text("""
            select m.id, m.competition_slug, ht.name as home, at.name as away,
                   m.kickoff_at, a.confidence, a.home_win_prob, a.draw_prob, a.away_win_prob,
                   a.predicted_score, a.value_bets
            from matches m
            join teams ht on ht.id = m.home_team_id
            join teams at on at.id = m.away_team_id
            left join analyses a on a.match_id = m.id
            where m.kickoff_at >= current_date
            order by m.kickoff_at
        """)).all()
        return [dict(r._mapping) for r in rows]

@app.get("/api/matches/{match_id}")
def match_detail(match_id: int):
    with Session(engine) as s:
        row = s.execute(text("""
            select m.*, a.* from matches m
            left join analyses a on a.match_id = m.id
            where m.id = :mid
        """), {"mid": match_id}).first()
        return dict(row._mapping) if row else {}

@app.get("/api/value-bets/today")
def value_bets_today():
    with Session(engine) as s:
        rows = s.execute(text("""
            select a.match_id, m.competition_slug, ht.name as home, at.name as away,
                   m.kickoff_at, a.value_bets
            from analyses a
            join matches m on m.id = a.match_id
            join teams ht on ht.id = m.home_team_id
            join teams at on at.id = m.away_team_id
            where m.kickoff_at >= current_date and a.value_bets != '[]'::jsonb
        """)).all()
        return [dict(r._mapping) for r in rows]