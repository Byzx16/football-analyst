import asyncio
import httpx
from datetime import date, timedelta
from app.config import settings

async def main():
    today = date.today()
    # Hitung season (misal: Agustus 2024 - Juli 2025 = season 2024)
    season = today.year if today.month >= 7 else today.year - 1
    
    print(f"📅 Hari ini: {today}")
    print(f"📅 Season yang dipakai: {season}")
    print(f"🔑 API Key (4 huruf pertama): {settings.api_football_key[:4]}...")
    
    headers = {"x-apisports-key": settings.api_football_key}
    
    async with httpx.AsyncClient() as client:
        # Cek match Premier League hari ini
        print("\n1️⃣ Cek Match Premier League HARI INI:")
        resp = await client.get(
            f"{settings.api_football_base}/fixtures",
            params={"league": 39, "season": season, "date": today.isoformat()},
            headers=headers
        )
        data = resp.json()
        print(f"   Error dari API: {data.get('errors')}")
        print(f"   Jumlah Match: {data.get('results')}")
        
        # Cek match Premier League 7 hari ke depan (pakai parameter 'next')
        print("\n2️⃣ Cek 10 Match Premier League BERIKUTNYA:")
        resp = await client.get(
            f"{settings.api_football_base}/fixtures",
            params={"league": 39, "season": season, "next": 10},
            headers=headers
        )
        data = resp.json()
        print(f"   Error dari API: {data.get('errors')}")
        print(f"   Jumlah Match: {data.get('results')}")
        
        if data.get('results', 0) > 0:
            first = data['response'][0]
            print(f"   ✅ Match terdekat: {first['teams']['home']['name']} vs {first['teams']['away']['name']} pada {first['fixture']['date']}")
        else:
            print("   ❌ API tidak mengembalikan match sama sekali.")

if __name__ == "__main__":
    asyncio.run(main())