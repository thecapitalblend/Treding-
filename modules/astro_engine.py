
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import math

try:
    import swisseph as swe
except Exception:
    swe = None

IST = ZoneInfo("Asia/Kolkata")

SIGNS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

TITHI_NAMES = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
    "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
    "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti"
]

KARANA_FIXED = {
    1: "Kimstughna",
    58: "Shakuni",
    59: "Chatushpada",
    60: "Naga",
}
KARANA_MOVING = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"
]

PLANET_BODIES = {
    "Sun": swe.SUN if swe else 0,
    "Moon": swe.MOON if swe else 1,
    "Mercury": swe.MERCURY if swe else 2,
    "Venus": swe.VENUS if swe else 3,
    "Mars": swe.MARS if swe else 4,
    "Jupiter": swe.JUPITER if swe else 5,
    "Saturn": swe.SATURN if swe else 6,
}

# Mean lunar node is the standard stable choice for a transit research layer.
NODE_BODY = swe.MEAN_NODE if swe else 10

# Compact research weights. These are intentionally transparent and bounded.
PLANET_RESEARCH_WEIGHTS = {
    "Sun": 0.4,
    "Moon": 1.0,
    "Mercury": 0.5,
    "Venus": 0.4,
    "Mars": -0.6,
    "Jupiter": 0.8,
    "Saturn": -0.8,
}

class CelestialEngine:
    """
    Real-time Vedic transit calculator using Swiss Ephemeris.

    Zodiac: sidereal Lahiri.
    Time: current India time is converted to UTC before Julian-day calculation.
    Planet positions are geocentric ecliptic longitudes.
    This is a research/astrology layer, not a scientifically validated market predictor.
    """

    def __init__(self, tz_name: str = "Asia/Kolkata"):
        self.tz = ZoneInfo(tz_name)

    @staticmethod
    def _norm(x: float) -> float:
        return float(x % 360.0)

    @staticmethod
    def _safe(v):
        try:
            return float(v)
        except Exception:
            return float("nan")

    def _empty(self, dt_local: datetime, error: str = "") -> dict:
        return {
            "available": False,
            "error": error,
            "calculated_at_utc": "",
            "calculated_at_ist": dt_local.isoformat(),
            "ayanamsa": float("nan"),
            "score": 0.0,
            "moon_longitude": float("nan"),
            "moon_sign": "Unavailable",
            "moon_degree_in_sign": float("nan"),
            "nakshatra": "Unavailable",
            "nakshatra_pada": None,
            "tithi_number": float("nan"),
            "tithi_name": "Unavailable",
            "tithi_percent": float("nan"),
            "paksha": "Unavailable",
            "yoga": "Unavailable",
            "karana": "Unavailable",
            "retrograde": "None",
            "planets": [],
        }

    def _karana_name(self, tithi_number: int, elongation: float) -> str:
        # Karanas are 6-degree halves of a tithi. Index 1..60.
        half_index = int(elongation // 6.0) + 1
        if half_index in KARANA_FIXED:
            return KARANA_FIXED[half_index]
        if half_index < 2:
            return "Kimstughna"
        idx = (half_index - 2) % 7
        return KARANA_MOVING[idx]

    def calculate(self, dt: datetime | None = None) -> dict:
        if dt is None:
            dt = datetime.now(self.tz)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)
        dt_local = dt.astimezone(self.tz)
        dt_utc = dt_local.astimezone(timezone.utc)

        base = self._empty(dt_local)
        if swe is None:
            base["error"] = "pyswisseph is not installed"
            return base

        try:
            jd = swe.julday(
                dt_utc.year, dt_utc.month, dt_utc.day,
                dt_utc.hour
                + dt_utc.minute / 60.0
                + dt_utc.second / 3600.0
                + dt_utc.microsecond / 3_600_000_000.0
            )

            swe.set_sid_mode(swe.SIDM_LAHIRI)
            flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

            ayanamsa = float(swe.get_ayanamsa_ut(jd))
            positions = {}

            for name, body in PLANET_BODIES.items():
                xx, retflag = swe.calc_ut(jd, body, flags)
                positions[name] = {
                    "longitude": self._norm(xx[0]),
                    "latitude": float(xx[1]),
                    "distance_au": float(xx[2]),
                    "speed": float(xx[3]),
                    "retrograde": bool(xx[3] < 0.0),
                }

            node_xx, _ = swe.calc_ut(jd, NODE_BODY, flags)
            rahu_lon = self._norm(node_xx[0])
            positions["Rahu"] = {
                "longitude": rahu_lon,
                "latitude": float(node_xx[1]),
                "distance_au": float(node_xx[2]),
                "speed": float(node_xx[3]),
                "retrograde": bool(node_xx[3] < 0.0),
            }
            ketu_lon = self._norm(rahu_lon + 180.0)
            positions["Ketu"] = {
                "longitude": ketu_lon,
                "latitude": -float(node_xx[1]),
                "distance_au": float(node_xx[2]),
                "speed": float(node_xx[3]),
                "retrograde": bool(node_xx[3] < 0.0),
            }

            sun = positions["Sun"]["longitude"]
            moon = positions["Moon"]["longitude"]

            sign_idx = int(moon // 30.0)
            degree_in_sign = moon % 30.0

            nak_size = 360.0 / 27.0
            nak_idx = min(26, int(moon // nak_size))
            nak_remainder = moon - nak_idx * nak_size
            pada = min(4, int(nak_remainder / (nak_size / 4.0)) + 1)

            elongation = (moon - sun) % 360.0
            tithi_number = int(elongation // 12.0) + 1
            tithi_number = min(30, max(1, tithi_number))
            tithi_day = ((tithi_number - 1) % 15) + 1
            paksha = "Shukla" if tithi_number <= 15 else "Krishna"
            if tithi_day == 15 and tithi_number <= 15:
                tithi_label = "Purnima"
            elif tithi_day == 15:
                tithi_label = "Amavasya"
            else:
                tithi_label = TITHI_NAMES[tithi_day - 1]
            tithi_name = f"{paksha} {tithi_label}"
            tithi_percent = (elongation % 12.0) / 12.0 * 100.0

            yoga_value = (sun + moon) % 360.0
            yoga_idx = min(26, int(yoga_value // nak_size))
            yoga = YOGA_NAMES[yoga_idx]

            karana = self._karana_name(tithi_number, elongation)

            retro = [
                name for name in
                ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
                if positions[name]["retrograde"]
            ]

            planet_rows = []
            for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                         "Saturn", "Rahu", "Ketu"]:
                p = positions[name]
                lon = p["longitude"]
                sidx = int(lon // 30.0)
                planet_rows.append({
                    "planet": name,
                    "longitude": round(lon, 6),
                    "sign": SIGNS[sidx],
                    "degree_in_sign": round(lon % 30.0, 4),
                    "speed": round(p["speed"], 6),
                    "retrograde": p["retrograde"],
                })

            # Transparent, bounded research score. It is deliberately small so
            # celestial data cannot overpower technical confirmation.
            score = 0.0
            moon_sign = SIGNS[sign_idx]
            if sign_idx in (0, 4, 8):       # fire signs
                score += 1.5
            elif sign_idx in (2, 5, 10):    # air signs
                score += 0.5
            elif sign_idx in (1, 9):        # earth signs
                score += 0.25
            else:                            # water signs
                score -= 0.25

            # Jupiter/Saturn transit tendency relative to current Moon sign.
            j_sign = int(positions["Jupiter"]["longitude"] // 30.0)
            s_sign = int(positions["Saturn"]["longitude"] // 30.0)
            j_distance = (j_sign - sign_idx) % 12 + 1
            s_distance = (s_sign - sign_idx) % 12 + 1
            if j_distance in (1, 5, 9):
                score += 1.0
            if s_distance in (6, 8, 10):
                score += 0.5
            elif s_distance in (1, 4, 7):
                score -= 0.75

            # Retrograde is contextual, not automatically bearish.
            score -= min(1.5, 0.25 * len(retro))
            score = max(-5.0, min(5.0, score))

            return {
                "available": True,
                "error": "",
                "calculated_at_utc": dt_utc.isoformat(),
                "calculated_at_ist": dt_local.isoformat(),
                "ayanamsa": ayanamsa,
                "score": round(float(score), 2),
                "moon_longitude": round(moon, 6),
                "moon_sign": moon_sign,
                "moon_degree_in_sign": round(degree_in_sign, 4),
                "nakshatra": NAKSHATRAS[nak_idx],
                "nakshatra_pada": pada,
                "tithi_number": float(tithi_number),
                "tithi_name": tithi_name,
                "tithi_percent": round(tithi_percent, 2),
                "paksha": paksha,
                "yoga": yoga,
                "karana": karana,
                "retrograde": ", ".join(retro) if retro else "None",
                "planets": planet_rows,
            }
        except Exception as exc:
            base["error"] = f"{type(exc).__name__}: {exc}"
            return base
