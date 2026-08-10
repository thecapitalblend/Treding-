from datetime import datetime, timezone
try:
    import swisseph as swe
except Exception:
    swe=None
NAK=["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
class CelestialEngine:
    def analyze(self, dt=None):
        dt=dt or datetime.now(timezone.utc)
        if swe is None:
            return {"score":0,"moon_longitude":0,"moon_nakshatra":"Unavailable","status":"Swiss Ephemeris unavailable"}
        jd=swe.julday(dt.year,dt.month,dt.day,dt.hour+dt.minute/60+dt.second/3600)
        moon=swe.calc_ut(jd,swe.MOON)[0][0]
        nak=NAK[int((moon%360)/(360/27))]
        return {"score":0,"moon_longitude":float(moon),"moon_nakshatra":nak,"status":"RESEARCH / NEUTRAL"}
