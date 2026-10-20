"""Jaimini chara karakas, Karakamsha and the devata indications built on them.

Karakas use D1 degrees within the sign (NOT a divisional chart's longitudes; a common error is reading them off a
navamsha table). Rahu's degree is counted backwards (30 - d) in the 8-karaka scheme.
Devata indications, each labelled with its school:
- Ishta: 12th from Karakamsha in D9 (Jaimini Upadesa Sutras, karakamsha section; BPHS karakamsha chapter).
- Dharma devata: 9th from the Atmakaraka in D9; Palana devata: 6th from the Amatyakaraka in D9 (Sanjay Rath school).
- Janma nakshatra presiding deity (standard Vedic list).
Occupants are listed in full; when there are several the texts say "the strongest", which this module does NOT
decide (Jaimini strength isn't implemented). Empty house -> its lord.
"""
import astro

KARAKAS = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka"]
KARAKAS8 = KARAKAS[:4] + ["Pitrikaraka"] + KARAKAS[4:]
SEVEN = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani"]

# Planet in (or lord of) the house -> deity. Classical = Jaimini sutras as standardly rendered
# ("ravau shiva-bhaktih, chandre gauryam, shukre lakshmyam, kuje skande, budha-shanyor vishnau, gurau sambashive,
#  rahau tamasyam durgayam, ketau ganeshe skande cha; papa-rkshe mande kshudra-devatasu").
DEITY = {"Surya": "Shiva", "Chandra": "Gauri (Parvati)", "Mangal": "Skanda (Subrahmanya)", "Budha": "Vishnu",
         "Guru": "Sambasiva (Shiva with Uma)", "Shukra": "Lakshmi", "Rahu": "Durga (tamasic form)",
         "Ketu": "Ganesha and Skanda",
         "Shani": "Vishnu"}
MALEFIC_SIGNS = {0, 4, 7, 9, 10}  # signs of Mangal, Surya, Shani (Mesha, Simha, Vrishchika, Makara, Kumbha)
NAK_DEITY = ["Ashwini Kumaras", "Yama", "Agni", "Brahma (Prajapati)", "Soma", "Rudra", "Aditi", "Brihaspati",
             "Sarpas (Nagas)", "Pitris", "Bhaga", "Aryaman", "Savitr", "Tvashtr (Vishvakarma)", "Vayu", "Indragni",
             "Mitra", "Indra", "Nirriti", "Apas", "Vishvedevas", "Vishnu", "Vasus", "Varuna", "Aja Ekapada",
             "Ahirbudhnya", "Pushan"]


def karakas(pos, eight=False):
    deg = {p["graha"]: p["longitude"] % 30 for p in pos if p["graha"] in SEVEN}
    if eight:
        deg["Rahu"] = 30 - next(p["longitude"] for p in pos if p["graha"] == "Rahu") % 30
    names = KARAKAS8 if eight else KARAKAS
    ranked = sorted(deg, key=lambda g: -deg[g])
    return [{"karaka": names[i], "graha": g, "degree": astro.body("", deg[g])["dms_in_rashi"]}
            for i, g in enumerate(ranked)]


def _house(d9, start, n, label, method):
    """n-th sign from `start` in D9 -> occupants (or lord) and the deity each indicates."""
    sign = (start + n - 1) % 12
    occ = [g for g, s in d9.items() if s == sign and g != "Lagna"]
    via = occ or [astro.RASHI_LORD[sign]]
    deity = {g: ("kshudra (minor) devatas: Shani in a malefic sign (else Vishnu); schools differ"
                 if g == "Shani" and sign in MALEFIC_SIGNS else DEITY[g]) for g in via}
    return {"indication": label, "method": method, "d9_sign": astro.RASHIS[sign], "occupants": occ,
            "used": "occupants" if occ else "lord (house empty)", "deities": deity}


def jaimini(pos, eight=False):
    ks = karakas(pos, eight)
    d9 = {p["graha"]: astro.varga(p["longitude"], 9) for p in pos if p["graha"] in SEVEN + ["Rahu", "Ketu", "Lagna"]}
    ak, amk = ks[0]["graha"], ks[1]["graha"]
    kk = d9[ak]
    moon = next(p for p in pos if p["graha"] == "Chandra")
    lag = next(p for p in pos if p["graha"] == "Lagna")["rashi_index"]
    d1 = {p["graha"]: p["rashi_index"] for p in pos}
    parashari = [{"house": h, "rashi": astro.RASHIS[(lag + h - 1) % 12], "lord": astro.RASHI_LORD[(lag + h - 1) % 12],
                  "occupants": [g for g in SEVEN + ["Rahu", "Ketu"] if d1[g] == (lag + h - 1) % 12]} for h in (5, 9)]
    return {"scheme": "8 karakas (Rahu included)" if eight else "7 karakas",
            "karakas": ks, "karakamsha": astro.RASHIS[kk],
            "devatas": [
                _house(d9, kk, 12, "Ishta devata (moksha)", "12th from Karakamsha in D9 (Jaimini/BPHS)"),
                _house(d9, d9[ak], 9, "Dharma devata", "9th from Atmakaraka in D9 (Sanjay Rath school)"),
                _house(d9, d9[amk], 6, "Palana devata (sustenance)", "6th from Amatyakaraka in D9 (Sanjay Rath school)")],
            "janma_nakshatra": {"nakshatra": moon["nakshatra"],
                                "deity": NAK_DEITY[astro.NAKSHATRAS.index(moon["nakshatra"])]},
            "d1_5th_9th": parashari}
