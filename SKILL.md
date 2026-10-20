---
name: kundali
description: Generate Vedic/Jyotish birth charts (kundali) LOCALLY via the `kundali` CLI (Swiss Ephemeris; no birth data leaves the machine) — graha positions, D1 + any divisional chart D2–D60 + Bhav Chalit, planet/house tables (dignity, relationship, aspects, combustion), upagrahas, Vimshottari dasha to prana, birth panchang, classical yogas with cancellations (bhanga), ashtakavarga, shadbala, bhavabala. Classical conventions by default; `--drik` reproduces drikpanchang.com. Use for any kundali, birth chart, navamsha, dasha, yoga, or planetary-position request.
---

# kundali

A local Jyotish engine. Its numbers reproduce drikpanchang.com: the conventions were reverse-engineered and checked cell by cell against Drik on **fake** charts during development (that oracle harness is not shipped). The CLI makes no network calls except a one-time GeoNames download.

```bash
kundali city springfield                                 # offline GeoNames lookup (same ids as Drik)
kundali chart 2000-01-01 12:00 "Chennai"                 # positions, D1 + D9, dignities, upagrahas (--json)
kundali chart 2000-01-01 12:00 1264527 --div d10         # any of d0 (Bhav Chalit), d2..d60
kundali chart 2000-01-01 12:00 --lat 13.08784 --lon 80.27847 --tz Asia/Kolkata [--elevation 6]
kundali panchang  <date> <time> <place>                  # tithi, nakshatra, yoga, karana, ishta kala, gana, nadi...
kundali dasha     <date> <time> <place> [--depth 1-5] [--running]
kundali yogas     <date> <time> <place> [--all] [--explain] [--gender F]
kundali ashtakavarga | shadbala | bhavabala <date> <time> <place>
kundali transits  <date> <time> <place> [--at YYYY-MM-DD[THH:MM]] [--months 12]   # gochara vs natal, Sade Sati, ingresses/stations
kundali jaimini   <date> <time> <place> [--eight]   # chara karakas, karakamsha, ishta/dharma/palana devata, nakshatra deity
```
Every command takes `--json`, `--drik` and `--ayanamsha` (chitra-paksha = Lahiri [default], bv-ramana, krishnamurthi-paddhati, tropical).

**Default is classical**:
- true local sidereal time for Lagna and houses
- the birthplace meridian for Nata/Unnata bala
- BPHS ashtakavarga
- classical Chesta bala and classical yogas with cancellations (bhanga)

**`--drik`** reproduces drikpanchang's quirks:
- Lagna and houses from longitude × 1.0027. That shifts Lagna about 16′ at Delhi and up to 0.4° in the Americas, roughly 1 minute of birth time. It flips the D60 Lagna about half the time, D27/D40/D45 a third of the time, and D9 to D12 about 10%.
- the time-zone meridian for Nata/Unnata
- Drik's buggy ashtakavarga tables

With `--drik`, everything matches Drik except Chesta and yogas, which are always classical.

High vargas (D24 and up) need a birth time accurate to seconds in either mode: ±2 minutes of birth time moves the Lagna about ±30′.

The place can be a geoname id or "City, State/Country". When the name is ambiguous the CLI lists the candidates and exits 2, and never guesses.

## Rules for agents
- Every value you report must come from `kundali` output, copied verbatim. Use `--json` when another step consumes it. Never compute, estimate or "correct" a value by hand. If the CLI errors, say so and stop.
- If the place is ambiguous (exit 2), ask the user which candidate. Never pick one.
- Shadbala and bhavabala rows marked **†** use classical Chesta bala and therefore differ from Drik by design (see Accuracy). Say so when you quote them.
- Yogas: quote `--explain`, which gives the reason, rule text and source. Interpretation is a separate step and must be labelled as interpretation.
- Jaimini karakas MUST come from D1 degrees (`kundali jaimini`). Never read them off a navamsha table: those longitudes are D9 values, and another LLM got the Atmakaraka wrong exactly that way. When the 12th from Karakamsha holds several grahas, the texts say take the strongest; the CLI doesn't decide that, so don't pick one silently.
- Birth data is private. Never send it to drikpanchang or any other service. The CLI never does.

## Accuracy vs Drik (measured during development on fake charts)
| Section | Status |
|---|---|
| Positions | Surya..Shani ≤3″, Moon ≤8″ (≤40″ after 2020; Drik's ΔT differs), Lagna ≤45″, mean Rahu ≤20″. Drik's Pluto is up to 1° off (not compared). |
| D2–D60, Bhav Chalit | exact (19 vargas × 5–12 charts; chalit = Sripati, 8 charts) |
| Planet/house tables, combustion | exact, 30k cells / 36 charts |
| Upagrahas | exact, 36 charts |
| Panchang, dasha | Dasha dates differ from Drik by minutes to hours: 1″ of Moon ≈ 3.7 h of dasha time, and that sits within ephemeris noise |
| Ashtakavarga | exact, 2664 cells / 9 charts. The default reproduces 2 Drik bugs (the Lagna column counts the 3rd house twice and the 10th never; the reduced "Sarv *" column is a meaningless fold). The classical default fixes both; `--drik` reproduces them. |
| Yogas | classical by design: 311 agree with Drik, 22 differ intentionally (bhanga, Drik misreading Raman's text, Drik contradicting its own text), 0 unexplained |
| Shadbala/Bhavabala | 1781/2412 values exact. 622 differ **by design**: classical Chesta for Mangal..Shani (Drik's values exceed the formula's 60 maximum and invert it, e.g. they halve a retrograde Guru at opposition), and Budha as benefic where Drik flips him. The test proves every one of these is caused by those two choices alone. 9 bhava-Drishti values are off by ≤0.02 (Drik-internal rounding). |

## Drik conventions (reverse-engineered; details in each module's docstring)
- Ayanamsha = MEAN Lahiri (SIDM_LAHIRI_VP285) subtracted from apparent tropical longitudes.
- Lagna: Drik converts the birthplace longitude to sidereal time at the sidereal rate (lon × 1.0027379). This is strictly a bug, worth up to 0.4° in the Americas; we match it.
- Sunrise: Sun-centre altitude −0.8333° − 0.0373°·√(elevation in m). Elevation is used even though the browser shows "elevation disabled".
- Combustion is heliacal (asta), judged by the Sun's depression at the planet's rise or set. It is not a fixed degree orb.
- Bhavadhipati = the lord of the sign on the Sripati bhava madhya, not the whole-sign house. Dasha year = 365.25636 days. Nata/Unnata uses the time-zone meridian. Hora uses unequal planetary hours. Ahargana epoch is BV Raman's.

## Files
`kundali.py` CLI · `astro.py` core (positions, vargas, sunrise) · `places.py` GeoNames (~/.cache/kundali) · `timing.py` panchang/upagrahas/dasha · `details.py` tables/combustion/chalit · `yogas.py` · `ashtakavarga.py` · `shadbala.py` · `transits.py` · `jaimini.py`

Tests (offline): `test_transits.py`, `test_jaimini.py` (self-checks) and `test_snapshot.py` (every command's `--json` on fake charts vs `snapshots/`; `--update` to regenerate after an intended change).
Run: `for t in test_*.py; do uv run --quiet --with pyswisseph python3 $t || echo "FAIL $t"; done`
