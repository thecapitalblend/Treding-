from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni",
    "Uttara Phalguni","Hasta","Chitra","Swati","Vishakha",
    "Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha",
    "Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati"
]

@dataclass
class PlanetPosition:
    name: str
    longitude: float
    zodiac: str
    nakshatra: str
    retrograde: bool

class CelestialEngine:
    """Astronomical positions plus an explicitly configurable research score.

    SBC and Ashtakavarga interpretations are kept as a separate research layer.
    This avoids presenting one particular tradition/implementation as universally
    defined.
    """

    PLANETS = {"Sun":0, "Moon":1, "Mercury":2, "Venus":3, "Mars":4, "Jupiter":5, "Saturn":6, "Rahu":10}

    def __init__(self):
        try:
            import swisseph as swe
            self.swe = swe
            self.available = True
        except Exception:
            self.swe = None
            self.available = False

    def _jd(self, dt):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        u = dt.astimezone(timezone.utc)
        return self.swe.julday(u.year, u.month, u.day, u.hour + u.minute/60 + u.second/3600)

    @staticmethod
    def _zodiac(lon):
        return ZODIACS[int(lon // 30) % 12]

    @staticmethod
    def _nakshatra(lon):
        return NAKSHATRAS[int(lon / (360/27)) % 27]

    def planetary_positions(self, dt):
        if not self.available:
            return {}
        jd = self._jd(dt)
        out = {}
        for name, planet_id in self.PLANETS.items():
            try:
                pos, _ = self.swe.calc_ut(jd, planet_id)
                lon = float(pos[0] % 360)
                speed = float(pos[3]) if len(pos) > 3 else 0.0
                out[name] = PlanetPosition(
                    name, lon, self._zodiac(lon), self._nakshatra(lon), speed < 0
                )
            except Exception:
                continue
        return out

    def research_score(self, dt):
        positions = self.planetary_positions(dt)
        if not positions:
            return {"score":0.0, "label":"UNAVAILABLE", "positions":{}, "notes":[]}

        score = 0.0
        notes = []
        positive_nakshatras = {"Ashwini","Rohini","Pushya","Anuradha","Revati"}
        benefics = {"Jupiter","Venus","Mercury","Moon"}
        malefics = {"Saturn","Mars","Sun","Rahu"}

        for name, p in positions.items():
            if p.nakshatra in positive_nakshatras:
                if name in benefics:
                    score += 8; notes.append(f"{name} research factor +8")
                elif name in malefics:
                    score -= 8; notes.append(f"{name} research factor -8")
            if p.retrograde and name in {"Mars","Saturn","Mercury"}:
                score -= 3; notes.append(f"{name} retrograde adjustment -3")

        score = max(-100, min(100, score))
        label = "BULLISH" if score >= 20 else "BEARISH" if score <= -20 else "NEUTRAL"
        return {"score":float(score), "label":label, "positions":positions, "notes":notes}
