import asyncio
from datetime import datetime, timedelta
import pytz
from sqlmodel import Session, text
from app.storage.db import engine

async def main():
    print("💉 Menyuntikkan data simulasi ke database...")
    with Session(engine) as s:
        # 1. Daftarkan Liga (WAJIB DULU)
        s.execute(text("""
            INSERT INTO competitions (slug, name, type)
            VALUES ('PL', 'Premier League', 'domestic_weekend')
            ON CONFLICT (slug) DO NOTHING;
        """))

        # 2. Buat Tim Fiktif (Arsenal vs Man City)
        s.execute(text("""
            INSERT INTO teams (api_id, name, logo_url) 
            VALUES (9991, 'Arsenal', 'https://media.api-sports.io/football/teams/42.png'),
                   (9992, 'Manchester City', 'https://media.api-sports.io/football/teams/50.png')
            ON CONFLICT (api_id) DO NOTHING;
        """))
        
        # Ambil ID database mereka
        home_id = s.execute(text("SELECT id FROM teams WHERE api_id = 9991")).first()[0]
        away_id = s.execute(text("SELECT id FROM teams WHERE api_id = 9992")).first()[0]

        # 3. Buat Match (Besok jam 20:00 WIB)
        besok = datetime.now(pytz.timezone("Asia/Jakarta")) + timedelta(days=1)
        besok = besok.replace(hour=20, minute=0, second=0, microsecond=0)
        
        s.execute(text("""
            INSERT INTO matches (api_id, competition_slug, home_team_id, away_team_id, kickoff_at, status)
            VALUES (8881, 'PL', :h, :a, :ko, 'NS')
            ON CONFLICT (api_id) DO NOTHING;
        """), {"h": home_id, "a": away_id, "ko": besok})
        
        s.commit()
        
        # Cek hasil
        count = s.execute(text("SELECT count(*) FROM matches")).first()[0]
        print(f"✅ Berhasil! Total match di database sekarang: {count}")
        print(f"✅ Match Arsenal vs Man City dijadwalkan pada: {besok}")

if __name__ == "__main__":
    asyncio.run(main())