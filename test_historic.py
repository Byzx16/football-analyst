import asyncio
from datetime import date, datetime
from app.pipeline import _upsert_fixtures
from app.ingest.api_football import fixtures_for_date
from app.storage.db import engine
from sqlmodel import Session, text

async def main():
    # Kita ambil data tanggal 26 Desember 2023 (Boxing Day) - dijamin ada match PL!
    target_date = date(2023, 12, 26)
    print(f"⏳ Menarik jadwal historis Premier League tanggal {target_date}...")
    
    fixtures = await fixtures_for_date(target_date, 'PL')
    
    if not fixtures:
        print("❌ Tetap kosong. Cek API key atau limit.")
        return
        
    print(f"✅ Dapat {len(fixtures)} match. Menyimpan ke database...")
    _upsert_fixtures(fixtures, 'PL')
    
    with Session(engine) as s:
        res = s.execute(text('SELECT count(*) FROM matches')).first()
        print(f"\n🔍 Total match di database sekarang: {res[0]}")

if __name__ == "__main__":
    asyncio.run(main())