"""Local Jyotish engine on Swiss Ephemeris. Conventions reverse-engineered from drikpanchang (checked against Drik during development).

Drik conventions reproduced here (verified on 36 fake charts, 1920-2030, 12 cities):
- Graha longitude = apparent tropical longitude - MEAN ayanamsha (no nutation), Lahiri = SIDM_LAHIRI_VP285.
  Residual <= 3" for Sun..Saturn, Moon <= 8" before 2020 (~30" after: Drik's delta-T differs), mean Rahu <= 20".
- Lagna: Drik converts birthplace longitude to sidereal time at the SIDEREAL rate (lon * 1.0027379 / 15 h).
  Strictly that's an error (moves Lagna up to ~0.4 deg in the Americas) but we match it; residual <= 40".
"""
import datetime, math, zoneinfo
import swisseph as swe

RASHIS = ["mesha", "vrishabha", "mithuna", "karka", "simha", "kanya",
          "tula", "vrishchika", "dhanu", "makara", "kumbha", "meena"]
RASHI_LORD = ["Mangal", "Shukra", "Budha", "Chandra", "Surya", "Budha",
              "Shukra", "Mangal", "Guru", "Shani", "Shani", "Guru"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
              "Ashlesha", "Magha", "P Phalguni", "U Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
              "Anuradha", "Jyeshtha", "Mula", "P Ashadha", "U Ashadha", "Shravana", "Dhanishtha",
              "Shatabhisha", "P Bhadrapada", "U Bhadrapada", "Revati"]
# Vimshottari order and years; nakshatra i is ruled by DASHA_LORDS[i % 9]
DASHA_LORDS = ["Ketu", "Shukra", "Surya", "Chandra", "Mangal", "Rahu", "Guru", "Shani", "Budha"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

GRAHAS = [("Surya", swe.SUN), ("Chandra", swe.MOON), ("Mangal", swe.MARS), ("Budha", swe.MERCURY),
          ("Guru", swe.JUPITER), ("Shukra", swe.VENUS), ("Shani", swe.SATURN)]
OUTER = [("Arun", swe.URANUS), ("Varun", swe.NEPTUNE), ("Yam", swe.PLUTO)]
AYANAMSHA = {"chitra-paksha": swe.SIDM_LAHIRI_VP285, "bv-ramana": swe.SIDM_RAMAN,
             "krishnamurthi-paddhati": swe.SIDM_KRISHNAMURTI, "tropical": None}
SIDEREAL_RATE = 1.00273790935
CLASSICAL = False  # True: true local sidereal time (no Drik longitude quirk). Module default = Drik mode (the oracle
                   # tests rely on it); the `kundali` CLI sets True unless --drik is given.


def jd_ut(date, time, tz):
    """Local civil date/time in an olson zone -> Julian day (UT). zoneinfo applies historical DST."""
    local = datetime.datetime.combine(datetime.date.fromisoformat(date), datetime.time.fromisoformat(time),
                                      zoneinfo.ZoneInfo(tz))
    u = local.astimezone(datetime.timezone.utc)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600 + u.microsecond / 3.6e9)


def ayanamsha(jd, name="chitra-paksha"):
    mode = AYANAMSHA[name]
    if mode is None:
        return 0.0
    swe.set_sid_mode(mode)
    return swe.get_ayanamsa_ex_ut(jd, swe.FLG_NONUT)[1]


def lagna(jd, lat, lon, aya):
    armc = (swe.sidtime(jd) * 15 + lon * (1.0 if CLASSICAL else SIDEREAL_RATE)) % 360
    eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
    cusps, ascmc = swe.houses_armc(armc, lat, eps, b"P")
    return (ascmc[0] - aya) % 360, armc, eps


def nakshatra(lon):
    """-> (index 0..26, pada 1..4, lord, KP sub-lord)."""
    span = 360 / 27
    i = int(lon // span)
    within = lon - i * span
    pada = int(within // (span / 4)) + 1
    # KP sub: the nakshatra divided in Vimshottari proportions starting from its own lord
    start = i % 9
    acc = 0.0
    for k in range(9):
        j = (start + k) % 9
        acc += span * DASHA_YEARS[j] / 120
        if within < acc - 1e-12:
            return i, pada, DASHA_LORDS[start], DASHA_LORDS[j]
    return i, pada, DASHA_LORDS[start], DASHA_LORDS[(start + 8) % 9]


def dms(x):
    """Degrees within rashi -> (d, m, s) truncated, as Drik prints them."""
    s = int(round(x * 3600, 6))
    return s // 3600, s // 60 % 60, s % 60


def body(name, lon, speed=0.0, lat=0.0, ra=0.0, dec=0.0):
    k = int(lon // 30) % 12
    n, pada, lord, sub = nakshatra(lon)
    d, m, s = dms(lon - 30 * k)
    return {"graha": name, "longitude": round(lon, 6), "rashi": RASHIS[k], "rashi_index": k,
            "dms_in_rashi": f"{d:02d}°{m:02d}′{s:02d}″", "nakshatra": NAKSHATRAS[n], "pada": pada,
            "nakshatra_lord": lord, "sub_lord": sub, "retro": speed < 0, "speed": round(speed, 4),
            "latitude": round(lat, 4), "right_ascension": round(ra, 4), "declination": round(dec, 4)}


def positions(jd, lat, lon, aya_name="chitra-paksha", rahu="mean-rahu", outer=True):
    """Lagna + 7 grahas (+ Uranus/Neptune/Pluto) + Rahu/Ketu, sidereal, Drik conventions."""
    aya = ayanamsha(jd, aya_name)
    asc, _, _ = lagna(jd, lat, lon, aya)
    out = [body("Lagna", asc)]
    for name, pid in GRAHAS + (OUTER if outer else []) + [("Rahu", swe.MEAN_NODE if rahu == "mean-rahu" else swe.TRUE_NODE)]:
        (l, b, _, sp, *_), _ = swe.calc_ut(jd, pid, swe.FLG_SPEED)
        (ra, dec, *_), _ = swe.calc_ut(jd, pid, swe.FLG_EQUATORIAL)
        out.append(body(name, (l - aya) % 360, sp, b, ra, dec))
        if name == "Rahu":
            k = (l - aya + 180) % 360
            out.append(body("Ketu", k, sp, -b, (ra + 180) % 360, -dec))
    for p in out:  # nodes are always shown retrograde (mean node speed is always negative anyway)
        if p["graha"] in ("Rahu", "Ketu"):
            p["retro"] = True
    return out


# ---- divisional charts -------------------------------------------------------------------------------
MOVABLE, FIXED, DUAL = (0, 3, 6, 9), (1, 4, 7, 10), (2, 5, 8, 11)


def _by_modality(k, movable, fixed, dual):
    return movable if k in MOVABLE else fixed if k in FIXED else dual


def varga(lon, n):
    """Sign index (0=Mesha) of a sidereal longitude in the D-n chart. Parashari schemes unless noted."""
    k, deg = int(lon // 30) % 12, lon % 30
    odd = k % 2 == 0  # Mesha (index 0) is an odd sign
    part = int(deg * n // 30)
    if n == 1:
        return k
    if n == 2:  # Parashari hora: odd 0-15 Simha / 15-30 Karka, even reversed
        return (4 if part == 0 else 3) if odd else (3 if part == 0 else 4)
    if n == 3:
        return (k + 4 * part) % 12
    if n == 4:
        return (k + 3 * part) % 12
    if n == 5:  # Panchamsha: odd Mesha, Kumbha, Dhanu, Mithuna, Tula; even reverse order of their pairs
        return ([0, 10, 8, 2, 6] if odd else [1, 5, 11, 9, 7])[part]
    if n == 6:
        return ((0 if odd else 6) + part) % 12
    if n == 7:
        return ((k if odd else k + 6) + part) % 12
    if n == 8:
        return (_by_modality(k, 0, 8, 4) + part) % 12
    if n == 9:
        return (_by_modality(k, k, k + 8, k + 4) + part) % 12
    if n == 10:
        return ((k if odd else k + 8) + part) % 12
    if n == 11:
        return (part - k) % 12  # Drik's Rudramsha: fitted 50/50 on Drik output
    if n == 12:
        return (k + part) % 12
    if n == 16:
        return (_by_modality(k, 0, 4, 8) + part) % 12
    if n == 20:
        return (_by_modality(k, 0, 8, 4) + part) % 12
    if n == 24:
        return ((4 if odd else 3) + part) % 12
    if n == 27:
        return ([0, 3, 6, 9][k % 4] + part) % 12
    if n == 30:  # unequal: odd 5,5,8,7,5 -> Mesha,Kumbha,Dhanu,Mithuna,Tula; even mirrored
        if odd:
            return 0 if deg < 5 else 10 if deg < 10 else 8 if deg < 18 else 2 if deg < 25 else 6
        return 1 if deg < 5 else 5 if deg < 12 else 11 if deg < 20 else 9 if deg < 25 else 7
    if n == 40:
        return ((0 if odd else 6) + part) % 12
    if n == 45:
        return (_by_modality(k, 0, 4, 8) + part) % 12
    if n == 60:
        return (k + part) % 12
    raise ValueError(f"unsupported division D{n}")


DIVISIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60]


def chart_houses(pos, n=1):
    """Whole-sign houses of the D-n chart -> [{bhava, rashi, residents}] (Lagna not listed as resident)."""
    signs = {p["graha"]: varga(p["longitude"], n) for p in pos}
    lag = signs["Lagna"]
    order = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu"]
    return [{"bhava": h + 1, "rashi": RASHIS[(lag + h) % 12],
             "residents": [g for g in order if signs.get(g) == (lag + h) % 12]} for h in range(12)]


def sun_altitude(jd, lat, lon):
    """True (unrefracted) altitude of the Sun's centre, degrees."""
    xx = swe.calc_ut(jd, swe.SUN, swe.FLG_EQUATORIAL)[0]
    return swe.azalt(jd, swe.EQU2HOR, (lon, lat, 0), 0, 0, xx)[1]


SUN_H0 = -0.8333  # centre altitude at rise/set at sea level (34' refraction + 16' semidiameter); Drik adds a dip:
# pass h0=timing.sun_h0(elevation) = SUN_H0 - 0.0373*sqrt(elevation m) to match Drik (fitted, timing.py)


def _cross(f, a, b):
    for _ in range(50):
        m = (a + b) / 2
        if (f(a) > 0) == (f(m) > 0):
            a = m
        else:
            b = m
    return (a + b) / 2


def sun_events(jd, lat, lon, h0=None):
    """(sunrise on/before jd, following sunset, next sunrise) in JD UT, Sun centre crossing altitude h0."""
    h0 = SUN_H0 if h0 is None else h0
    f = lambda t: sun_altitude(t, lat, lon) - h0
    step = 1 / 96  # 15 min scan, then bisect
    rises, sets = [], []
    t = jd - 1.5
    while t < jd + 1.5:
        a, b = f(t), f(t + step)
        if a <= 0 < b:
            rises.append(_cross(f, t, t + step))
        elif a > 0 >= b:
            sets.append(_cross(f, t, t + step))
        t += step
    rise = max(r for r in rises if r <= jd)
    return rise, min(x for x in sets if x > rise), min(r for r in rises if r > rise)
