"""Time-based Jyotish on astro.py: sunrise/sunset, birth panchang, upagrahas, Vimshottari dasha.
Drik conventions (reverse-engineered, checked against Drik during development):
- Sunrise/sunset: Sun's CENTRE at true altitude h0 = -0.8333 - 0.0373*sqrt(elevation m) degrees
  (refraction + semidiameter, plus a horizon dip that grows with the place's elevation). Fitted on 37 charts,
  14 m..2854 m (Quito pins the coefficient). Residual: rise and set both shifted by the same +-7 s per chart.
- Ishta Kala = 30 ghati * (birth - sunrise) / (sunset - sunrise) [day birth];
  Ahoratri Ishta Kala = 60 ghati * (birth - sunrise) / (next sunrise - sunrise).
- Upagrahas: day (night) split in 8 equal parts; part lords cycle Sun..Saturn + one lordless part, starting
  with the weekday lord by day and the 5th lord from it (in the 7-lord cycle) by night. Kala, Mrityu,
  Ardha Prahara, Yama Ghantaka, Gulika = Lagna at the START of the part of Sun, Mars, Mercury, Jupiter, Saturn.
  Mandi = Lagna at (16k - 7)/120 of the day (night), k = Saturn's part index (Drik-specific; fitted).
  Dhuma = Sun + 133.33 (decimal, not 133 deg 20'), Upaketu = Indra Chapa + 16.67.
- Vimshottari: year = 365.25636 days (sidereal), periods laid end to end from birth - elapsed balance,
  shown in local time TRUNCATED to the second; sub-periods are laid out from the parent's displayed bounds,
  and an exact whole second displays one lower (see _sec), so deeper levels drift a second per level.
- Panchang: Tara counted from Ashwini (nakshatra index % 9); Vashya from the Moon's sign at sunrise.
"""
import datetime, math, zoneinfo
import swisseph as swe
import astro

DIP = 0.0373  # deg per sqrt(metre) of elevation, fitted to Drik


def sun_h0(elevation=0.0):
    return astro.SUN_H0 - DIP * math.sqrt(max(float(elevation), 0.0))


def local(jd, tz):
    y, m, d, h = swe.revjul(jd)
    u = datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=h)
    return u.astimezone(zoneinfo.ZoneInfo(tz))


def asc_at(t, lat, lon):
    return astro.lagna(t, lat, lon, astro.ayanamsha(t))[0]


def day_parts(jd, lat, lon, tz, elevation=0.0):
    """-> (rise, set, next rise, start of birth's day-or-night half, its length, weekday 0=Sun, is_day)."""
    rise, set_, nxt = astro.sun_events(jd, lat, lon, sun_h0(elevation))
    wd = (local(rise, tz).weekday() + 1) % 7
    day = jd < set_
    return rise, set_, nxt, rise if day else set_, (set_ - rise) if day else (nxt - set_), wd, day


# ---- upagrahas ---------------------------------------------------------------------------------------
PART_LORDS = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani", None]
UPAGRAHA_OF = {"Kala": "Surya", "Mrityu": "Mangal", "Ardha Prahara": "Budha", "Yama Ghantaka": "Guru",
               "Gulika": "Shani"}


def upagraha_times(jd, lat, lon, tz, elevation=0.0):
    """-> {name: JD UT} at which the Lagna-based upagrahas rise."""
    rise, set_, nxt, a, span, wd, day = day_parts(jd, lat, lon, tz, elevation)
    first = wd if day else (wd + 4) % 7
    seq = [PART_LORDS[(first + i) % 8] for i in range(8)]
    out = {n: a + span * seq.index(g) / 8 for n, g in UPAGRAHA_OF.items()}
    out["Mandi"] = a + span * (16 * seq.index("Shani") - 7) / 120
    return out


def upagrahas(jd, lat, lon, tz, elevation=0.0):
    """-> {name: sidereal longitude} for Drik's 11 upagrahas."""
    out = {n: asc_at(t, lat, lon) for n, t in upagraha_times(jd, lat, lon, tz, elevation).items()}
    sun = (swe.calc_ut(jd, swe.SUN)[0][0] - astro.ayanamsha(jd)) % 360
    out["Dhuma"] = (sun + 133.33) % 360
    out["Vyatipata"] = (360 - out["Dhuma"]) % 360
    out["Parivesha"] = (out["Vyatipata"] + 180) % 360
    out["Indra Chapa"] = (360 - out["Parivesha"]) % 360
    out["Upaketu"] = (out["Indra Chapa"] + 16.67) % 360
    return out


# ---- panchang ----------------------------------------------------------------------------------------
WEEKDAYS = ["Raviwara", "Somawara", "Mangalawara", "Budhawara", "Guruwara", "Shukrawara", "Shaniwara"]
TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami",
          "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"]
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti", "Shula",
         "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana",
         "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
SIGNS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara",
         "Kumbha", "Meena"]
PAYA = ["Golden", "Silver", "Copper", "Iron"]
RASHI_PAYA = {1: 0, 6: 0, 11: 0, 2: 1, 5: 1, 9: 1, 3: 2, 7: 2, 10: 2, 4: 3, 8: 3, 12: 3}  # Moon's house from Lagna
TATTVA = ["Fiery", "Earthy", "Airy", "Watery"]
VARNA = ["Kshatriya", "Vaishya", "Shudra", "Brahmin"]
TARAS = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyaka", "Sadhana", "Naidhana", "Mitra", "Parama Mitra"]
YONI = ["Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat", "Rat", "Rat", "Cow",
        "Buffalo", "Tiger", "Buffalo", "Tiger", "Hare", "Hare", "Dog", "Monkey", "Mongoose", "Monkey", "Lion",
        "Horse", "Lion", "Cow", "Elephant"]
GANA = "DMRMDMDDRRMMDRDRDRRMMDRRMMD"  # Deva / Manava / Rakshasa per nakshatra
GANAS = {"D": "Deva", "M": "Manava", "R": "Rakshasa"}
NADIS = ["Aadi", "Madhya", "Antya"]


def ghati(x):
    """Ghatis -> 'GG Ghati PP Pala VV Vipala' (truncated)."""
    v = int(x * 3600 + 1e-6)
    return f"{v // 3600} Ghati {v // 60 % 60:02d} Pala {v % 60:02d} Vipala"


def hhmm(jd, tz):
    t = local(jd + 30 / 86400, tz)  # Drik rounds to the minute
    return t.strftime("%I:%M %p , %b %d")


def full(name):
    return name.replace("P ", "Purva ").replace("U ", "Uttara ")


def nakshatra_paya(n):
    # ponytail: fitted on 9 charts (Ardra/Hasta Silver, Anuradha Iron, Shravana..U Bhadrapada Copper); Golden
    # block and the Iron/Copper edges are unverified
    return "Golden" if n in (26, 0, 1, 2, 3, 4) else "Silver" if n <= 15 else "Iron" if n <= 20 else "Copper"


def yunja(n):
    # ponytail: 6/12/9 split (Revati.., Ardra.., Jyeshtha..); Madhya 5/12/16 and Antya 21/22/25 verified
    return "Purva" if n in (26, 0, 1, 2, 3, 4) else "Madhya" if n <= 16 else "Antya"


def vashya(lon):
    k, half = int(lon // 30), lon % 30 >= 15
    if k == 8:
        return "Chatushpada" if half else "Manava"
    if k == 9:
        return "Jalachara" if half else "Chatushpada"
    return ["Chatushpada", "Chatushpada", "Manava", "Jalachara", "Vanachara", "Manava", "Manava", "Keeta",
            None, None, "Manava", "Jalachara"][k].replace("Keeta", "Keet")


def panchang(jd, lat, lon, tz, elevation=0.0):
    """Birth panchang, keys as Drik's kundali 'panchangam' tab."""
    rise, set_, nxt, a, span, wd, day = day_parts(jd, lat, lon, tz, elevation)
    pos = {p["graha"]: p for p in astro.positions(jd, lat, lon, outer=False)}
    sun, moon, lag = pos["Surya"]["longitude"], pos["Chandra"]["longitude"], pos["Lagna"]["longitude"]
    # Drik takes Vashya from the Moon's sign at the Hindu day's SUNRISE (fits 9/9; London 2011 is the tell)
    moon_rise = (swe.calc_ut(rise, swe.MOON)[0][0] - astro.ayanamsha(rise)) % 360
    el = (moon - sun) % 360
    t = int(el // 12)
    k = int(el // 6)
    nm, ns = (int(x // (360 / 27)) for x in (moon, sun))
    ms = int(moon // 30)
    ishta = 30 * (jd - rise) / (set_ - rise) if day else 30 + 30 * (jd - set_) / (nxt - set_)
    return {
        "Sunrise": hhmm(rise, tz), "Sunset": hhmm(set_, tz),
        "Ishta Kala": ghati(ishta), "Ahoratri Ishta Kala": ghati(60 * (jd - rise) / (nxt - rise)),
        "Weekday": WEEKDAYS[wd],
        "Tithi": "Purnima" if t == 14 else "Amavasya" if t == 29 else TITHIS[t % 15],
        "Paksha": "Shukla Paksha" if t < 15 else "Krishna Paksha",
        "Nakshatra": full(astro.NAKSHATRAS[nm]),
        "Yoga": YOGAS[int((sun + moon) % 360 // (360 / 27))],
        "Karana": "Kimstughna" if k == 0 else "Shakuni" if k == 57 else "Chatushpada" if k == 58
        else "Naga" if k == 59 else KARANAS[(k - 1) % 7],
        "Moonsign": SIGNS[ms], "Sunsign": SIGNS[int(sun // 30)],
        "Surya Nakshatra": full(astro.NAKSHATRAS[ns]),
        "Rashi Paya": PAYA[RASHI_PAYA[(ms - int(lag // 30)) % 12 + 1]],
        "Nakshatra Paya": nakshatra_paya(nm),
        "Tattva": TATTVA[ms % 4], "Yunja": yunja(nm), "Varna": VARNA[ms % 4], "Vashya": vashya(moon_rise),
        "Tara": TARAS[nm % 9],  # counted from Ashwini (fitted on 9 charts; Naidhana/Parama Mitra spellings unverified)
        "Yoni": YONI[nm], "Gana": GANAS[GANA[nm]], "Nadi": NADIS[[0, 1, 2, 2, 1, 0][nm % 6]],
    }


# ---- Vimshottari dasha -------------------------------------------------------------------------------
YEAR = 365.25636  # days; Drik's "sidereal-year"
LEVELS = ["maha", "antara", "pratyantara", "sookshma", "prana"]


def _sec(jd):
    """Drik's displayed dasha second: truncated, and an exact whole second shows one second LOWER (its
    string->time->string round trip lands a hair below the integer). Sub-periods are then laid out from
    these displayed parent bounds, so each level can lose a second."""
    return (math.ceil(jd * 86400 - 1e-4) - 1) / 86400


def _fmt(jd, tz):
    return local(_sec(jd) + 1e-3 / 86400, tz).strftime("%d/%m/%Y %H:%M:%S")  # +1 ms: revjul jitter


def dasha(jd, moon_longitude, tz, depth=2, now=None, running_only=False):
    """Vimshottari periods like drik.dasha(): [{lord, begins, ends, running, sub}], times local
    'dd/mm/YYYY HH:MM:SS'. now = JD UT for the running flag (default: current time)."""
    if now is None:
        u = datetime.datetime.now(datetime.timezone.utc)
        now = swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)
    span = 360 / 27
    n = int(moon_longitude // span)
    start_lord = n % 9
    start = jd - (moon_longitude % span) / span * astro.DASHA_YEARS[start_lord] * YEAR

    def walk(lord0, begin, length, level):
        out, t = [], begin
        for i in range(9):
            j = (lord0 + i) % 9
            d = length * astro.DASHA_YEARS[j] / 120
            p = {"lord": astro.DASHA_LORDS[j], "begins": _fmt(t, tz), "ends": _fmt(t + d, tz),
                 "running": t <= now < t + d}
            if level < depth and (p["running"] or not running_only):
                rb, re_ = _sec(t), _sec(t + d)  # Drik subdivides the parent's begin/end as displayed (whole seconds)
                p["sub"] = walk(j, rb, re_ - rb, level + 1)
            out.append(p)
            t += d
        return out
    return walk(start_lord, start, 120 * YEAR, 1)
