"""Shadbala and Bhavabala, reproducing drikpanchang's numbers (checked against Drik during development).

Drik conventions found by fitting its tables (evidence from the development oracle, not shipped):
- Uchcha = distance from deep debilitation / 3. Dig = distance from the powerless cardinal point / 3, using the
  real MC/IC (not Lagna+90).
- Ayana = (24 +- declination) * 1.25 on true equatorial declination, UNCLAMPED (can go negative); +dec good for
  Su/Ma/Gu/Sk, -dec for Mo/Sa, |dec| for Bu; Sun doubled.
- Paksha: elongation/3 for benefics, 60 minus that for malefics; Moon always gets 2 * elongation/3.
- Drishti (planets): 1/4 of (benefic - malefic) sphuta aspects. Special aspects (Ma 4/8, Gu 5/9, Sa 3/10)
  add 15/30/45 virupas when the aspected point lies in that SIGN counted from the aspector (rashi count, not
  degree ranges). Bhava drishti: same on Sripati (Porphyry) bhava madhyas, special-aspect count from the
  WHOLE-SIGN house, Guru and Budha aspects in full, Budha always benefic there.
- Moon benefic iff waxing. Budha's benefic/malefic status for Paksha + planet Drishti is UNRESOLVED (Drik makes
  him malefic in 3 of 9 test charts with no conjunction/aspect/lordship pattern found); we use benefic (classical
  default for an unafflicted Budha). Tests file those charts as intentional.
- astro.CLASSICAL (CLI default; `--drik` turns it off): Nata/Unnata at the birthplace meridian instead of the time-zone meridian.
- Nata/Unnata from the Sun's hour angle at the TIME-ZONE meridian (tz*15), not the birthplace longitude.
- Hora lord: unequal planetary hours (day/night each /12) from the Drik sunrise (timing.sun_h0). Varsha/Masa:
  BV Raman ahargana (day 175 = 1952-01-01). Tri Bhaga: Guru always 60 + the lord of the day/night third.
- Chesta: CLASSICAL BY DESIGN (deliberate). Sun = |sayana Sun - 270| / 3 and Moon = elongation / 3
  match Drik; for Ma..Sa we use the classical cheshta kendra, because Drik's values can't be the classical formula
  (they exceed its 60 maximum, and e.g. halve a retrograde Guru near opposition). Tests file these as intentional.
- Bhavadhipati = Total Pinda of the lord of the sign on the Sripati bhava MADHYA (found 2026-10-04; whole-sign
  house lord fails at high latitudes). Bhava Drishti residual: 9/108 values off by 0.01-0.02 (Drik-internal rounding;
  rounding aspects/terms/madhyas to 2 dp doesn't close it).
- "Bhava (in %)": 100 at the Sripati bhava madhya falling linearly to 0 at either sandhi, rounded.
"""
import math
import astro, timing, swisseph as swe

G = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani"]
NAISARGIKA = [60.0, 51.43, 17.14, 25.71, 34.29, 42.86, 8.57]
MIN_RUPAS = [5, 6, 5, 7, 6.5, 5.5, 5]
DEBIL = [190, 213, 118, 345, 275, 177, 20]          # deep debilitation longitudes
OWN = {"Surya": [4], "Chandra": [3], "Mangal": [0, 7], "Budha": [2, 5], "Guru": [8, 11], "Shukra": [1, 6],
       "Shani": [9, 10]}
MT = {"Surya": (4, 0, 20), "Chandra": (1, 3, 30), "Mangal": (0, 0, 12), "Budha": (5, 15, 20),
      "Guru": (8, 0, 10), "Shukra": (6, 0, 15), "Shani": (10, 0, 20)}  # moolatrikona sign, degree span
FRIENDS = {"Surya": "Chandra Mangal Guru", "Chandra": "Surya Budha", "Mangal": "Surya Chandra Guru",
           "Budha": "Surya Shukra", "Guru": "Surya Chandra Mangal", "Shukra": "Budha Shani",
           "Shani": "Budha Shukra"}
ENEMIES = {"Surya": "Shukra Shani", "Chandra": "", "Mangal": "Budha", "Budha": "Chandra",
           "Guru": "Budha Shukra", "Shukra": "Surya Chandra", "Shani": "Surya Chandra Mangal"}
VARGAS = [1, 2, 3, 7, 9, 12, 30]
DAY_LORD = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani"]  # Sunday first
HORA_ORDER = ["Surya", "Shukra", "Budha", "Chandra", "Shani", "Guru", "Mangal"]
SPECIAL = {"Mangal": ((3, 7), 15), "Guru": ((4, 8), 30), "Shani": ((2, 9), 45)}  # sign offsets 4th/8th etc.


def arc(a, b):
    """Shortest angular distance, 0..180."""
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


def relation(g, lord, sign_of):
    """Compound (panchadha) relation of g to lord: 2 great friend .. -2 great enemy."""
    nat = 1 if lord in FRIENDS[g].split() else -1 if lord in ENEMIES[g].split() else 0
    tmp = 1 if (sign_of[lord] - sign_of[g]) % 12 in (1, 2, 3, 9, 10, 11) else -1
    return nat + tmp


def sapta_vargaja(g, lon, sign_of):
    total = 0.0
    for n in VARGAS:
        s = astro.varga(lon, n)
        mts, lo, hi = MT[g]
        if n == 1 and s == mts and lo <= lon % 30 < hi:
            total += 45
        elif s in OWN[g]:
            total += 30
        else:
            total += {2: 22.5, 1: 15, 0: 7.5, -1: 3.75, -2: 1.875}[relation(g, astro.RASHI_LORD[s], sign_of)]
    return total


def sphuta_aspect(a):
    """Base drishti virupas for aspect angle a (aspected - aspector, 0..360)."""
    if a < 30: return 0.0
    if a < 60: return (a - 30) / 2
    if a < 90: return a - 45
    if a < 120: return 30 + (120 - a) / 2
    if a < 150: return 150 - a
    if a < 180: return 2 * (a - 150)
    if a < 300: return (300 - a) / 2
    return 0.0


def aspect(g, glon, target, tsign=None):
    """Drishti of graha g at glon on the point target; tsign = sign used for the special-aspect count
    (the target's own sign for planets, the whole-sign house for bhavas)."""
    v = sphuta_aspect((target - glon) % 360)
    if g in SPECIAL:
        offs, add = SPECIAL[g]
        if ((int(target // 30) if tsign is None else tsign) - int(glon // 30)) % 12 in offs:
            v += add
    return v


def sripati_madhya(jd, lat, lon, pos):
    """Bhava madhyas: cardinal points (sidereal) with each quadrant trisected (Porphyry)."""
    aya = astro.ayanamsha(jd)
    _, armc, eps = astro.lagna(jd, lat, lon, aya)
    cusps, _ = swe.houses_armc(armc, lat, eps, b"O")
    return [(c - aya) % 360 for c in cusps[:12]]


def _rows(jd, lat, lon, pos, tz=None, elevation=0, budha_benefic=True, chesta_override=None):
    L = {p["graha"]: p for p in pos}
    lon_ = {g: L[g]["longitude"] for g in G}
    sign_of = {g: int(lon_[g] // 30) for g in G}
    asc = L["Lagna"]["longitude"]
    mad = sripati_madhya(jd, lat, lon, pos)
    mc, ic = mad[9], mad[3]
    elong = arc(lon_["Chandra"], lon_["Surya"])
    waxing = (lon_["Chandra"] - lon_["Surya"]) % 360 < 180
    benefic = {"Surya": False, "Chandra": waxing, "Mangal": False, "Budha": budha_benefic, "Guru": True, "Shukra": True,
               "Shani": False}

    R = {}
    R["Uchcha"] = [arc(lon_[g], DEBIL[i]) / 3 for i, g in enumerate(G)]
    R["Sapta Varigya"] = [sapta_vargaja(g, lon_[g], sign_of) for g in G]
    oja = []
    for g in G:
        want = 1 if g in ("Chandra", "Shukra") else 0  # even-sign lovers
        oja.append(15 * ((sign_of[g] % 2 == want) + (astro.varga(lon_[g], 9) % 2 == want)))
    R["Oja Yugma"] = oja
    R["Kendradi"] = [{0: 60, 1: 30, 2: 15}[((sign_of[g] - int(asc // 30)) % 12) % 3] for g in G]
    dec = {"Surya": 0, "Mangal": 0, "Guru": 0, "Budha": 1, "Shani": 1, "Chandra": 2, "Shukra": 2}
    R["Drekkana"] = [15 if int(lon_[g] % 30 // 10) == dec[g] else 0 for g in G]
    R["Sthana"] = [sum(R[k][i] for k in ("Uchcha", "Sapta Varigya", "Oja Yugma", "Kendradi", "Drekkana"))
                           for i in range(7)]
    weak = {"Surya": ic, "Mangal": ic, "Chandra": mc, "Shukra": mc, "Budha": (asc + 180) % 360,
            "Guru": (asc + 180) % 360, "Shani": asc}
    R["Disha"] = [arc(lon_[g], weak[g]) / 3 for g in G]

    # --- Kala ---
    rise, sset, nrise = astro.sun_events(jd, lat, lon, h0=timing.sun_h0(elevation))
    day = rise <= jd < sset
    R["Nata Unnata"] = nata_unnata(jd, lat, lon, tz)
    R["Paksha"] = [2 * elong / 3 if g == "Chandra" else elong / 3 if benefic[g] else 60 - elong / 3 for g in G]
    part = int((jd - rise) / (sset - rise) * 3) if day else int((jd - sset) / (nrise - sset) * 3)
    tri = (["Budha", "Surya", "Shani"] if day else ["Chandra", "Shukra", "Mangal"])[part]
    R["Tri Bhaga"] = [60 if g in (tri, "Guru") else 0 for g in G]
    varsha, masa, vara, hora = lords(jd, rise, sset, nrise, tz)
    R["Varshadhipati"] = [15 if g == varsha else 0 for g in G]
    R["Masadhipati"] = [30 if g == masa else 0 for g in G]
    R["Varadhipati"] = [45 if g == vara else 0 for g in G]
    R["Horadhipati"] = [60 if g == hora else 0 for g in G]
    R["Ayana"] = []
    for g in G:
        d = L[g]["declination"]
        d = -d if g in ("Chandra", "Shani") else abs(d) if g == "Budha" else d
        R["Ayana"].append((24 + d) * 1.25 * (2 if g == "Surya" else 1))
    R["Yuddha"] = [0.0] * 7  # ponytail: graha yuddha not modelled yet (needs a fixture with two planets < 1 deg)
    R["Kala"] = [sum(R[k][i] for k in ("Nata Unnata", "Paksha", "Tri Bhaga", "Varshadhipati", "Masadhipati",
                                              "Varadhipati", "Horadhipati", "Ayana", "Yuddha")) for i in range(7)]
    R["Chesta"] = list(chesta_override) if chesta_override else chesta(jd, lon_, elong)
    R["Naisargika"] = NAISARGIKA
    R["Drishti"] = [sum((1 if benefic[x] else -1) * aspect(x, lon_[x], lon_[g]) for x in G if x != g) / 4 for g in G]
    R["Total Pinda"] = [sum(R[k][i] for k in ("Sthana", "Disha", "Kala", "Chesta", "Naisargika",
                                              "Drishti")) for i in range(7)]
    R["Rupas"] = [t / 60 for t in R["Total Pinda"]]
    R["Min. Require"] = MIN_RUPAS
    R["Strength Ratio"] = [r / m for r, m in zip(R["Rupas"], MIN_RUPAS)]
    order = sorted(range(7), key=lambda i: -R["Strength Ratio"][i])
    R["Relative Rank"] = [order.index(i) + 1 for i in range(7)]
    R["Bhava (in %)"] = [bhava_pct(lon_[g], mad) for g in G]
    R["Ishta Phala"] = [math.sqrt(u * c) for u, c in zip(R["Uchcha"], R["Chesta"])]
    R["Kashta Phala"] = [math.sqrt(max(0.0, (60 - u) * (60 - c))) for u, c in zip(R["Uchcha"], R["Chesta"])]
    return R, benefic, lon_, mad


def bhava_pct(x, mad):
    """Closeness to the Sripati bhava madhya: 100 on the madhya, 0 on either sandhi (Drik's "Bhava (in %)")."""
    for h in range(12):
        m, prev, nxt = mad[h], mad[h - 1], mad[(h + 1) % 12]
        lo, hi = (m - prev) % 360 / 2, (nxt - m) % 360 / 2  # madhya -> sandhi on each side
        d = (x - m + 180) % 360 - 180
        if -lo <= d < hi:
            return int(100 * (1 - abs(d) / (hi if d >= 0 else lo)) + 0.5)


def nata_unnata(jd, lat, lon, tz=None):
    """Unnata (Su/Gu/Sk) = 60 at local apparent noon falling to 0 at midnight; Nata (Mo/Ma/Sa) = 60 - that;
    Budha 60. Drik measures the Sun's hour angle at the TIME-ZONE meridian (tz*15), not the birthplace."""
    mer = lon if tz is None or astro.CLASSICAL else tz * 15  # classical: local apparent time at the birthplace
    ra = swe.calc_ut(jd, swe.SUN, swe.FLG_EQUATORIAL)[0][0]
    ha = arc((swe.sidtime(jd) * 15 + mer) % 360, ra)
    un = 60 * (1 - ha / 180)
    return [60.0 if g == "Budha" else un if g in ("Surya", "Guru", "Shukra") else 60 - un for g in G]


def lords(jd, rise, sset, nrise, tz=None):
    """Varsha/Masa lords from BV Raman's ahargana (360-day years, 30-day months), vara, and the hora lord with
    unequal planetary hours (day and night each split in 12)."""
    off = (tz or 0) / 24
    a = int(jd + off + 0.5) - 2434013 + 175  # local civil day number; 2434013 = JD of 1952-01-01
    tue = ["Mangal", "Budha", "Guru", "Shukra", "Shani", "Surya", "Chandra"]
    varsha = tue[(a // 360 * 3 + 1) % 7]
    masa = tue[(a // 30 * 2 + 1) % 7]
    wd = int(rise + off + 1.5) % 7  # JD -> weekday, 0 = Sunday, of the sunrise that started this day
    vara = DAY_LORD[wd]
    h = int(12 * (jd - rise) / (sset - rise)) if jd < sset else 12 + int(12 * (jd - sset) / (nrise - sset))
    hora = HORA_ORDER[(HORA_ORDER.index(vara) + h) % 7]
    return varsha, masa, vara, hora


MEAN = {"Surya": (280.46646, 0.98564736), "Mangal": (355.433, 0.5240207766), "Budha": (252.250906, 4.0923344),
        "Guru": (34.351519, 0.0830853), "Shukra": (181.979801, 1.6021302), "Shani": (50.077444, 0.0334442)}


def chesta(jd, lon_, elong):
    """Sun: distance of the sayana Sun from the winter solstice / 3 (matches Drik). Moon: elongation / 3 (matches).
    Ma..Sa: classical cheshta kendra = sighrocca - (mean + true)/2, reduced to 0..180, / 3, with modern mean
    longitudes (J2000 linear). ponytail: Drik's own mean longitudes are unknown; this lands within ~1 virupa on
    about half the planets and is far off on the rest (per the development oracle residuals)."""
    aya = astro.ayanamsha(jd)
    m = {g: (a + r * (jd - 2451545.0) - aya) % 360 for g, (a, r) in MEAN.items()}
    out = [arc(lon_["Surya"] + aya, 270) / 3, elong / 3]
    for g in G[2:]:
        sig, mean = (m[g], m["Surya"]) if g in ("Budha", "Shukra") else (m["Surya"], m[g])
        avg = (mean + ((lon_[g] - mean + 180) % 360 - 180) / 2) % 360
        out.append(arc(sig, avg) / 3)
    return out


def shadbala(jd, lat, lon, pos, tz=None, elevation=0, **kw):
    """tz = UTC offset in hours (Drik's Nata/Unnata and calendar lords use it), elevation in metres (sunrise).
    -> {Drik row label: [Surya..Shani values]} (unrounded; Drik shows 2 decimals, ratio 4)."""
    return _rows(jd, lat, lon, pos, tz, elevation, **kw)[0]


def _bhava_kind(x):
    """Sign class of a longitude for bhava dig bala: 'nara' strong in 1st, 'jala' 4th, 'keeta' 7th, 'pashu' 10th."""
    s, d = int(x // 30), x % 30
    if s in (2, 5, 6, 10) or (s == 8 and d < 15):
        return 0
    if s in (3, 11) or (s == 9 and d >= 15):
        return 3
    if s == 7:
        return 6
    return 9


def bhavabala(jd, lat, lon, pos, tz=None, elevation=0, **kw):
    """-> {Drik row label: [bhava I..XII values]}."""
    R, benefic, lon_, mad = _rows(jd, lat, lon, pos, tz, elevation, **kw)
    pinda = dict(zip(G, R["Total Pinda"]))
    asc_sign = int(next(p for p in pos if p["graha"] == "Lagna")["longitude"] // 30)
    # lord of the sign holding the Sripati bhava madhya (not the whole-sign house; they differ at high latitudes)
    B = {"Bhavadhipati": [pinda[astro.RASHI_LORD[int(mad[h] // 30) % 12]] for h in range(12)]}
    B["Disha"] = [60 - 10 * min((h - _bhava_kind(mad[h])) % 12, (_bhava_kind(mad[h]) - h) % 12) for h in range(12)]
    benefic = {**benefic, "Budha": True}  # Drik: Budha always benefic for bhava drishti
    B["Drishti"] = [sum((1 if benefic[x] else -1) * aspect(x, lon_[x], mad[h], (asc_sign + h) % 12) * (1 if x in ("Guru", "Budha") else 0.25)
                        for x in G) for h in range(12)]
    B["Total Pinda"] = [a + b + c for a, b, c in zip(B["Bhavadhipati"], B["Disha"], B["Drishti"])]
    B["Rupas"] = [t / 60 for t in B["Total Pinda"]]
    order = sorted(range(12), key=lambda i: -B["Total Pinda"][i])
    B["Ranking"] = [order.index(i) + 1 for i in range(12)]
    return B
