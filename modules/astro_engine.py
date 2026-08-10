from datetime import datetime, timezone
import math

try:
    import swisseph as swe
except Exception:
    swe = None

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati"
]
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
         "Sagittarius","Capricorn","Aquarius","Pisces"]

class CelestialEngine:
    """
    Research-only celestial layer.
    Calculates Swiss Ephemeris planetary longitudes and Moon nakshatra.
    The SBC score is a simplified computational research heuristic, not a
    claim of canonical classical SBC implementation or predictive validity.
    """
    def __init__(self):
        if swe is not None:
            try:
                swe.set_ephe_path("")
            except Exception:
                pass

    def _jd(self, dt):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return swe.julday(dt.year, dt.month, dt.day,
                          dt.hour + dt.minute/60 + dt.second/3600)

    def _planet(self, jd, pid):
        pos, _ = swe.calc_ut(jd, pid)
        return float(pos[0] % 360)

    def analyze(self, dt):
        if swe is None:
            return {
                "score": 0, "moon_longitude": 0.0,
                "nakshatra": "Unavailable", "moon_sign": "Unavailable",
                "planets": {}
            }

        jd = self._jd(dt)
        moon = self._planet(jd, swe.MOON)
        planets = {
            "Sun": self._planet(jd, swe.SUN),
            "Moon": moon,
            "Mars": self._planet(jd, swe.MARS),
            "Mercury": self._planet(jd, swe.MERCURY),
            "Jupiter": self._planet(jd, swe.JUPITER),
            "Venus": self._planet(jd, swe.VENUS),
            "Saturn": self._planet(jd, swe.SATURN),
        }

        nak_span = 360 / 27
        idx = min(26, int(moon / nak_span))
        nak = NAKSHATRAS[idx]
        sign = SIGNS[int(moon // 30)]

        # Research heuristic: benefic proximity to Moon gets positive points;
        # malefic proximity gets negative points. This is intentionally modest.
        score = 0.0
        for name in ("Jupiter", "Venus", "Mercury"):
            sep = abs((planets[name] - moon + 180) % 360 - 180)
            if sep <= 15:
                score += 10
        for name in ("Mars", "Saturn"):
            sep = abs((planets[name] - moon + 180) % 360 - 180)
            if sep <= 15:
                score -= 10

        return {
            "score": max(-30, min(30, score)),
            "moon_longitude": moon,
            "nakshatra": nak,
            "moon_sign": sign,
            "planets": planets,
        }
