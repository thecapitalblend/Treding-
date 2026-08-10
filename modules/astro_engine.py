from datetime import timezone
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
PLANETS = {
    "Sun": swe.SUN if swe else 0,
    "Moon": swe.MOON if swe else 1,
    "Mars": swe.MARS if swe else 4,
    "Mercury": swe.MERCURY if swe else 2,
    "Jupiter": swe.JUPITER if swe else 5,
    "Venus": swe.VENUS if swe else 3,
    "Saturn": swe.SATURN if swe else 6,
}

class CelestialEngine:
    """Experimental Vedic-finance research layer. Not a validated predictor."""

    def _jd(self, dt):
        dt = dt.replace(tzinfo=dt.tzinfo or timezone.utc).astimezone(timezone.utc)
        return swe.julday(dt.year, dt.month, dt.day,
                          dt.hour + dt.minute/60 + dt.second/3600)

    def _calc(self, jd, pid):
        pos, ret = swe.calc_ut(jd, pid)
        return float(pos[0] % 360), float(pos[3])

    def analyze(self, dt):
        if swe is None:
            return {"score": 0, "moon_longitude": 0, "nakshatra": "Unavailable",
                    "moon_sign": "Unavailable", "tithi": 0, "retrograde": [],
                    "planets": {}, "sbc": "Unavailable"}

        jd = self._jd(dt)
        vals, speeds = {}, {}
        for name, pid in PLANETS.items():
            vals[name], speeds[name] = self._calc(jd, pid)

        moon = vals["Moon"]
        nak_span = 360 / 27
        nak_idx = min(26, int(moon / nak_span))
        nak = NAKSHATRAS[nak_idx]
        sign = SIGNS[int(moon // 30)]

        sun_moon_diff = (moon - vals["Sun"]) % 360
        tithi = sun_moon_diff / 12 + 1
        retro = [n for n in ("Mars","Mercury","Jupiter","Venus","Saturn") if speeds[n] < 0]

        score = 0.0
        # Small experimental confluence score only.
        for name in ("Jupiter","Venus"):
            sep = abs((vals[name] - moon + 180) % 360 - 180)
            if sep <= 15: score += 8
        for name in ("Mars","Saturn"):
            sep = abs((vals[name] - moon + 180) % 360 - 180)
            if sep <= 15: score -= 8

        # Experimental "SBC pressure" proxy: clusters near Moon.
        malefic_near = sum(
            abs((vals[n] - moon + 180) % 360 - 180) <= 30
            for n in ("Mars","Saturn")
        )
        benefic_near = sum(
            abs((vals[n] - moon + 180) % 360 - 180) <= 30
            for n in ("Jupiter","Venus")
        )
        score += (benefic_near - malefic_near) * 3

        return {
            "score": int(max(-30, min(30, round(score)))),
            "moon_longitude": moon,
            "nakshatra": nak,
            "moon_sign": sign,
            "tithi": tithi,
            "retrograde": retro,
            "planets": vals,
            "planet_speeds": speeds,
            "sbc": {
                "nakshatra_index": nak_idx + 1,
                "benefic_pressure": benefic_near,
                "malefic_pressure": malefic_near,
                "vedha_proxy": "BENEFIC" if benefic_near > malefic_near else
                               "MALEFIC" if malefic_near > benefic_near else "NEUTRAL"
            }
        }
