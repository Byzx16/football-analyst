from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_football_key: str
    api_football_base: str = "https://v3.football.api-sports.io"
    odds_api_key: str
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    gemini_api_key: str
    database_url: str
    redis_url: str
    value_bet_min_edge: float = 0.05

    class Config:
        env_file = ".env"

settings = Settings()

# Mapping kompetisi -> API-Football league ID & Odds API sport key
COMPETITIONS = {
    "PL":    {"api_id": 39,  "odds_key": "soccer_epl",                 "type": "domestic_weekend"},
    "PD":    {"api_id": 140, "odds_key": "soccer_spain_la_liga",       "type": "domestic_weekend"},
    "SA":    {"api_id": 135, "odds_key": "soccer_italy_serie_a",       "type": "domestic_weekend"},
    "BL1":   {"api_id": 78,  "odds_key": "soccer_germany_bundesliga",  "type": "domestic_weekend"},
    "FL1":   {"api_id": 61,  "odds_key": "soccer_france_ligue_one",    "type": "domestic_weekend"},
    "UCL":   {"api_id": 2,   "odds_key": "soccer_uefa_champs_league",  "type": "european"},
    "UEL":   {"api_id": 3,   "odds_key": "soccer_uefa_europa_league",  "type": "european"},
    "UECL":  {"api_id": 848, "odds_key": "soccer_uefa_europa_conference_league", "type": "european"},
}