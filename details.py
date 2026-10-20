"""The planet/house detail tables of Drik's kundali page, Bhav Chalit and combustion, computed locally.
Conventions fitted against Drik (checked against Drik during development):
- Relationship = NAISARGIKA (natural) friendship of the graha with the sign lord, not panchadha (compound).
  Rahu/Ketu have their own tables below and never show "Own House" (Ruler of still lists Kumbha/Vrishchika).
- Dignity on the varga longitude (sign + degree*n within it). Whole-sign exaltation/debilitation, except Chandra
  and Budha, whose exaltation ends where their moolatrikona span starts in the same sign. "Deep" = inside the
  deep-exaltation degree (Surya 10 -> 9..10). Rahu: exalted Mithuna, debilitated Dhanu, mooltrikona Kanya;
  Ketu the opposite signs, mooltrikona Meena.
- (Q)/(T) = the graha's/bhava's house is a kendra (1 4 7 10) / trikona (5 9).
- Icons: 💱 Sthana Parivartana (sign exchange among the 7 grahas, "<lord-of-house> X and <lord-of-house> Y"),
  🌸 Pushkaramsha (D1 table only), ⚠ Mrityuamsha (graha inside its mrityu-bhaga degree, any varga, incl. Lagna,
  Rahu, Ketu), 🔥 Dagdha rashi of the birth tithi (house tables).
- Combustion ("C") is Drik's asta = heliacal invisibility, not an orb: Sun's depression below the horizon when
  the graha rises (morning sky) / sets (evening sky) at the birthplace, at the last such event before birth
  and the next after it; combust if either is below the graha's arcus visionis.
"""
import swisseph as swe
import astro

ORDER = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani", "Rahu", "Ketu"]
RASHI_NAMES = [r.title() for r in astro.RASHIS]
# Naisargika friendship: (friends, enemies); the rest neutral. Rahu/Ketu rows fitted to Drik.
NATURAL = {"Surya": ("Chandra Mangal Guru", "Shukra Shani"), "Chandra": ("Surya Budha", ""),
           "Mangal": ("Surya Chandra Guru", "Budha"), "Budha": ("Surya Shukra", "Chandra"),
           "Guru": ("Surya Chandra Mangal", "Budha Shukra"), "Shukra": ("Budha Shani", "Surya Chandra"),
           "Shani": ("Budha Shukra", "Surya Chandra Mangal"),
           "Rahu": ("Guru Shukra Shani", "Surya Chandra Mangal"), "Ketu": ("Mangal Shukra Shani", "Surya Chandra")}
OWN = {g: [k for k in range(12) if astro.RASHI_LORD[k] == g] for g in ORDER}
OWN["Rahu"], OWN["Ketu"] = [10], [7]
# (exaltation sign, deep-exaltation degree, moolatrikona sign, mt from, mt to); debilitation = exaltation + 6
DIGNITY = {"Surya": (0, 10, 4, 0, 20), "Chandra": (1, 3, 1, 3, 30), "Mangal": (9, 28, 0, 0, 12),
           "Budha": (5, 15, 5, 15, 20), "Guru": (3, 5, 8, 0, 10), "Shukra": (11, 27, 6, 0, 15),
           "Shani": (6, 20, 10, 0, 20), "Rahu": (2, None, 5, 0, 30), "Ketu": (8, None, 11, 0, 30)}
# Mrityu bhaga per rashi, columns Surya..Ketu, Lagna (the standard table); the graha is in the degree's
# 1-degree span ending at the listed value (20 -> 19..20)
MRITYU = [[20, 26, 19, 15, 19, 28, 10, 14, 8, 1], [9, 12, 28, 14, 29, 15, 4, 13, 18, 9],
          [12, 13, 25, 13, 12, 11, 7, 12, 20, 22], [6, 25, 23, 12, 27, 17, 9, 11, 10, 22],
          [8, 24, 29, 8, 6, 10, 12, 24, 21, 25], [24, 11, 28, 18, 4, 13, 16, 23, 22, 2],
          [16, 26, 14, 20, 13, 4, 3, 22, 23, 4], [17, 14, 21, 10, 10, 6, 18, 21, 24, 23],
          [22, 13, 2, 21, 17, 27, 28, 10, 11, 18], [2, 25, 15, 22, 11, 12, 14, 20, 12, 20],
          [3, 5, 11, 7, 15, 29, 13, 18, 13, 24], [23, 12, 6, 5, 28, 19, 15, 8, 14, 10]]
# Pushkara navamshas (0-based index of 9 within the sign) by element: fire 7th+9th, earth 3rd+5th, air 6th+8th,
# water 1st+3rd
PUSHKARA = [(6, 8), (2, 4), (5, 7), (0, 2)]
# Dagdha rashis for tithi 1..14 of either paksha; Purnima/Amavasya none. Dashami = Mesha+Vrishchika (Drik's
# table; Muhurta texts often give Simha+Vrishchika). Tithis 1, 3, 4, 7, 9 not yet seen in Drik data.
DAGDHA = [(6, 9), (8, 11), (4, 9), (1, 10), (2, 5), (0, 4), (3, 8), (2, 5), (4, 7), (0, 7), (8, 11), (6, 9),
          (1, 4), (2, 5, 8, 11)]
HOUSE_LORD = ["Lagnesha", "Dhanesha", "Sahajesha", "Sukhesha", "Sutesha", "Ridesha", "Daresha",
              "Randhresha", "Bhagyesha", "Karmesha", "Labhesha", "Vyayesha"]
ASPECTS = {"Mangal": (4, 7, 8), "Guru": (5, 7, 9), "Shani": (3, 7, 10)}  # others 7th only; Rahu/Ketu none
# Arcus visionis (Sun depression, deg). Fitted: every value inside the separating interval on 37 charts
# (Chandra 8.6-10.8, Budha 10.4-11.0 (direct and retro), Shukra 4.0-9.7, Mangal 12.1-21.3, Guru 2.2-7.7,
# Shani 8.8-21.9, Arun 0.4-14.8, Varun 2.8-6.7, Yam 1.1-4.6); exact values unknown inside those ranges.
ARCUS = {"Chandra": 10, "Mangal": 14.5, "Budha": 10.7, "Guru": 5, "Shukra": 5, "Shani": 11,
         "Arun": 5, "Varun": 5, "Yam": 3}
PID = dict(astro.GRAHAS + astro.OUTER)


def varga_lon(lon, n):
    """Longitude in the D-n chart: its sign + the degree scaled by n within it (what Drik's tables print)."""
    return 30 * astro.varga(lon, n) + lon * n % 30


def relationship(g, sign):
    if sign in OWN[g] and g not in ("Rahu", "Ketu"):
        return "Own House"
    lord, (f, e) = astro.RASHI_LORD[sign], NATURAL[g]
    return "Friend's House" if lord in f.split() else "Enemy's House" if lord in e.split() else "Neutral"


def dignity(g, lon):
    ex, deep, mt, a, b = DIGNITY[g]
    k, d = int(lon // 30), lon % 30
    if k == mt and a <= d < b:
        return "Mooltrikona"
    if k == ex and not (k == mt and d >= a):
        return "Deep Exalted" if deep is not None and int(d) == deep - 1 else "Exalted"
    if k == (ex + 6) % 12:
        return "Deep Debilitated" if deep is not None and int(d) == deep - 1 else "Debilitated"
    return "-"


def tithi(pos):
    """1..30 (16..30 = krishna paksha, 30 = Amavasya) at the moment of the positions."""
    lon = {p["graha"]: p["longitude"] for p in pos}
    return int((lon["Chandra"] - lon["Surya"]) % 360 // 12) + 1


def dagdha(pos):
    t = tithi(pos) % 15
    return set(DAGDHA[t - 1]) if t else set()


def marker(h):
    return "(Q)" if h in (1, 4, 7, 10) else "(T)" if h in (5, 9) else ""


def _chart(pos, n):
    lon = {p["graha"]: varga_lon(p["longitude"], n) for p in pos if p["graha"] in ORDER + ["Lagna"]}
    return lon, {g: int(x // 30) for g, x in lon.items()}, int(lon["Lagna"] // 30)


def planet_table(pos, n=1):
    """Rows of Drik's planet table for the D-n chart (n=1: the Rashi chart)."""
    lon, sign, lag = _chart(pos, n)
    rows = []
    for g in ["Lagna"] + ORDER:
        k, d = sign[g], lon[g] % 30
        h = (k - lag) % 12 + 1
        icons = []
        for y in ORDER[:7]:
            if g in ORDER[:7] and y != g and astro.RASHI_LORD[k] == y and astro.RASHI_LORD[sign[y]] == g:
                icons.append(f"{HOUSE_LORD[(sign[y] - lag) % 12]} {g} and {HOUSE_LORD[h - 1]} {y} Sthana Parivartana")
        if n == 1 and int(d * 3 / 10) in PUSHKARA[k % 4]:
            icons.append(f"{g} Pushkaramsha")
        if int(d) == MRITYU[k][9 if g == "Lagna" else ORDER.index(g)] - 1:
            icons.append(f"{g} Mrityuamsha")
        r = {"graha": g, "marker": marker(h), "icons": icons, "is_in": f"{h} Bhava", "b_owner": astro.RASHI_LORD[k]}
        if g == "Lagna":
            r.update(ruler_of="", relationship="", dignity="-")
        else:
            r.update(ruler_of=", ".join(str((s - lag) % 12 + 1) for s in OWN[g]) + " Bhava",
                     relationship=relationship(g, k), dignity=dignity(g, lon[g]))
        rows.append(r)
    return rows


def house_table(pos, n=1):
    """Rows of Drik's house table for the D-n chart (whole-sign bhavas)."""
    lon, sign, lag = _chart(pos, n)
    burnt = dagdha(pos)
    out = []
    for h in range(1, 13):
        k = (lag + h - 1) % 12
        asp = [g for g in ORDER[:7] if (k - sign[g]) % 12 + 1 in ASPECTS.get(g, (7,))]
        out.append({"bhava": h, "marker": marker(h), "residents": ", ".join(g for g in ORDER if sign[g] == k),
                    "owner": astro.RASHI_LORD[k], "rashi": RASHI_NAMES[k],
                    "icons": [f"Dagdha {RASHI_NAMES[k]} Rashi"] if k in burnt else [],
                    "qualities": ("Mas" if k % 2 == 0 else "Fem") + ", " + ["Movable", "Fixed", "Common"][k % 3],
                    "aspected_by": ", ".join(asp)})
    return out


def _sun_depression(t, geo):
    return -swe.azalt(t, swe.EQU2HOR, geo, 0, 0, swe.calc_ut(t, swe.SUN, swe.FLG_EQUATORIAL)[0])[1]


def combust(jd, lat, lon, pos=None):
    """{graha: bool} Drik's "C" (asta) flag for Chandra..Shani and Arun/Varun/Yam."""
    pos = pos or astro.positions(jd, lat, lon)
    L = {p["graha"]: p["longitude"] for p in pos}
    geo = (lon, lat, 0)
    out = {}
    for g, av in ARCUS.items():
        if g not in L:
            continue
        el = (L[g] - L["Surya"]) % 360
        if 60 < el < 300:  # nowhere near the Sun; skip the rise/set searches
            out[g] = False
            continue
        rs = swe.CALC_SET if el < 180 else swe.CALC_RISE  # east of the Sun = evening sky
        try:
            ts = [t for o in (-2, -1, 0) if (t := swe.rise_trans(jd + o, PID[g], rs, geo, 0, 0)[1][0]) > 0]
            before, after = max(t for t in ts if t <= jd), min(t for t in ts if t > jd)
        except (ValueError, swe.Error):  # circumpolar at this latitude
            out[g] = False
            continue
        out[g] = min(_sun_depression(before, geo), _sun_depression(after, geo)) < av
    return out


def bhav_chalit(jd, lat, lon, pos=None):
    """Sripati bhavas: madhyas trisect the Lagna-MC quadrants (Porphyry), bhava starts at the midpoint (sandhi)."""
    pos = pos or astro.positions(jd, lat, lon)
    aya = astro.ayanamsha(jd)
    _, armc, eps = astro.lagna(jd, lat, lon, aya)
    sandhi, madhya = ([(c - aya) % 360 for c in swe.houses_armc(armc, lat, eps, hs)[0][:12]] for hs in (b"S", b"O"))
    L = {p["graha"]: p["longitude"] for p in pos}
    out = []
    for h in range(12):
        a, b = sandhi[h], sandhi[(h + 1) % 12]
        out.append({"bhava": h + 1, "start": round(a, 6), "madhya": round(madhya[h], 6),
                    "rashi": astro.RASHIS[int(madhya[h] // 30)],
                    "residents": [g for g in ORDER if (L[g] - a) % 360 < (b - a) % 360]})
    return out
