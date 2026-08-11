"""Medini Jyotish -- experimental 10-Chakra analysis for NIFTY 50.

Uses the SAME real planetary data source as core/astro.py: Swiss Ephemeris
(pyswisseph), which is built on JPL DE ephemeris data -- the same underlying
astronomical model NASA planetarium tools use -- with Lahiri sidereal
ayanamsa. So the raw planetary positions here are astronomically accurate.

IMPORTANT HONESTY NOTE:
The interpretive rules below (vedha pairs, Kota Chakra swami table, Pancha
Pakshi bird/activity cycle, etc.) are classical Vedic techniques, but
different texts/traditions give slightly different versions of some of
these tables. This module implements one reasonable, simplified
interpretation for research purposes. It is NOT a validated predictor of
NIFTY price movement. It deliberately does NOT output specific price
targets or "expected % move" numbers -- only qualitative chakra verdicts,
because presenting precise numeric predictions from an unvalidated method
would be misleading.
"""

from datetime import datetime, timezone

try:
    import swisseph as swe
    OK = True
except Exception:
    OK = False

NAKSHATRAS = ['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha',
              'Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
              'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada',
              'Uttara Bhadrapada','Revati']
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
NADI = ['Adi','Madhya','Antya']

PLANETS = [('Sun',0),('Moon',1),('Mars',4),('Mercury',2),('Jupiter',5),('Venus',3),('Saturn',6),('Rahu',10)]
MALEFICS = {'Sun','Mars','Saturn','Rahu','Ketu'}

DEBILITATION = {'Sun':'Libra','Moon':'Scorpio','Mars':'Cancer','Mercury':'Pisces',
                 'Jupiter':'Capricorn','Venus':'Virgo','Saturn':'Aries'}
EXALTATION = {'Sun':'Aries','Moon':'Taurus','Mars':'Capricorn','Mercury':'Virgo',
               'Jupiter':'Cancer','Venus':'Pisces','Saturn':'Libra'}

# Simplified vedha (obstruction) pairing across the 27-nakshatra Sarvatobhadra
# grid -- one commonly cited version. Regional texts vary; treat as heuristic.
VEDHA_PAIRS = {0:8,8:0,1:7,7:1,2:19,19:2,3:16,16:3,4:15,15:4,5:14,14:5,6:26,26:6,
               9:25,25:9,10:24,24:10,11:23,23:11,12:22,22:12,13:21,21:13,17:20,20:17,18:18}

KOTA_SWAMI_BY_WEEKDAY = {6:'Sun',0:'Moon',1:'Mars',2:'Mercury',3:'Jupiter',4:'Venus',5:'Saturn'}
# Python weekday(): Monday=0 ... Sunday=6

PANCHA_PAKSHI_BIRDS = ['Vulture','Owl','Crow','Cock','Peacock']
PANCHA_PAKSHI_ACTIVITIES = ['Ruling','Eating','Walking','Sleeping','Dying']  # best -> worst


def _positions():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    now = datetime.now(timezone.utc)
    jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60 + now.second/3600)
    longs, lats = {}, {}
    for name, pid in PLANETS:
        xx, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        longs[name] = float(xx[0]) % 360
        lats[name] = float(xx[1])
    longs['Ketu'] = (longs['Rahu'] + 180) % 360
    lats['Ketu'] = -lats['Rahu']
    return longs, lats, now


def _nak_idx(lon): return int(lon / (360/27)) % 27
def _sign_idx(lon): return int(lon // 30) % 12


def sarvatobhadra(longs):
    moon_nak = _nak_idx(longs['Moon'])
    vedha_nak = VEDHA_PAIRS.get(moon_nak, moon_nak)
    hits = [p for p in longs if p != 'Moon' and _nak_idx(longs[p]) in (moon_nak, vedha_nak) and p in MALEFICS]
    verdict = 'Negative' if hits else 'Positive'
    return {'chakra': 'Sarvatobhadra', 'verdict': verdict,
            'detail': f"Moon Nakshatra: {NAKSHATRAS[moon_nak]}. Vedha-causing malefics present: {hits or 'None'}."}


def sanghatta(longs):
    nadis = {p: NADI[_nak_idx(l) % 3] for p, l in longs.items()}
    moon_nadi = nadis['Moon']
    same_nadi = [p for p, n in nadis.items() if n == moon_nadi and p in MALEFICS]
    verdict = 'Negative (crash risk)' if len(same_nadi) >= 2 else 'Positive'
    return {'chakra': 'Sanghatta', 'verdict': verdict,
            'detail': f"Moon Nadi: {moon_nadi}. Malefics sharing this Nadi: {same_nadi or 'None'}."}


def kurma(longs):
    moon_sign = _sign_idx(longs['Moon'])
    bad = []
    for p in ('Saturn', 'Mars'):
        rel = (_sign_idx(longs[p]) - moon_sign) % 12
        if rel in (0, 5, 7):  # same / 6th (conflict) / 8th (dusthana) from Moon sign
            bad.append(p)
    verdict = 'Negative' if bad else 'Positive'
    return {'chakra': 'Kurma', 'verdict': verdict,
            'detail': f"Moon Rashi: {SIGNS[moon_sign]}. Malefics in stressed houses from Moon: {bad or 'None'}."}


def kota(longs, now):
    swami = KOTA_SWAMI_BY_WEEKDAY[now.weekday()]
    sign = SIGNS[_sign_idx(longs[swami])]
    if sign == DEBILITATION.get(swami):
        verdict = 'Breached (Bearish)'
    elif sign == EXALTATION.get(swami):
        verdict = 'Secure (Bullish)'
    else:
        verdict = 'Neutral / Holding'
    return {'chakra': 'Kota', 'verdict': verdict,
            'detail': f"Kota Swami (today): {swami}, placed in {sign}."}


def surya_chandra_kalanala(longs):
    sun_sign = SIGNS[_sign_idx(longs['Sun'])]
    sun_strength = 'exalted' if sun_sign == EXALTATION['Sun'] else 'debilitated' if sun_sign == DEBILITATION['Sun'] else 'neutral'
    phase_diff = (longs['Moon'] - longs['Sun']) % 360
    waxing = phase_diff < 180
    mode = 'Agni (explosive/volatile)' if (waxing and sun_strength != 'debilitated') else 'Jala (calm/range-bound)'
    return {'chakra': 'Surya-Chandra Kalanala', 'verdict': mode,
            'detail': f"Sun: {sun_strength} in {sun_sign}. Moon phase: {'Waxing (Shukla)' if waxing else 'Waning (Krishna)'}."}


def graha_yuddha(longs):
    names = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    war = None
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a, b = names[i], names[j]
            if abs(longs[a] - longs[b]) <= 1.0:
                war = (a, b)
    if not war:
        return {'chakra': 'Graha Yuddha', 'verdict': 'None', 'detail': 'No planetary war within 1 degrees currently.'}
    return {'chakra': 'Graha Yuddha', 'verdict': f'War: {war[0]} vs {war[1]}',
            'detail': f'{war[0]} and {war[1]} are in close conjunction (<=1 deg) -- classical planetary war active for this sector.'}


def pancha_pakshi(longs, now):
    moon_nak = _nak_idx(longs['Moon'])
    bird = PANCHA_PAKSHI_BIRDS[moon_nak % 5]
    hour = now.hour
    slot = hour // 5  # rough 5-segment split of a 24h cycle, simplified
    activity = PANCHA_PAKSHI_ACTIVITIES[slot % 5]
    ruling_slot = [h for h in range(24) if (h // 5) % 5 == 0][:1]
    sleeping_slot = [h for h in range(24) if (h // 5) % 5 == 3][:1]
    return {'chakra': 'Pancha Pakshi', 'verdict': f"Bird: {bird}, current state: {activity}",
            'detail': f"Simplified cycle. Best entry near hour {ruling_slot[0]:02d}:00 IST (Ruling), avoid near hour {sleeping_slot[0]:02d}:00 IST (Sleeping)."}


def run_all_chakras():
    if not OK:
        return {'available': False, 'message': 'pyswisseph not installed.'}
    longs, lats, now = _positions()
    results = [
        sarvatobhadra(longs),
        sanghatta(longs),
        kurma(longs),
        kota(longs, now),
        surya_chandra_kalanala(longs),
        graha_yuddha(longs),
        pancha_pakshi(longs, now),
    ]
    neg = sum(1 for r in results if 'Negative' in r['verdict'] or 'Breached' in r['verdict'] or 'War' in r['verdict'])
    pos = sum(1 for r in results if 'Positive' in r['verdict'] or 'Secure' in r['verdict'])
    summary = 'Bullish leaning' if pos > neg else 'Bearish leaning' if neg > pos else 'Neutral / Mixed'
    return {'available': True, 'summary': summary, 'chakras': results, 'as_of': now.isoformat()}
