import asyncio
from app.pipeline import run_pre_match_pipeline
from app.storage.db import engine
from sqlmodel import Session, text
from datetime import datetime, timedelta
import pytz

async def main():
    # Trik: Ubah tanggal match di DB jadi "besok" biar dibaca sama pipeline
    print("⏳ Mengakali waktu match agar dibaca sebagai 'besok'...")
    with Session(engine) as s:
        # Ambil 1 match PL pertama
        match = s.execute(text("SELECT id FROM matches WHERE competition_slug='PL' LIMIT 1")).first()
        if not match:
            print("❌ Belum ada match di DB.")
            return
        mid = match[0]
        
        besok = datetime.now(pytz.timezone("Asia/Jakarta")) + timedelta(days=1)
        s.execute(text("UPDATE matches SET kickoff_at = :t WHERE id = :id"), {"t": besok, "id": mid})
        s.commit()
        print(f"✅ Match ID {mid} berhasil diatur ke besok.")

    print("\n🤖 Memulai analisa AI...")
    await run_pre_match_pipeline('PL')

if __name__ == "__main__":
    asyncio.run(main())