"""Offline place lookup on the GeoNames cities1000 dump (same geoname ids drikpanchang uses).
Downloads ~11 MB once into ~/.cache/kundali/. Only a public file is fetched; no birth data leaves the machine."""
import csv, pathlib, pickle, urllib.request, zipfile

DIR = pathlib.Path.home() / ".cache/kundali"
URL = "https://download.geonames.org/export/dump/"


def _file(name):
    f = DIR / name
    if not f.exists():
        DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL + name, f)
    return f


def _rows():
    idx = DIR / "cities1000.pickle"
    if idx.exists():
        return pickle.loads(idx.read_bytes())
    rows = list(_parse())
    idx.write_bytes(pickle.dumps(rows))
    return rows


def _parse():
    txt = DIR / "cities1000.txt"
    if not txt.exists():
        zipfile.ZipFile(_file("cities1000.zip")).extract("cities1000.txt", DIR)
    countries = {r[0]: r[4] for r in csv.reader(open(_file("countryInfo.txt"), encoding="utf8"), delimiter="\t")
                 if r and not r[0].startswith("#")}
    admin1 = {r[0]: r[1] for r in csv.reader(open(_file("admin1CodesASCII.txt"), encoding="utf8"), delimiter="\t")}
    with open(txt, encoding="utf8") as f:
        for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            yield {"id": r[0], "city": r[1], "ascii": r[2], "lat": float(r[4]), "lon": float(r[5]),
                   "country_code": r[8], "country": countries.get(r[8], r[8]),
                   "state": admin1.get(f"{r[8]}.{r[10]}", r[10]), "state_code": r[10],
                   "elevation": int(r[15] or r[16] or 0), "tz": r[17], "population": int(r[14] or 0)}


def search(name):
    """Exact (case-insensitive) city-name matches, most populous first."""
    n = name.strip().lower()
    return sorted((g for g in _rows() if n in (g["city"].lower(), g["ascii"].lower())),
                  key=lambda g: -g["population"])


def by_id(gid):
    return next((g for g in _rows() if g["id"] == str(gid)), None)


def resolve(place):
    """Geoname id, or "City[, State/Country ...]" -> (place dict, None) or (None, candidates). Never guesses."""
    if place.strip().isdigit():
        g = by_id(place.strip())
        return (g, None) if g else (None, [])
    name, *quals = [x.strip().lower() for x in place.split(",")]
    hits = [g for g in search(name)
            if all(q in (g["state"].lower(), g["state_code"].lower(), g["country"].lower(), g["country_code"].lower())
                   for q in quals)]
    return (hits[0], None) if len(hits) == 1 else (None, hits or search(name))
