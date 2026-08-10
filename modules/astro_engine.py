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
    "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati"
]
SIGNS = ["Mesha","Vrishabha","Mithuna","Karka","Simha","Kanya","Tula","Vrishchika","Dhanu","Makara","Kumbha","Meena"]
PLANETS = {
    "Sun": 0, "Moon": 1, "Mercury": 2, "Venus": 3, "Mars": 4,
    "Jupiter": 5, "Saturn": 6, "Rahu": 10, "Ketu": 11
}

class CelestialEngine:
    def calculate(self, dt):
        base = {
            "score": 0.0, "moon_longitude": float("nan"),
            "moon_sign": "Unavailable", "nakshatra": "Unavailable",
            "tithi_number": float("nan"), "tithi_name": "Unavailable",
            "retrograde": "None"
        }
        if swe is None:
            return base

        try:
            jd = swe.julday(dt.year, dt.month, dt.day,
                            dt.hour + dt.minute/60 + dt.second/3600)

            # Lahiri sidereal zodiac
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

            positions = {}
            for name, body in PLANETS.items():
                xx, _ = swe.calc_ut(jd, body, flags)
                positions[name] = xx

            sun = positions["Sun"][0] % 360
            moon = positions["Moon"][0] % 360

            sign_idx = int(moon // 30)
            nak_idx = int(moon // (360/27))
            elong = (moon - sun) % 360
            tithi_num = int(elong // 12) + 1

            paksha = "Shukla" if tithi_num <= 15 else "Krishna"
            tithi_day = tithi_num if tithi_num <= 15 else tithi_num - 15
            tithi_names = [
                "Pratipada","Dvitiya","Tritiya","Chaturthi","Panchami","Shashthi",
                "Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi",
                "Trayodashi","Chaturdashi","Purnima"
            ]
            tname = f"{paksha} {tithi_names[tithi_day-1]}"

            retro = []
            for name in ["Mercury","Venus","Mars","Jupiter","Saturn"]:
                if positions[name][3] < 0:
                    retro.append(name)

            # Experimental score: tiny bounded research signal, never dominant.
            score = 0
            if sign_idx in (0, 4, 8):
                score += 2
            elif sign_idx in (2, 5, 10):
                score -= 2
            if retro:
                score -= min(3, len(retro))

            return {
                "score": float(score),
                "moon_longitude": moon,
                "moon_sign": SIGNS[sign_idx],
                "nakshatra": NAKSHATRAS[nak_idx],
                "tithi_number": float(tithi_num),
                "tithi_name": tname,
                "retrograde": ", ".join(retro) if retro else "None"
            }
        except Exception:
            return base
