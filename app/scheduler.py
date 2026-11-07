import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app.config import COMPETITIONS

WIB = pytz.timezone("Asia/Jakarta")
scheduler = AsyncIOScheduler(timezone=WIB)

async def _run_analysis_for(competition_slugs: list[str], label: str):
    from app.pipeline import run_pre_match_pipeline  # dijelaskan di bawah
    print(f"[{datetime.now(WIB)}] Running {label}: {competition_slugs}")
    for slug in competition_slugs:
        await run_pre_match_pipeline(slug)

# Weekend domestik — Sabtu & Minggu 15:00 WIB
async def weekend_domestic():
    await _run_analysis_for(["PL","PD","SA","BL1","FL1"], "weekend-domestic")

# European nights — Selasa, Rabu (UCL), Kamis (UEL/UECL) 21:00 WIB
async def ucl_analysis():
    await _run_analysis_for(["UCL"], "ucl")

async def uel_uecl_analysis():
    await _run_analysis_for(["UEL","UECL"], "uel-uecl")

# Sync fixtures tiap hari 06:00 & 12:00 WIB
async def sync_fixtures():
    from app.pipeline import sync_all_fixtures
    await sync_all_fixtures()

def start_scheduler():
    scheduler.add_job(sync_fixtures, CronTrigger(hour="6,12", minute=0))
    scheduler.add_job(weekend_domestic, CronTrigger(day_of_week="sat,sun", hour=15, minute=0))
    scheduler.add_job(ucl_analysis, CronTrigger(day_of_week="tue,wed", hour=21, minute=0))
    scheduler.add_job(uel_uecl_analysis, CronTrigger(day_of_week="thu", hour=21, minute=0))
    scheduler.start()