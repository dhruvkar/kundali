"""Ashtakavarga (BPHS ch. 66-70): bhinna tables, Sarvashtakavarga, Trikona/Ekadhipatya shodhana, Shodhya pinda.
Output mirrors drikpanchang's three tables (checked against Drik during development)."""
from astro import RASHIS

ORDER = ["Lagna", "Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani"]
CONTRIB = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani", "Lagna"]
# BENEFIC[x][i]: houses (a repeat counts twice), counted from CONTRIB[i], where x gets a bindu. Lagna's own row = BPHS 66.
BENEFIC = {
    "Surya": [[1, 2, 4, 7, 8, 9, 10, 11], [3, 6, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [3, 5, 6, 9, 10, 11, 12],
              [5, 6, 9, 11], [6, 7, 12], [1, 2, 4, 7, 8, 9, 10, 11], [3, 4, 6, 10, 11, 12]],
    "Chandra": [[3, 6, 7, 8, 10, 11], [1, 3, 6, 7, 10, 11], [2, 3, 5, 6, 9, 10, 11], [1, 3, 4, 5, 7, 8, 10, 11],
                [1, 4, 7, 8, 10, 11, 12], [3, 4, 5, 7, 9, 10, 11], [3, 5, 6, 11], [3, 6, 10, 11]],
    "Mangal": [[3, 5, 6, 10, 11], [3, 6, 11], [1, 2, 4, 7, 8, 10, 11], [3, 5, 6, 11],
               [6, 10, 11, 12], [6, 8, 11, 12], [1, 4, 7, 8, 9, 10, 11], [1, 3, 6, 10, 11]],
    "Budha": [[5, 6, 9, 11, 12], [2, 4, 6, 8, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 3, 5, 6, 9, 10, 11, 12],
              [6, 8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 2, 4, 6, 8, 10, 11]],
    "Guru": [[1, 2, 3, 4, 7, 8, 9, 10, 11], [2, 5, 7, 9, 11], [1, 2, 4, 7, 8, 10, 11], [1, 2, 4, 5, 6, 9, 10, 11],
             [1, 2, 3, 4, 7, 8, 10, 11], [2, 5, 6, 9, 10, 11], [3, 5, 6, 12], [1, 2, 4, 5, 6, 7, 9, 10, 11]],
    "Shukra": [[8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11, 12], [3, 5, 6, 9, 11, 12], [3, 5, 6, 9, 11],
               [5, 8, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9, 10, 11], [3, 4, 5, 8, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9, 11]],
    "Shani": [[1, 2, 4, 7, 8, 10, 11], [3, 6, 11], [3, 5, 6, 10, 11, 12], [6, 8, 9, 10, 11, 12],
              [5, 6, 11, 12], [6, 11, 12], [3, 5, 6, 11], [1, 3, 4, 6, 10, 11]],
    "Lagna": [[3, 4, 6, 10, 11, 12], [3, 6, 10, 11, 12], [1, 3, 6, 10, 11], [1, 2, 4, 6, 8, 10, 11],
              [1, 2, 4, 5, 6, 7, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9], [1, 3, 4, 6, 10, 11], [3, 3, 6, 11]],
}  # Drik quirk: Lagna-from-Lagna counts the 3rd twice and never the 10th (BPHS: 3,6,10,11); fitted on 9 charts
RASHI_MANA = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]
GRAHA_MANA = {"Surya": 5, "Chandra": 5, "Mangal": 8, "Budha": 5, "Guru": 10, "Shukra": 7, "Shani": 5}
TWO_SIGNS = [(0, 7), (1, 6), (2, 5), (8, 11), (9, 10)]  # Mangal, Shukra, Budha, Guru, Shani


def bhinna(sign, classical=False):
    """sign: {contributor: rashi index} -> {graha: [12 bindus]}. classical: BPHS Lagna-from-Lagna 3,6,10,11."""
    table = {**BENEFIC, "Lagna": BENEFIC["Lagna"][:7] + [[3, 6, 10, 11]]} if classical else BENEFIC
    return {g: [sum(table[g][i].count((r - sign[c]) % 12 + 1) for i, c in enumerate(CONTRIB)) for r in range(12)]
            for g in ORDER}


def trikona(v):
    v = v[:]
    for k in range(4):
        m = min(v[k], v[k + 4], v[k + 8])
        for j in (k, k + 4, k + 8):
            v[j] -= m
    return v


def ekadhipatya(v, occupied):
    v = v[:]
    for a, b in TWO_SIGNS:
        if not v[a] or not v[b] or (a in occupied and b in occupied):
            continue
        if a not in occupied and b not in occupied:
            v[a] = v[b] = 0 if v[a] == v[b] else min(v[a], v[b])
        else:
            o, e = (a, b) if a in occupied else (b, a)
            v[e] = 0 if v[e] <= v[o] else v[o]
    return v


def ashtakavarga(pos, classical=False):
    """classical=True fixes Drik's two bugs: BPHS Lagna-from-Lagna houses, and reduced Sarv = sum of reduced rows."""
    sign = {p["graha"]: p["rashi_index"] for p in pos}
    bav = bhinna(sign, classical)
    occupied = {sign[g] for g in CONTRIB if g != "Lagna"}
    red = {g: ekadhipatya(trikona(v), occupied) for g, v in bav.items()}
    sarv = [sum(bav[g][r] for g in ORDER[1:]) for r in range(12)]
    # Drik quirk: its reduced "Sarv" column is not the sum of the reduced rows but the two shodhanas applied to
    # (SAV - 1) mod 12 -- SAV folded like a sign count. Fitted exactly on 9 charts; meaningless, but it's what Drik shows.
    rsarv = ([sum(red[g][r] for g in ORDER[1:]) for r in range(12)] if classical
             else ekadhipatya(trikona([(x - 1) % 12 for x in sarv]), occupied))
    head = [""] + ORDER + ["Sarv *"]
    table = lambda t, s: [head] + [[RASHIS[r].capitalize()] + [t[g][r] for g in ORDER] + [s[r]] for r in range(12)]
    rp = {g: sum(a * b for a, b in zip(red[g], RASHI_MANA)) for g in ORDER}
    gp = {g: sum(red[g][sign[x]] * m for x, m in GRAHA_MANA.items()) for g in ORDER}
    return {"Ashtakavarga": table(bav, sarv), "Reduced Ashtakavarga": table(red, rsarv),
            "Shodhya Pinda": [[""] + ORDER, ["Rashi"] + [rp[g] for g in ORDER], ["Graha"] + [gp[g] for g in ORDER],
                              ["Shodhya"] + [rp[g] + gp[g] for g in ORDER]]}
