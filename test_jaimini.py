"""Self-check for jaimini.py on a hand-built chart (no oracle: Drik's kundali page has no karaka table)."""
import astro, jaimini

lon = {"Lagna": 165, "Surya": 350, "Chandra": 215, "Mangal": 325, "Budha": 335, "Guru": 148, "Shukra": 13,
       "Shani": 25, "Rahu": 126, "Ketu": 306}
pos = [astro.body(g, l) for g, l in lon.items()]
r = jaimini.jaimini(pos)
assert [k["graha"] for k in r["karakas"]] == ["Guru", "Mangal", "Shani", "Surya", "Shukra", "Chandra", "Budha"]
assert r["karakamsha"] == astro.RASHIS[astro.varga(148, 9)] == "dhanu"
ishta = r["devatas"][0]
assert ishta["d9_sign"] == "vrishchika" and set(ishta["occupants"]) == {
    g for g in lon if g != "Lagna" and astro.varga(lon[g], 9) == 7}
assert r["janma_nakshatra"] == {"nakshatra": "Anuradha", "deity": "Mitra"}
r8 = jaimini.jaimini(pos, eight=True)
assert [k["graha"] for k in r8["karakas"]][:4] == ["Guru", "Mangal", "Shani", "Rahu"]  # Rahu 30-6 = 24 > Surya 20
print("ok")
