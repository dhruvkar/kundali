#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyswisseph"]
# ///
"""Vedic kundali, computed locally (Swiss Ephemeris). No birth data leaves the machine.
Default = classical conventions (true sidereal time, BPHS tables). --drik reproduces drikpanchang.com exactly
(verified by test_*.py against Drik on fake charts) apart from the deliberate classical choices (Chesta, yogas).

  kundali city springfield                             # list places (offline GeoNames)
  kundali chart 2000-01-01 12:00 "Chennai"            # positions + D1 + D9
  kundali chart 2000-01-01 12:00 1264527 --div d10 --json
  kundali chart 2000-01-01 12:00 --lat 13.08784 --lon 80.27847 --tz Asia/Kolkata
"""
import argparse, datetime, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import astro, ashtakavarga, details, jaimini, places, transits, shadbala, timing, yogas

ABBR = {"Surya": "Su", "Chandra": "Mo", "Mangal": "Ma", "Budha": "Me", "Guru": "Ju",
        "Shukra": "Ve", "Shani": "Sa", "Rahu": "Ra", "Ketu": "Ke"}
DIV_NAMES = {1: "Rashi", 2: "Hora", 3: "Dreshkana", 4: "Chaturthamsha", 5: "Panchamsha", 6: "Shashthamsha",
             7: "Saptamsha", 8: "Ashtamsha", 9: "Navamsha", 10: "Dashamsha", 11: "Rudramsha", 12: "Dwadashamsha",
             16: "Shodashamsha", 20: "Vimshamsha", 24: "Chaturvimshamsha", 27: "Saptavimshamsha",
             30: "Trimshamsha", 40: "Khavedamsha", 45: "Akshavedamsha", 60: "Shashtiamsha"}


def south_grid(hs):
    """South-Indian chart: fixed rashi boxes, Mesha top row second from left."""
    by = {h["rashi"]: h for h in hs}
    lag = hs[0]["rashi"]
    cell = lambda r: (("Asc " if r == lag else "") + " ".join(ABBR.get(x, x[:2]) for x in by[r]["residents"])).strip()
    order = [[11, 0, 1, 2], [10, None, None, 3], [9, None, None, 4], [8, 7, 6, 5]]
    w = 16
    line = "+" + ("-" * w + "+") * 4
    rows = [line]
    for rr in order:
        rows.append("|" + "|".join((astro.RASHIS[i].title() if i is not None else "").ljust(w) for i in rr) + "|")
        rows.append("|" + "|".join((cell(astro.RASHIS[i]) if i is not None else "").ljust(w) for i in rr) + "|")
        rows.append(line)
    return "\n".join(rows)


def birth(a, p):
    """Validate input and resolve the place -> dict(jd, lat, lon, tz, place)."""
    try:
        datetime.date.fromisoformat(a.date)
        datetime.time.fromisoformat(a.time)
    except ValueError as e:
        p.error(f"date must be YYYY-MM-DD, time HH:MM[:SS]: {e}")
    if a.lat is not None or a.lon is not None or a.tz:
        if None in (a.lat, a.lon) or not a.tz:
            p.error("--lat, --lon and --tz go together")
        g = {"id": None, "city": a.place or "", "lat": a.lat, "lon": a.lon, "tz": a.tz, "elevation": a.elevation or 0}
    else:
        if not a.place:
            p.error("give a place (geoname id or 'City, State/Country') or --lat/--lon/--tz")
        g, cands = places.resolve(a.place)
        if g is None:
            print(f"'{a.place}' matched {len(cands)} places; pass a geoname id or add ', State' / ', Country':",
                  file=sys.stderr)
            for c in cands[:30]:
                print(c["id"], c["city"], c["state"], c["country"], c["tz"], sep="\t", file=sys.stderr)
            sys.exit(2)
    jd = astro.jd_ut(a.date, a.time, g["tz"])
    elev = a.elevation if a.elevation is not None else g.get("elevation", 0)
    return {"jd": jd, "lat": g["lat"], "lon": g["lon"], "tz": g["tz"], "elevation": elev,
            "place": {**{k: g.get(k) for k in ("id", "city", "state", "country", "lat", "lon", "tz")}, "elevation": elev}}


def cmd_chart(a, b):
    jd, lat, lon = b["jd"], b["lat"], b["lon"]
    pos = astro.positions(jd, lat, lon, a.ayanamsha, a.rahu)
    for p_, c in ((p_, details.combust(jd, lat, lon, pos)) for p_ in pos):
        p_["combust"] = c.get(p_["graha"], False)
    n = int(a.div[1:])
    if n == 0:
        div = {"title": "Bhav Chalit Chart - BC", "houses": details.bhav_chalit(jd, lat, lon, pos)}
    else:
        div = {"title": f"{DIV_NAMES[n]} Chart - D{n}", "houses": astro.chart_houses(pos, n),
               "planet_table": details.planet_table(pos, n), "house_table": details.house_table(pos, n)}
    r = {"input": {"date": a.date, "time": a.time, "ayanamsha": a.ayanamsha, "rahu": a.rahu, "classical": a.classical,
                   **b["place"]},
         "positions": pos,
         "d1": {"title": "Rashi Chart - D1", "houses": astro.chart_houses(pos, 1),
                "planet_table": details.planet_table(pos, 1), "house_table": details.house_table(pos, 1)},
         a.div: div,
         "upagrahas": {k: astro.body(k, v) for k, v in
                       timing.upagrahas(jd, lat, lon, b["tz"], b["elevation"]).items()}}
    if a.json:
        return r
    dig = {row["graha"]: row for row in r["d1"]["planet_table"]}
    for p_ in pos:
        t = dig.get(p_["graha"], {})
        print(f"{p_['graha']:<9}{p_['rashi']:<11}{p_['dms_in_rashi']:>11}  {p_['nakshatra'] + ' ' + str(p_['pada']):<16}"
              f"{p_['nakshatra_lord']:<8}{'R' if p_['retro'] else ' '}{'C' if p_['combust'] else ' '}  "
              f"{t.get('is_in', ''):<10}{t.get('relationship', ''):<16}{t.get('dignity', '') if t.get('dignity') != '-' else ''}")
    print(f"\n{r['d1']['title']}\n{south_grid(r['d1']['houses'])}")
    if n == 0:  # chalit bhavas don't align with signs, so list them instead of drawing the sign grid
        print(f"\n{div['title']}  (bhava: starts at, residents)")
        for h in div["houses"]:
            print(f"  {h['bhava']:>2}  {astro.RASHIS[int(h['start'] // 30)]:<11}{astro.body('', h['start'])['dms_in_rashi']:>11}"
                  f"  {', '.join(h['residents'])}")
    else:
        print(f"\n{div['title']}\n{south_grid(div['houses'])}")


def cmd_panchang(a, b):
    r = timing.panchang(b["jd"], b["lat"], b["lon"], b["tz"], b["elevation"])
    if a.json:
        return r
    for k, v in r.items():
        print(f"{k:<22}{v}")


def print_dasha(ds, indent=0):
    for d in ds:
        print(f"{'  ' * indent}{'*' if d['running'] else ' '} {d['lord']:<9}{d['begins']}  ->  {d['ends']}")
        print_dasha(d.get("sub", []), indent + 1)


def cmd_dasha(a, b):
    moon = next(p["longitude"] for p in astro.positions(b["jd"], b["lat"], b["lon"], a.ayanamsha) if p["graha"] == "Chandra")
    r = timing.dasha(b["jd"], moon, b["tz"], a.depth, running_only=a.running)
    if a.json:
        return r
    print_dasha(r)


def cmd_yogas(a, b):
    pos = astro.positions(b["jd"], b["lat"], b["lon"], a.ayanamsha)
    ys = [{k: v for k, v in y.items() if not k.startswith("_")}
          for y in yogas.yogas(pos, b["jd"], b["lat"], b["lon"], a.gender, elevation=b["elevation"])]
    ys = [y for y in ys if a.all or y["present"]]
    if a.json:
        return ys
    for y in ys:
        state = "cancelled" if y["present"] and y["cancelled"] else "present" if y["present"] else "absent"
        print(f"{state:<10}{y['yoga']}")
        if a.explain:
            print(f"          why: {y['reason']}")
            if y["cancelled"]:
                print(f"          cancelled: {y['cancel_reason']}")
            print(f"          rule: {y['rule']}\n          source: {y['source']}")


def cmd_ashtakavarga(a, b):
    r = ashtakavarga.ashtakavarga(astro.positions(b["jd"], b["lat"], b["lon"], a.ayanamsha), a.classical)
    if a.json:
        return r
    for title, rows in r.items():
        print(f"\n{title}")
        for row in rows:
            print(str(row[0]).ljust(12) + "".join(str(c)[:8].rjust(9) for c in row[1:]))
    if not a.classical:
        print("\n--drik: Drik's tables reproduced, bugs included (the Lagna column counts the 3rd house twice and not "
              "the 10th; the reduced 'Sarv *' column is not the sum of the reduced rows).")


def cmd_jaimini(a, b):
    r = jaimini.jaimini(astro.positions(b["jd"], b["lat"], b["lon"], a.ayanamsha), a.eight)
    if a.json:
        return r
    print(f"Chara karakas ({r['scheme']}; D1 degree within sign):")
    for k in r["karakas"]:
        print(f"  {k['karaka']:<14}{k['graha']:<9}{k['degree']}")
    print(f"\nKarakamsha (Atmakaraka's D9 sign): {r['karakamsha']}\n")
    for d in r["devatas"]:
        print(f"{d['indication']}: {d['method']}")
        print(f"  D9 sign {d['d9_sign']}; occupants: {', '.join(d['occupants']) or 'none'} -> using {d['used']}")
        for g, deity in d["deities"].items():
            print(f"    {g:<8}-> {deity}")
    jn = r["janma_nakshatra"]
    print(f"\nJanma nakshatra {jn['nakshatra']}: presiding deity {jn['deity']}")
    print("\nD1 5th / 9th from Lagna (Parashari mantra / dharma houses):")
    for h in r["d1_5th_9th"]:
        print(f"  {h['house']}th {h['rashi']}: lord {h['lord']}; occupants: {', '.join(h['occupants']) or 'none'}")
    print("\nSeveral occupants: the texts say take the strongest; that isn't decided here. "
          "Deity mapping = classical Jaimini; other schools differ (esp. Shani).")


def cmd_transits(a, b):
    if a.at:
        at = datetime.datetime.fromisoformat(a.at)
        at = (at if at.tzinfo else at.astimezone()).astimezone(datetime.timezone.utc)
    else:
        at = datetime.datetime.now(datetime.timezone.utc)
    jd = astro.swe.julday(at.year, at.month, at.day, at.hour + at.minute / 60 + at.second / 3600)
    natal = astro.positions(b["jd"], b["lat"], b["lon"], a.ayanamsha)
    r = transits.transits(natal, jd, a.ayanamsha, a.classical)
    moon = next(p["rashi_index"] for p in natal if p["graha"] == "Chandra")
    ev = sorted((e for g in transits.NINE if g != "Chandra"
                 for e in transits.events(g, jd, jd + a.months * 30.44, a.ayanamsha)), key=lambda e: e["jd"])
    for e in ev:
        e["when"] = transits.local_str(e["jd"])
        e["house_from_moon"] = (astro.RASHIS.index(e["rashi"]) - moon) % 12 + 1
    ss = [{"from": transits.local_str(s), "to": transits.local_str(t) if t else "beyond range"}
          for s, t in transits.sade_sati(moon, jd - 30 * 365.25, jd + 30 * 365.25, a.ayanamsha)]
    r.update({"at": transits.local_str(jd), "events": ev, "sade_sati_periods": ss})
    if a.json:
        return r
    print(f"Transits at {r['at']} (houses counted from natal Lagna {astro.RASHIS[(next(p for p in natal if p['graha'] == 'Lagna'))['rashi_index']]} "
          f"and natal Moon {astro.RASHIS[moon]})\n")
    print(f"{'graha':<9}{'rashi':<12}{'deg':>11}  {'nakshatra':<17}R  fromLagna fromMoon  good?  bindus  SAV")
    for x in r["rows"]:
        print(f"{x['graha']:<9}{x['rashi']:<12}{x['dms_in_rashi']:>11}  {x['nakshatra']:<17}{'R' if x['retro'] else ' '}"
              f"  {x['house_from_lagna']:>9}{x['house_from_moon']:>9}  {'yes' if x['favourable_from_moon'] else 'no':<5}"
              f"  {x['bindus'] if x['bindus'] is not None else '-':>6}  {x['sav']:>3}")
    print(f"\nSade Sati now: {r['sade_sati_now'] or 'no'}")
    print("Sade Sati periods (Shani in 12th/1st/2nd from Moon), +-30 years:")
    for s in ss:
        print(f"  {s['from']}  ->  {s['to']}")
    print(f"\nNext {a.months} months (Moon omitted):")
    for e in ev:
        print(f"  {e['when']}  {e['graha']:<7}{e['event']:<17}{e['rashi']:<11}({e['house_from_moon']} from Moon)")
    print("\ngood? = classical favourable houses from the Moon (Phaladeepika gochara; vedha not applied). "
          "bindus = that graha's ashtakavarga points in the sign (0-8; 4+ is good), SAV = sarva total (28+ is good).")


# Rows that use CLASSICAL Chesta bala for Mangal..Shani (by design: Drik's values can't be the classical formula,
# see shadbala.py) and so differ from Drik's.
UNVERIFIED = {"Chesta", "Total Pinda", "Rupas", "Strength Ratio", "Ishta Phala", "Kashta Phala",
              "Relative Rank", "Bhavadhipati", "Ranking"}


def cmd_bala(a, b):
    off = datetime.datetime.fromisoformat(f"{a.date}T{a.time}").replace(
        tzinfo=__import__("zoneinfo").ZoneInfo(b["tz"])).utcoffset().total_seconds() / 3600
    pos = astro.positions(b["jd"], b["lat"], b["lon"], a.ayanamsha)
    fn = shadbala.shadbala if a.cmd == "shadbala" else shadbala.bhavabala
    rows = fn(b["jd"], b["lat"], b["lon"], pos, off, b["elevation"])
    if a.json:
        return {"rows": rows, "classical_chesta_rows": sorted(UNVERIFIED & set(rows))}
    cols = shadbala.G if a.cmd == "shadbala" else ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
    print(" " * 18 + "".join(c[:8].rjust(9) for c in cols))
    for k, v in rows.items():
        fmt = (lambda x: f"{x:.0f}") if k in ("Relative Rank", "Ranking", "Bhava (in %)") else \
              (lambda x: f"{x:.4f}") if k == "Strength Ratio" else (lambda x: f"{x:.2f}")
        print(f"{k + (' †' if k in UNVERIFIED else ''):<18}" + "".join(fmt(x).rjust(9) for x in v))
    print("\n† uses classical Chesta bala for Mangal..Shani (by design); Drik's values for these rows differ"
          + (" (with --drik, all other rows match Drik)" if a.classical else "; all other rows match Drik"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("city", help="list places matching a city name (offline GeoNames)")
    c.add_argument("query")
    bp = argparse.ArgumentParser(add_help=False)
    bp.add_argument("date", help="YYYY-MM-DD")
    bp.add_argument("time", help="HH:MM[:SS] local birth time")
    bp.add_argument("place", nargs="?", help='geoname id, or "City, State" / "City, Country" (must be unambiguous)')
    bp.add_argument("--lat", type=float); bp.add_argument("--lon", type=float)
    bp.add_argument("--tz", help="olson zone, e.g. Asia/Kolkata (with --lat/--lon)")
    bp.add_argument("--elevation", type=float, help="metres; affects sunrise (default: GeoNames value, or 0)")
    bp.add_argument("--ayanamsha", default="chitra-paksha", choices=list(astro.AYANAMSHA))
    bp.add_argument("--drik", action="store_true",
                    help="reproduce drikpanchang's quirks instead of the classical default: Lagna/houses from longitude "
                         "x 1.0027 sidereal time, time-zone meridian for Nata/Unnata, Drik's buggy ashtakavarga tables")
    bp.add_argument("--json", action="store_true")
    k = sp.add_parser("chart", parents=[bp], help="positions + D1 + a divisional chart")
    k.add_argument("--div", default="d9", choices=[f"d{n}" for n in [0] + astro.DIVISIONS], help="d0 = Bhav Chalit")
    k.add_argument("--rahu", default="mean-rahu", choices=["mean-rahu", "true-rahu"])
    sp.add_parser("panchang", parents=[bp], help="birth panchang: tithi, nakshatra, yoga, karana, gana, nadi...")
    d = sp.add_parser("dasha", parents=[bp], help="Vimshottari dasha (* = running now)")
    d.add_argument("--depth", type=int, default=2, choices=range(1, 6), help="1 maha .. 5 prana; default 2")
    d.add_argument("--running", action="store_true", help="only drill into the running periods")
    y = sp.add_parser("yogas", parents=[bp], help="classical yogas (Raman's rules + bhanga); present/cancelled")
    y.add_argument("--gender", default="M", choices=["M", "F"], help="Mahabhagya differs by gender")
    y.add_argument("--all", action="store_true", help="also list absent yogas")
    y.add_argument("--explain", action="store_true", help="show which grahas/houses satisfied the rule, rule text, source")
    sp.add_parser("ashtakavarga", parents=[bp], help="ashtakavarga, reduced, shodhya pinda")
    t = sp.add_parser("transits", parents=[bp], help="gochara: current transits vs the natal chart, Sade Sati, ingresses")
    t.add_argument("--at", help="YYYY-MM-DD[THH:MM] (machine-local time) instead of now")
    t.add_argument("--months", type=int, default=12, help="look-ahead for ingresses/stations (default 12)")
    j = sp.add_parser("jaimini", parents=[bp], help="chara karakas, karakamsha, ishta/dharma/palana devata")
    j.add_argument("--eight", action="store_true", help="8-karaka scheme (Rahu included, degree reversed)")
    for name in ("shadbala", "bhavabala"):
        sp.add_parser(name, parents=[bp], help=f"{name} († rows use classical Chesta)")
    a = p.parse_args()

    if a.cmd == "city":
        for g in places.search(a.query):
            print(g["id"], g["city"], g["state"], g["country"], g["tz"], sep="\t")
        return
    a.classical = not a.drik
    astro.CLASSICAL = a.classical
    b = birth(a, p)
    r = {"chart": cmd_chart, "panchang": cmd_panchang, "dasha": cmd_dasha,
         "yogas": cmd_yogas, "ashtakavarga": cmd_ashtakavarga, "jaimini": cmd_jaimini, "transits": cmd_transits, "shadbala": cmd_bala, "bhavabala": cmd_bala}[a.cmd](a, b)
    if r is not None:
        print(json.dumps(r, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
