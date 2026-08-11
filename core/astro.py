from datetime import datetime,timezone
try: import swisseph as swe; OK=True
except Exception: OK=False
SIGNS=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
PLANETS=[('Sun',0),('Moon',1),('Mars',4),('Mercury',2),('Jupiter',5),('Venus',3),('Saturn',6),('Rahu',10)]
def sign(lon): return SIGNS[int(lon//30)%12],lon%30
def nak(lon):
    n=['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati']; return n[int(lon/(360/27))%27]
def get_sidereal_positions():
    if not OK:return {'available':False,'message':'pyswisseph is not installed. Run pip install -r requirements.txt'}
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI); now=datetime.now(timezone.utc); jd=swe.julday(now.year,now.month,now.day,now.hour+now.minute/60+now.second/3600); rows=[]; longs={}; retro=[]
        for name,pid in PLANETS:
            xx,_=swe.calc_ut(jd,pid,swe.FLG_SWIEPH|swe.FLG_SIDEREAL); lon=float(xx[0])%360; speed=float(xx[3]); sg,d=sign(lon); longs[name]=lon; retro.append(name) if speed<0 else None; rows.append({'Planet':name,'Sign':sg,'Degree':round(d,4),'Retrograde':speed<0})
        kl=(longs['Rahu']+180)%360; sg,d=sign(kl); rows.append({'Planet':'Ketu','Sign':sg,'Degree':round(d,4),'Retrograde':False}); moon=longs['Moon']; sun=longs['Sun']; msg=(moon-sun)%360; tithi=f"{'Shukla' if msg<180 else 'Krishna'} Paksha, Tithi {((int(msg/12))%15)+1}"; sg,deg=sign(moon)
        return {'available':True,'planets':rows,'moon_sign':sg,'moon_degree':deg,'nakshatra':nak(moon),'tithi':tithi,'retrograde':retro}
    except Exception as e:return {'available':False,'message':f'Swiss Ephemeris calculation failed: {e}'}
