#!/usr/bin/env python3
"""
neighborhood-report-ai — address → AI-compiled neighborhood report
Schools, safety, transport, amenities, price trends, demographics,
noise levels, flood risk, development plans, walkability
"""
import anthropic, json, re, sys, urllib.request, urllib.parse

SYSTEM = """You are a real estate analyst and urban researcher with access to
comprehensive neighborhood data. Generate a detailed, balanced neighborhood report.

Be objective — include both positives and negatives. Don't oversell or undersell.
Acknowledge when data is limited or approximate.

Return ONLY valid JSON — no markdown, no explanation.

{
  "address": "string",
  "neighborhood": "neighborhood name",
  "city": "string",
  "country": "string",
  "report_date": "YYYY-MM",
  "overall_score": number_0_to_100,
  "overall_grade": "A|B|C|D|F",
  "summary": "3-4 sentence balanced summary of the neighborhood",
  "scores": {
    "safety": number_0_to_10,
    "schools": number_0_to_10,
    "transport": number_0_to_10,
    "amenities": number_0_to_10,
    "walkability": number_0_to_10,
    "noise_level": number_0_to_10,
    "green_space": number_0_to_10,
    "property_value_trend": number_0_to_10,
    "community_vibe": number_0_to_10
  },
  "safety": {
    "overall_assessment": "safe|generally_safe|mixed|caution_advised|high_risk",
    "crime_level": "low|below_average|average|above_average|high",
    "crime_types_noted": ["list of common crime types if any"],
    "police_presence": "high|moderate|low",
    "safety_notes": ["specific safety observations"],
    "improving_or_declining": "improving|stable|declining|unknown"
  },
  "schools": {
    "public_school_quality": "excellent|good|average|below_average|poor",
    "notable_schools": ["school names and types if known"],
    "school_distance": "walking|short_drive|drive_required",
    "private_options": true_or_false,
    "university_proximity": "string or null"
  },
  "transport": {
    "car_dependency": "low|moderate|high|essential",
    "public_transit": "excellent|good|limited|poor|none",
    "transit_options": ["metro","bus","tram","train","ferry"],
    "walkability_score": "very_walkable|walkable|car_friendly|car_dependent",
    "cycling": "good|moderate|poor",
    "highway_access": "excellent|good|moderate|difficult",
    "airport_distance": "string or null"
  },
  "amenities": {
    "grocery_stores": "walkable|short_drive|drive_required",
    "restaurants": "abundant|moderate|limited",
    "healthcare": "hospital_nearby|clinic_nearby|limited",
    "parks_green_space": "abundant|moderate|limited|none",
    "entertainment": "abundant|moderate|limited",
    "shopping": "abundant|moderate|limited",
    "notable_amenities": ["specific places worth mentioning"]
  },
  "property_market": {
    "price_trend_1yr": "rising_fast|rising|stable|declining|unknown",
    "price_trend_5yr": "string",
    "average_price_indicator": "affordable|mid_range|premium|luxury",
    "rental_market": "high_demand|balanced|oversupply|unknown",
    "gentrification_stage": "early|mid|advanced|stable|not_gentrifying|unknown",
    "development_activity": "high|moderate|low"
  },
  "environment": {
    "flood_risk": "low|moderate|high|very_high|unknown",
    "air_quality": "excellent|good|moderate|poor",
    "noise_sources": ["traffic","airport","railway","nightlife","construction"],
    "green_coverage": "high|moderate|low"
  },
  "demographics": {
    "population_density": "dense_urban|urban|suburban|low_density",
    "age_mix": "young_professionals|families|mixed|retirees|students",
    "diversity": "highly_diverse|diverse|moderate|homogeneous",
    "community_character": ["artsy","family_oriented","professional","multicultural","historic"]
  },
  "pros": ["top 4-5 genuine positives"],
  "cons": ["top 3-4 genuine negatives — be honest"],
  "ideal_for": ["young professionals","families with kids","retirees","students","investors"],
  "not_ideal_for": ["who would not enjoy this neighborhood"],
  "upcoming_developments": ["known planned projects that could affect the area"],
  "data_limitations": ["what we don't know or couldn't verify"],
  "confidence": 0.0
}"""

def generate_report(address: str, focus: str = "") -> dict:
    client = anthropic.Anthropic()
    prompt = f"Generate a neighborhood report for: {address}"
    if focus: prompt += f"\nFocus area: {focus}"
    prompt += "\n\nUse your knowledge of this location. Be specific, accurate, and balanced."

    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=3000, system=SYSTEM,
        messages=[{"role":"user","content":prompt}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

GRADE_C = {"A":"\033[92m","B":"\033[92m","C":"\033[93m","D":"\033[91m","F":"\033[91m"}
R = "\033[0m"

def score_bar(score: float, max_val: float = 10.0) -> str:
    filled = int((score / max_val) * 10)
    return "█"*filled + "░"*(10-filled)

def print_report(r: dict):
    scores = r.get("scores",{})
    grade = r.get("overall_grade","?")
    overall = r.get("overall_score",0)
    safety = r.get("safety",{})
    transport = r.get("transport",{})
    market = r.get("property_market",{})
    env = r.get("environment",{})

    print(f"\n{'═'*60}")
    print(f"  NEIGHBORHOOD REPORT — {r.get('neighborhood','?')}, {r.get('city','?')}")
    print(f"  Overall: {GRADE_C.get(grade,'')}{grade}{R} ({overall}/100)")
    print(f"{'═'*60}")
    print(f"\n  {r.get('summary','')}")

    print(f"\n  SCORES")
    for key, label in [("safety","Safety"),("schools","Schools"),("transport","Transport"),
                        ("amenities","Amenities"),("walkability","Walkability"),
                        ("noise_level","Quiet/noise"),("green_space","Green space"),
                        ("property_value_trend","Price trend"),("community_vibe","Community")]:
        s = scores.get(key, 0)
        print(f"  {label:<20} {score_bar(s)} {s}/10")

    print(f"\n  Safety: {safety.get('overall_assessment','?').replace('_',' ')} | Crime: {safety.get('crime_level','?')}")
    if safety.get("improving_or_declining") and safety["improving_or_declining"] != "unknown":
        print(f"  Trend: {safety['improving_or_declining']}")

    print(f"\n  Transport: {transport.get('car_dependency','?').replace('_',' ')} on car | Transit: {transport.get('public_transit','?')}")
    print(f"  Walk: {transport.get('walkability_score','?').replace('_',' ')}")

    print(f"\n  Property: {market.get('average_price_indicator','?').replace('_',' ')} | Trend 1yr: {market.get('price_trend_1yr','?').replace('_',' ')}")
    print(f"  Rental demand: {market.get('rental_market','?').replace('_',' ')}")

    if env.get("flood_risk") and env["flood_risk"] not in ("low","unknown"):
        print(f"\n  ⚠ Flood risk: {env['flood_risk']}")
    if env.get("noise_sources"):
        print(f"  Noise: {', '.join(env['noise_sources'])}")

    pros = r.get("pros",[])
    cons = r.get("cons",[])
    if pros:
        print(f"\n  PROS")
        for p in pros: print(f"  ✅ {p}")
    if cons:
        print(f"\n  CONS")
        for c in cons: print(f"  ⚠ {c}")

    ideal = r.get("ideal_for",[])
    not_ideal = r.get("not_ideal_for",[])
    if ideal: print(f"\n  Best for: {', '.join(ideal)}")
    if not_ideal: print(f"  Not for: {', '.join(not_ideal)}")

    upcoming = r.get("upcoming_developments",[])
    if upcoming:
        print(f"\n  UPCOMING DEVELOPMENTS")
        for u in upcoming: print(f"  🏗 {u}")

    limits = r.get("data_limitations",[])
    if limits: print(f"\n  ℹ Data limitations: {'; '.join(limits[:2])}")
    print(f"  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate AI neighborhood report for any address")
    p.add_argument("address", help="Full address or neighborhood name")
    p.add_argument("--focus","-f",default="",help="Focus area (e.g. 'families','commuters','investors')")
    p.add_argument("--json",action="store_true")
    a = p.parse_args()
    r = generate_report(a.address, a.focus)
    if a.json: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_report(r)
