"""Gochara (transits) against a natal chart. Transit positions come from the same engine as the natal chart
(astro.positions / Swiss Ephemeris, Drik-verified), so no external data is involved.

- House from natal Lagna and from natal Chandra (classical gochara counts from the Moon sign).
- Favourable houses from the Moon: Phaladeepika ch. 26 (gochara) as commonly tabulated. Moderate confidence:
  lists vary slightly between texts. Vedha (obstruction) is NOT applied.
- Ashtakavarga bindus of the transited sign: the transiting graha's own (bhinna) table + Sarvashtakavarga.
- Sade Sati: Shani in the 12th, 1st or 2nd from the natal Moon sign.
"""
import datetime
import astro, ashtakavarga, swisseph as swe

NINE = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu"]
PID = {"Surya": swe.SUN, "Chandra": swe.MOON, "Mangal": swe.MARS, "Budha": swe.MERCURY, "Guru": swe.JUPITER,
       "Shukra": swe.VENUS, "Shani": swe.SATURN, "Rahu": swe.MEAN_NODE, "Ketu": swe.MEAN_NODE}
GOOD_FROM_MOON = {"Surya": {3, 6, 10, 11}, "Chandra": {1, 3, 6, 7, 10, 11}, "Mangal": {3, 6, 11},
                  "Budha": {2, 4, 6, 8, 10, 11}, "Guru": {2, 5, 7, 9, 11}, "Shukra": {1, 2, 3, 4, 5, 8, 9, 11, 12},
                  "Shani": {3, 6, 11}, "Rahu": {3, 6, 11}, "Ketu": {3, 6, 11}}
SADE_SATI = {11: "rising (12th from Moon)", 0: "peak (over the Moon)", 1: "setting (2nd from Moon)"}


def sid(jd, g, aya_name="chitra-paksha"):
    """(sidereal longitude, speed deg/day) of graha g, same conventions as astro.positions."""
    l, sp = swe.calc_ut(jd, PID[g], swe.FLG_SPEED)[0][0:4:3]
    l = (l - astro.ayanamsha(jd, aya_name) + (180 if g == "Ketu" else 0)) % 360
    return l, sp


def _refine(f, a, b):
    """f changes value between a and b -> JD (UT) of the change, to ~1 s."""
    fa = f(a)
    while b - a > 1e-5:
        m = (a + b) / 2
        a, b = (m, b) if f(m) == fa else (a, m)
    return b


def events(g, jd0, jd1, aya_name="chitra-paksha"):
    """Sign ingresses and (for Mangal..Shani) retrograde/direct stations of g between jd0 and jd1."""
    step = {"Chandra": 0.1, "Surya": 0.5, "Budha": 0.25, "Shukra": 0.5, "Mangal": 1, "Guru": 2, "Shani": 2,
            "Rahu": 2, "Ketu": 2}[g]
    sign = lambda t: int(sid(t, g, aya_name)[0] // 30)
    retro = lambda t: sid(t, g, aya_name)[1] < 0
    out, t = [], jd0
    while t < jd1:
        u = min(t + step, jd1)
        if sign(t) != sign(u):
            j = _refine(sign, t, u)
            out.append({"jd": j, "graha": g, "event": "enters", "rashi": astro.RASHIS[sign(j + 1e-4)]})
        if g in ("Mangal", "Budha", "Guru", "Shukra", "Shani") and retro(t) != retro(u):
            j = _refine(retro, t, u)
            out.append({"jd": j, "graha": g, "event": "turns retrograde" if retro(u) else "turns direct",
                        "rashi": astro.RASHIS[sign(j)]})
        t = u
    return out


def sade_sati(moon_sign, jd0, jd1, aya_name="chitra-paksha"):
    """Periods when Shani is in the 12th/1st/2nd from the Moon sign, merged across retrograde back-and-forth."""
    inside = lambda t: (int(sid(t, "Shani", aya_name)[0] // 30) - moon_sign) % 12 in SADE_SATI
    spans, t, start = [], jd0, None
    while t < jd1:
        u = t + 2
        a, b = inside(t), inside(u)
        if not a and b:
            start = _refine(inside, t, u)
        elif a and not b:
            end = _refine(inside, t, u)
            spans.append([start if start is not None else jd0, end])
            start = None
        t = u
    if start is not None:
        spans.append([start, None])
    merged = []
    for s in spans:  # a retrograde exit/re-entry within ~a year belongs to the same Sade Sati
        if merged and merged[-1][1] is not None and s[0] - merged[-1][1] < 400:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return merged


def transits(natal_pos, jd, aya_name="chitra-paksha", classical=True):
    natal = {p["graha"]: p for p in natal_pos}
    lag, moon = natal["Lagna"]["rashi_index"], natal["Chandra"]["rashi_index"]
    av = ashtakavarga.ashtakavarga(natal_pos, classical)["Ashtakavarga"]
    col = {name: i for i, name in enumerate(av[0])}
    rows = []
    for g in NINE:
        l, sp = sid(jd, g, aya_name)
        b = astro.body(g, l, sp)
        k = b["rashi_index"]
        from_moon = (k - moon) % 12 + 1
        rows.append({"graha": g, "rashi": b["rashi"], "dms_in_rashi": b["dms_in_rashi"],
                     "nakshatra": f"{b['nakshatra']} {b['pada']}", "retro": sp < 0 or g in ("Rahu", "Ketu"),
                     "house_from_lagna": (k - lag) % 12 + 1, "house_from_moon": from_moon,
                     "favourable_from_moon": from_moon in GOOD_FROM_MOON[g],
                     "bindus": av[k + 1][col[g]] if g in col else None, "sav": av[k + 1][col["Sarv *"]]})
    shani = (int(sid(jd, "Shani", aya_name)[0] // 30) - moon) % 12
    return {"rows": rows, "sade_sati_now": SADE_SATI.get(shani)}


def local_str(jd, tz=None):
    """JD UT -> 'YYYY-MM-DD HH:MM TZ' in tz (olson) or the machine's local zone."""
    y, m, d, h = swe.revjul(jd)
    t = datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=h)
    t = t.astimezone(__import__("zoneinfo").ZoneInfo(tz)) if tz else t.astimezone()
    return t.strftime("%Y-%m-%d %H:%M %Z")
