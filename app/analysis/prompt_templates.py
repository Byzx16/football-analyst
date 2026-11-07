PRE_MATCH_PROMPT = """Kamu adalah analis sepakbola profesional. Analisa match berikut berdasarkan DATA JSON yang diberikan.

ATURAN KERAS:
- HANYA gunakan data dari JSON. JANGAN mengarang statistik, injury, atau berita.
- Jika data kurang, tulis "data terbatas" dan turunkan confidence.
- Probabilitas harus berjumlah 100% untuk 1X2, over+under harus 100%.
- Handicap line dipilih dari: -1.5, -1.0, -0.75, -0.5, -0.25, 0, +0.25, +0.5, +0.75, +1.0, +1.5 (dari sisi home).

DATA:
{data_json}

Output HARUS valid JSON saja (tanpa markdown fence), dengan skema:
{{
  "predicted_score": "2-1",
  "1x2": {{"home": 0.52, "draw": 0.26, "away": 0.22}},
  "totals": {{
    "over_2_5": 0.61, "under_2_5": 0.39,
    "over_3_5": 0.34, "under_3_5": 0.66
  }},
  "handicap": {{
    "line": -0.5,
    "side": "home",
    "prob": 0.55,
    "reasoning": "singkat"
  }},
  "key_factors": ["faktor 1", "faktor 2", "faktor 3"],
  "risks": ["risiko 1", "risiko 2"],
  "news_summary": "ringkasan 2-3 kalimat",
  "injury_impact": "dampak 1-2 kalimat",
  "confidence": "low|medium|high"
}}"""


def build_match_data(match, home_form, away_form, injuries_home, injuries_away,
                     h2h, news_home, news_away, odds) -> dict:
    """Bangun dict terstruktur untuk di-feed ke LLM."""
    return {
        "match": {
            "competition": match["competition_slug"],
            "home_team": match["home_team"],
            "away_team": match["away_team"],
            "kickoff_wib": match["kickoff_wib"],
        },
        "form": {
            "home": home_form,   # {last5, goals_for, goals_against, xg_for, xg_against}
            "away": away_form,
        },
        "injuries": {
            "home": injuries_home,   # [{player, position, status, reason}]
            "away": injuries_away,
        },
        "h2h_last5": h2h,            # [{date, score, home, away}]
        "news": {
            "home": news_home[:5],   # [{title, summary, sentiment}]
            "away": news_away[:5],
        },
        "market_odds": odds,         # {h2h: {home,draw,away}, totals: {...}, spreads: {...}}
    }