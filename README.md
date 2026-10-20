# kundali

A local Vedic astrology (Jyotish) engine and CLI. It computes the chart on your machine with the Swiss Ephemeris. Birth data never leaves the machine.

It's also packaged as an agent skill (`SKILL.md`) for Claude Code and other agents that read skills.

## What it computes

- Planet positions, D1 and every divisional chart D2 to D60, plus the Bhav Chalit
- Planet and house tables: dignity, relationship, aspects, combustion
- Upagrahas (sub-planets such as Gulika)
- Birth panchang
- Vimshottari dasha down to the prana level
- Classical yogas, with their cancellation (bhanga) rules
- Ashtakavarga
- Shadbala and bhavabala (planet and house strength)
- Jaimini chara karakas, karakamsha and devatas
- Transits (gochara), Sade Sati, ingresses and stations

Two modes:

- **Classical** (the default): true local sidereal time, BPHS ashtakavarga tables, classical Chesta bala and yogas.
- **`--drik`**: reproduces [drikpanchang.com](https://www.drikpanchang.com)'s output, quirks included.

During development the numbers were checked cell by cell against Drik, using made-up charts only. `SKILL.md` has the accuracy table and the conventions that were reverse-engineered.

## Install

Needs [uv](https://docs.astral.sh/uv/). `kundali.py` is a uv script, so `pyswisseph` installs itself on first run.

```bash
git clone https://github.com/dhruvkar/kundali ~/.claude/skills/kundali   # or anywhere
ln -s ~/.claude/skills/kundali/kundali.py ~/.local/bin/kundali
```

The first place lookup downloads the GeoNames `cities1000` dump (about 11 MB) into `~/.cache/kundali/`. To skip it, pass `--lat/--lon/--tz` instead of a place name.

## Usage

```bash
kundali city springfield                          # list matching places (an ambiguous name is never guessed)
kundali chart 2000-01-01 12:00 "Chennai"          # positions + D1 + D9
kundali chart 2000-01-01 12:00 1264527 --div d10 --json
kundali dasha 2000-01-01 12:00 "Chennai" --running
kundali yogas 2000-01-01 12:00 "Chennai" --explain
kundali transits 2000-01-01 12:00 "Chennai" --months 12
kundali shadbala|bhavabala|ashtakavarga|jaimini|panchang <date> <time> <place>
```

Every command takes `--json`, `--drik` and `--ayanamsha`. The ayanamsha choices are `chitra-paksha` (Lahiri, the default), `bv-ramana`, `krishnamurthi-paddhati` and `tropical`.

## Tests

```bash
for t in test_*.py; do uv run --quiet --with pyswisseph python3 $t || echo "FAIL $t"; done
```

`test_snapshot.py` runs every command on three made-up charts and compares the results with `snapshots/`. After an intended change, regenerate them with `--update` and review the diff.

## License

AGPL-3.0, because the Swiss Ephemeris (via `pyswisseph`) is AGPL-3.0, or commercially licensed by [Astrodienst](https://www.astro.com/swisseph/). Place data comes from [GeoNames](https://www.geonames.org/) under CC BY 4.0.
