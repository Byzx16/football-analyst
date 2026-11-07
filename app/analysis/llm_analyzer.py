import json, re
import google.generativeai as genai
from app.config import settings
from app.analysis.prompt_templates import PRE_MATCH_PROMPT

genai.configure(api_key=settings.gemini_api_key)

# GANTI MENJADI MODEL TERBARU SESUAI SARAN ERROR
_model = genai.GenerativeModel("gemini-3.8-flash") 

def _parse_json(raw: str) -> dict:
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw)

async def analyze_match(match_data: dict) -> dict:
    prompt = PRE_MATCH_PROMPT.format(data_json=json.dumps(match_data, ensure_ascii=False, indent=2))
    resp = _model.generate_content(prompt, generation_config={
        "temperature": 0.2, "response_mime_type": "application/json"
    })
    return _parse_json(resp.text)

# (biarkan fungsi compute_value_bets di bawahnya sama persis seperti sebelumnya)


def compute_value_bets(analysis: dict, market_odds: dict, min_edge: float) -> list[dict]:
    """Bandingkan model prob vs implied prob dari odds."""
    def edge(model_prob, odds):
        if not odds: return None
        return model_prob * odds - 1

    vb = []
    # 1X2
    for sel, key in [("home", "home"), ("draw", "draw"), ("away", "away")]:
        odds = market_odds.get("h2h", {}).get(key)
        prob = analysis["1x2"].get(key, 0)
        e = edge(prob, odds)
        if e is not None and e >= min_edge:
            vb.append({"market": "1x2", "selection": sel, "model_prob": round(prob,3),
                       "implied_prob": round(1/odds,3), "odds": odds, "edge": round(e,3)})
    # Totals
    for label, mkey, okey in [("over_2_5","over","totals_2.5"), ("under_2_5","under","totals_2.5"),
                              ("over_3_5","over","totals_3.5"), ("under_3_5","under","totals_3.5")]:
        odds = market_odds.get("totals", {}).get(okey, {}).get(mkey)
        prob = analysis["totals"].get(label, 0)
        e = edge(prob, odds)
        if e is not None and e >= min_edge:
            vb.append({"market": okey, "selection": mkey, "model_prob": round(prob,3),
                       "implied_prob": round(1/odds,3), "odds": odds, "edge": round(e,3)})
    return sorted(vb, key=lambda x: x["edge"], reverse=True)