import asyncio
from app.pipeline import sync_all_fixtures
from app.storage.db import engine
from sqlmodel import Session, text

async def main():
    print("⏳ Menarik jadwal dari API...")
    await sync_all_fixtures()
    
    print("\n🔍 Cek Database:")
    with Session(engine) as s:
        res = s.execute(text('SELECT count(*) FROM matches')).first()
        print(f"Total match di database: {res[0]}")
        
        if res[0] > 0:
            print("\n3 Match Terdekat:")
            upcoming = s.execute(text('SELECT home_team_id, away_team_id, kickoff_at FROM matches ORDER BY kickoff_at ASC LIMIT 3')).all()
            for u in upcoming: 
                print(f"- Match ID {u[0]} vs {u[1]} | Kickoff: {u[2]}")

if __name__ == "__main__":
    asyncio.run(main())