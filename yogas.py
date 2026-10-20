"""Classical yogas, rule text = B.V. Raman, "Three Hundred Important Combinations" (as quoted in drikpanchang's
"How Yoga Formed" tooltip), implemented literally, plus bhanga (cancellation) where the classics give one.
Deliberate differences from drikpanchang are listed in DIFFERENCES.

Conventions (all whole-sign, D1 unless a rule names the navamsha):
- "Planets" = the 7 grahas Surya..Shani; Rahu/Ketu only where the rule names them.
- Natural benefics = Guru, Shukra, Budha, and Chandra when waxing; malefics = Surya, Mangal, Shani, Rahu, Ketu.
- Aspects: Parashari full aspects (7th for all, +4/8 Mangal, +5/9 Guru, +3/10 Shani).
- "Powerful"/"strong" graha (rule texts never define it): with `strengths` ({graha: shadbala ratio}),
  ratio >= 1; otherwise not debilitated, not combust, and in own/exaltation sign or a kendra/trikona from Lagna.
"""
import astro, timing

PLANETS = ["Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani"]
NODES = ["Rahu", "Ketu"]
MALEFICS = {"Surya", "Mangal", "Shani", "Rahu", "Ketu"}
EXALT = {"Surya": 0, "Chandra": 1, "Mangal": 9, "Budha": 5, "Guru": 3, "Shukra": 11, "Shani": 6}
ASPECTS = {"Mangal": (4, 7, 8), "Guru": (5, 7, 9), "Shani": (3, 7, 10)}
COMBUST = {"Chandra": 12, "Mangal": 17, "Budha": 14, "Guru": 11, "Shukra": 10, "Shani": 15}  # Surya Siddhanta
KENDRA, TRIKONA = (1, 4, 7, 10), (1, 5, 9)
SOURCE = 'B.V. Raman, "Three Hundred Important Combinations" (text as on drikpanchang)'


class Chart:
    def __init__(self, pos, strengths=None):
        self.lon = {p["graha"]: p["longitude"] for p in pos}
        self.sign = {g: int(l // 30) % 12 for g, l in self.lon.items()}
        self.retro = {p["graha"]: p.get("retro", False) for p in pos}
        self.strengths = strengths

    def h(self, g, ref="Lagna"):
        """House of graha g counted from ref (a graha name or 'Lagna'), 1..12."""
        return (self.sign[g] - self.sign[ref]) % 12 + 1

    def lord(self, house, ref="Lagna"):
        return astro.RASHI_LORD[(self.sign[ref] + house - 1) % 12]

    def in_house(self, house, ref="Lagna", who=PLANETS):
        return [g for g in who if g != ref and self.h(g, ref) == house]

    def own(self, g, sign=None):
        return astro.RASHI_LORD[self.sign[g] if sign is None else sign] == g

    def exalted(self, g):
        return EXALT.get(g) == self.sign[g]

    def debilitated(self, g):
        return g in EXALT and (EXALT[g] + 6) % 12 == self.sign[g]

    def combust(self, g):
        if g not in COMBUST:
            return False
        orb = {"Budha": 12, "Shukra": 8}.get(g, COMBUST[g]) if self.retro.get(g) else COMBUST[g]
        return abs((self.lon[g] - self.lon["Surya"] + 180) % 360 - 180) < orb

    def navamsha(self, g):
        return astro.varga(self.lon[g], 9)

    def aspects(self, g, house_sign):
        """Does graha g aspect the sign house_sign (Parashari full aspect)?"""
        return (house_sign - self.sign[g]) % 12 + 1 in ASPECTS.get(g, (7,))

    def conj(self, a, b):
        return self.sign[a] == self.sign[b]

    def mutual_kendra(self, a, b):
        return self.h(a, b) in KENDRA

    def strong(self, g):
        """'Powerful' -> (bool, why). See module docstring."""
        if self.strengths:
            r = self.strengths[g]
            return r >= 1, f"{g} shadbala ratio {r:.2f} {'>=' if r >= 1 else '<'} 1"
        if self.debilitated(g):
            return False, f"{g} debilitated"
        if self.combust(g):
            return False, f"{g} combust"
        dig = [w for w, ok in (("exalted", self.exalted(g)), ("own sign", self.own(g)),
                               (f"house {self.h(g)}", self.h(g) in KENDRA + TRIKONA)) if ok]
        return bool(dig), f"{g} {'strong: ' + ', '.join(dig) if dig else 'not strong (no own/exalt/kendra/trikona)'}"


FRIENDS = {"Surya": {"Chandra", "Mangal", "Guru"}, "Chandra": {"Surya", "Budha"},
           "Mangal": {"Surya", "Chandra", "Guru"}, "Budha": {"Surya", "Shukra"},
           "Guru": {"Surya", "Chandra", "Mangal"}, "Shukra": {"Budha", "Shani"}, "Shani": {"Budha", "Shukra"}}


def intimate_friend(c, g, other):
    """Adhimitra (BPHS): natural friend AND temporal friend (other in 2,3,4,10,11,12 from g)."""
    return other in FRIENDS[g] and c.h(other, g) in (2, 3, 4, 10, 11, 12)


def benefics(c):
    """Guru, Shukra, Budha, plus Chandra when waxing (Shukla paksha)."""
    waxing = (c.lon["Chandra"] - c.lon["Surya"]) % 360 < 180
    return ["Budha", "Guru", "Shukra"] + (["Chandra"] if waxing else [])


def gulika(jd, lat, lon, h0=None):
    """Gulika = Lagna at the START of Shani's eighth of the day (or night). Segment lords run from the weekday
    lord by day, from the 5th weekday lord by night. Matches Drik's upagraha table to ~0.2 deg (sunrise calibration)."""
    rise, sset, nxt = astro.sun_events(jd, lat, lon, h0)
    wd = (int(rise + 0.5 + lon / 360) + 1) % 7  # 0 = Sunday, local mean date of sunrise
    start, length, i = (rise, (sset - rise) / 8, (6 - wd) % 7) if jd < sset else (sset, (nxt - sset) / 8, (2 - wd) % 7)
    return astro.lagna(start + i * length, lat, lon, astro.ayanamsha(jd))[0]


def _names(gs):
    return ", ".join(gs) or "none"


def lunar(c, houses):
    others = [g for g in PLANETS if g != "Surya"]
    found = {h: c.in_house(h, "Chandra", others) for h in houses}
    return all(found.values()), "; ".join(f"house {h} from Chandra: {_names(v)}" for h, v in found.items())


def solar(c, houses):
    others = [g for g in PLANETS if g != "Chandra"]
    found = {h: c.in_house(h, "Surya", others) for h in houses}
    drik = all(v and c.h("Chandra", "Surya") != h for h, v in found.items())  # Drik: the house must not hold Chandra
    return all(found.values()), "; ".join(f"house {h} from Surya: {_names(v)}" for h, v in found.items()), None, drik


def mahapurusha(g):
    def rule(c, ctx):
        dig = c.own(g) or c.exalted(g)
        return dig and c.h(g) in KENDRA, f"{g} in {astro.RASHIS[c.sign[g]]} (own/exalted: {dig}), house {c.h(g)} from Lagna"
    return rule


# ---- rules: f(c, ctx) -> (present, reason[, cancel_reason]) ----
def r_mangala_dosha(c, ctx):
    h = c.h("Mangal")
    return h in (1, 2, 4, 7, 8, 12), f"Mangal in house {h} from Lagna"


def r_kala_sarpa(c, ctx):
    r = c.lon["Rahu"]
    side = {g: (c.lon[g] - r) % 360 < 180 for g in PLANETS}
    ok = len(set(side.values())) == 1
    hs = [c.h(g, "Rahu") for g in PLANETS]  # Drik: whole signs, a graha sharing Rahu's/Ketu's sign counts as inside
    drik = all(h <= 7 for h in hs) or all(h >= 7 or h == 1 for h in hs)
    return ok, ("all 7 grahas on one side of the Rahu-Ketu axis" if ok else
                f"Rahu->Ketu side: {_names([g for g in PLANETS if side[g]])}; Ketu->Rahu side: "
                f"{_names([g for g in PLANETS if not side[g]])}"), None, drik


def r_lagna_mallika(c, ctx):
    hs = sorted(c.h(g) for g in PLANETS)
    return hs == list(range(1, 8)), f"houses of the 7 grahas from Lagna: {hs}"


def r_gajakesari(c, ctx):
    h = c.h("Guru", "Chandra")
    return h in KENDRA, f"Guru in house {h} from Chandra"


def r_kemadruma(c, ctx):
    others = [g for g in PLANETS if g != "Surya"]
    side = {h: c.in_house(h, "Chandra", others) for h in (2, 12)}
    who = [f"{g} (house {c.h(g)})" for g in others if c.h(g) in KENDRA] + \
          [f"{g} ({c.h(g, 'Chandra')} from Chandra)" for g in others if g != "Chandra" and c.h(g, "Chandra") in KENDRA]
    cancel = f"Kemadruma bhanga (Phaladeepika 6.5): graha in a kendra from Lagna or Chandra: {_names(who)}" if who else None
    return not any(side.values()), "; ".join(f"house {h} from Chandra: {_names(v)}" for h, v in side.items()), cancel


def r_adhi(c, ctx):
    where = {g: c.h(g, "Chandra") for g in benefics(c) if g != "Chandra"}
    return all(h in (6, 7, 8) for h in where.values()), \
        "from Chandra: " + ", ".join(f"{g} {h}" for g, h in where.items())


def r_chatussagara(c, ctx):
    occ = {h: c.in_house(h) for h in KENDRA}
    return all(occ.values()), "; ".join(f"house {h}: {_names(v)}" for h, v in occ.items())


def r_vasumati(c, ctx):
    out = {ref: {g: c.h(g, ref) for g in benefics(c) if g != ref} for ref in ("Lagna", "Chandra")}
    ok = any(all(h in (3, 6, 10, 11) for h in v.values()) for v in out.values())
    return ok, "; ".join(f"from {ref}: " + ", ".join(f"{g} {h}" for g, h in v.items()) for ref, v in out.items())


def r_rajalakshana(c, ctx):
    where = {g: c.h(g) for g in ("Guru", "Shukra", "Budha", "Chandra")}
    return all(h in KENDRA for h in where.values()), "from Lagna: " + ", ".join(f"{g} {h}" for g, h in where.items())


def r_vanchana(c, ctx):
    gs = ctx["gulika_sign"]
    gh = (gs - c.sign["Lagna"]) % 12 + 1
    in_lagna = [g for g in PLANETS + NODES if c.h(g) == 1 and g in MALEFICS]
    a = bool(in_lagna) and gh in (5, 9)
    with_g = [g for g in PLANETS if c.sign[g] == gs]
    kl = {c.lord(h) for h in KENDRA} & set(with_g)
    tl = {c.lord(h) for h in TRIKONA} & set(with_g)
    b = bool(kl or tl)
    l1 = c.lord(1)
    with_l1 = [g for g in ("Rahu", "Shani", "Ketu") if g != l1 and c.conj(g, l1)]
    # Drik reads clause 1 as "a malefic together with Gulika, in a trine (5/9)", ignoring "the Lagna is occupied"
    drik_a = gh in (5, 9) and any(g in MALEFICS for g in PLANETS + NODES if c.sign[g] == gs)
    return a or b or bool(with_l1), (f"malefics in Lagna: {_names(in_lagna)}, Gulika house {gh}; "
                                     f"with Gulika: kendra lords {_names(sorted(kl))}, trikona lords {_names(sorted(tl))}; "
                                     f"Lagna lord {l1} with {_names(with_l1)}"), None, drik_a or b or bool(with_l1)


def r_shakata(c, ctx):
    h = c.h("Chandra", "Guru")
    present = h in (6, 8, 12)
    cancel = (f"Shakata bhanga (Phaladeepika 6.14): Chandra in a kendra (house {c.h('Chandra')}) from Lagna"
              if present and c.h("Chandra") in KENDRA else None)
    return present, f"Chandra in house {h} from Guru", cancel


def r_amala(c, ctx):
    b = benefics(c)
    occ = {ref: [g for g in b if g != ref and c.h(g, ref) == 10] for ref in ("Lagna", "Chandra")}
    return any(occ.values()), "; ".join(f"10th from {r}: {_names(v)}" for r, v in occ.items())


def r_parvata(c, ctx):
    b = benefics(c)
    ben_k = [g for g in b if c.h(g) in KENDRA]
    bad68 = [g for g in PLANETS + NODES if c.h(g) in (6, 8) and g not in b]
    l1, l12 = c.lord(1), c.lord(12)
    alt = c.mutual_kendra(l1, l12)
    return bool(ben_k) and not bad68, (f"benefics in kendras: {_names(ben_k)}; non-benefics in 6/8: "
                                                f"{_names(bad68)}; (minority variant, not applied: lords of 1 ({l1}) and 12 ({l12}) in mutual kendras: {alt})")


def r_kahala(c, ctx):
    l4, l9, l1 = c.lord(4), c.lord(9), c.lord(1)
    mk = c.mutual_kendra(l4, l9)
    st, why = c.strong(l1)
    return mk and st, f"4th lord {l4} house {c.h(l4, l9)} from 9th lord {l9}; {why}"


def r_pushkala(c, ctx):
    d, l1 = c.lord(1, "Chandra"), c.lord(1)
    assoc = c.conj("Chandra", l1)
    placed = c.h(d) in KENDRA or intimate_friend(c, d, astro.RASHI_LORD[c.sign[d]])
    asp = c.sign[d] == c.sign["Lagna"] or c.aspects(d, c.sign["Lagna"])
    strong_in_l = [g for g in PLANETS if c.h(g) == 1 and c.strong(g)[0]]
    return assoc and placed and asp and bool(strong_in_l), (
        f"Chandra with Lagna lord {l1}: {assoc}; dispositor {d} in house {c.h(d)}, kendra or intimate friend's sign: "
        f"{placed}, aspects Lagna: {asp}; powerful grahas in Lagna: {_names(strong_in_l)}")


def r_lakshmi(c, ctx):
    l1, l9 = c.lord(1), c.lord(9)
    st, why = c.strong(l1)
    dig = c.own(l9) or c.exalted(l9)
    place = c.h(l9) in KENDRA + TRIKONA
    return st and dig and place, f"{why}; 9th lord {l9} in house {c.h(l9)}, own/exalted: {dig}"


def r_gauri(c, ctx):
    l10, l1 = c.lord(10), c.lord(1)
    n = astro.RASHI_LORD[c.navamsha(l10)]
    ok = c.h(n) == 10 and c.exalted(n) and c.conj(n, l1)
    return ok, f"10th lord {l10} in navamsha of {n}; {n} in house {c.h(n)}, exalted {c.exalted(n)}, with Lagna lord {l1}: {c.conj(n, l1)}"


def r_bharati(c, ctx):
    l9 = c.lord(9)
    ns = {h: astro.RASHI_LORD[c.navamsha(c.lord(h))] for h in (2, 5, 11)}
    hit = [f"{h}th lord's navamsha lord {n}" for h, n in ns.items() if c.exalted(n) and c.conj(n, l9)]
    return bool(hit), (f"navamsha lords of 2/5/11 lords: " + ", ".join(f"{h}:{n}" for h, n in ns.items()) +
                       f"; exalted and with 9th lord {l9}: {_names(hit)}")


def r_chapa(c, ctx):
    l1, l4, l10 = c.lord(1), c.lord(4), c.lord(10)
    swap = c.h(l4) == 10 and c.h(l10) == 4
    return c.exalted(l1) and swap, f"Lagna lord {l1} exalted: {c.exalted(l1)}; 4th lord {l4} in {c.h(l4)}, 10th lord {l10} in {c.h(l10)}"


def r_shrinatha(c, ctx):
    l7, l9, l10 = c.lord(7), c.lord(9), c.lord(10)
    ok = c.exalted(l7) and c.h(l7) == 10 and c.conj(l10, l9)
    return ok, f"7th lord {l7} exalted {c.exalted(l7)} in house {c.h(l7)}; 10th lord {l10} with 9th lord {l9}: {c.conj(l10, l9)}"


def r_shankha(c, ctx):
    l5, l6, l1 = c.lord(5), c.lord(6), c.lord(1)
    st, why = c.strong(l1)
    return c.mutual_kendra(l5, l6) and st, f"5th lord {l5} house {c.h(l5, l6)} from 6th lord {l6}; {why}"


def r_bheri(c, ctx):
    l1, l9 = c.lord(1), c.lord(9)
    trio = ["Shukra", l1, "Guru"]
    mk = all(c.mutual_kendra(a, b) for a in trio for b in trio)
    st, why = c.strong(l9)
    return mk and st, "Shukra/Lagna lord {}/Guru in houses {}; mutual kendras: {}; {}".format(
        l1, [c.h(g) for g in trio], mk, why)


def r_parijata(c, ctx):
    l1 = c.lord(1)
    d = astro.RASHI_LORD[c.sign[l1]]
    cands = {"dispositor's dispositor": astro.RASHI_LORD[c.sign[d]], "dispositor's navamsha lord": astro.RASHI_LORD[c.navamsha(d)]}
    good = lambda g, ref="Lagna": c.h(g, ref) in KENDRA + TRIKONA or c.own(g) or c.exalted(g)
    hit = [f"{k} {g} (house {c.h(g)})" for k, g in cands.items() if good(g)]
    drik = good(cands["dispositor's dispositor"])  # Drik ignores the navamsha alternative
    return bool(hit), (f"Lagna lord {l1} -> dispositor {d}; " +
                       ", ".join(f"{k} {g} house {c.h(g)}" for k, g in cands.items()) + f"; qualifying: {_names(hit)}"
                       ), None, drik


def r_mahabhagya(c, ctx):
    odd = {g: c.sign[g] % 2 == 0 for g in ("Surya", "Chandra", "Lagna")}
    day = ctx["day"]
    ok = (day and all(odd.values())) if ctx["gender"] == "M" else (not day and not any(odd.values()))
    return ok, f"gender {ctx['gender']}, {'day' if day else 'night'} birth; " + \
        ", ".join(f"{g} {'odd' if o else 'even'}" for g, o in odd.items())


RULES = [  # (name, rule text, implementation note, function)
    ("Mangala Dosha", "When malefic planets specially Mangala Graha, are placed into or aspect the Bhava of marriage, "
     "wealth and comfort, Mangala Dosha is formed.", "Kuja dosha: Mangal in house 1, 2, 4, 7, 8 or 12 from Lagna "
     "(the text's 'aspect' clause would flag Mangal in 9 of 12 houses; Drik, like the classical Kuja dosha, does not)",
     r_mangala_dosha),
    ("Kala Sarpa", "When all planets are situated at one side of the axis joining Rahu and Ketu, Kala Sarpa Yoga is formed.",
     "by longitude, Surya..Shani", r_kala_sarpa),
    ("Lagna Mallika", "If all the seven planets occupy the seven houses contiguously, reckoned from Lagna, the Lagna "
     "Malika Yoga is formed.", "houses 1-7 each hold one of the 7 grahas", r_lagna_mallika),
    ("Gajakesari", "If Jupiter is in a Kendra from the Chandra the combination goes under the name Gajakesari.",
     "Guru in house 1/4/7/10 from Chandra", r_gajakesari),
    ("Sunapha", "If there are planets (excepting the Surya) in the second house from the Chandra, Sunapha is caused.",
     "Mangal..Shani in 2nd from Chandra (nodes never count in these lunar yogas)", lambda c, x: lunar(c, (2,))),
    ("Anapha", "If there are planets in the 12th from the Chandra, Anapha Yoga is formed.",
     "as Sunapha, 12th from Chandra, Surya excepted", lambda c, x: lunar(c, (12,))),
    ("Durdhara", "If there are planets on either side of the Chandra, the combination goes under the name of Dhurdhura.",
     "grahas other than Surya in both 2nd and 12th from Chandra", lambda c, x: lunar(c, (2, 12))),
    ("Kemadruma", "When there are no planets on both sides of the Chandra, Kemadruma Yoga is formed.",
     "no graha other than Surya in 2nd or 12th from Chandra; cancelled by any graha (not Surya/nodes) in a kendra "
     "from Lagna or from Chandra", r_kemadruma),
    ("Chandra Mangala", "If Mangala conjoins the Chandra this yoga is formed.", "same sign", lambda c, x: (
        c.conj("Mangal", "Chandra"), f"Mangal in {astro.RASHIS[c.sign['Mangal']]}, Chandra in {astro.RASHIS[c.sign['Chandra']]}")),
    ("Adhi", "If benefic(s) are situated in the 6th, 7th and 8th from the Chandra, the combination goes under the name "
     "of Adhi Yoga.", "all benefics (Budha, Guru, Shukra) within houses 6-8 from Chandra (jointly or severally)", r_adhi),
    ("Chatussagara", "Chatussagara Yoga is caused when all the Kendra(s) are occupied by planets.",
     "each of houses 1/4/7/10 from Lagna holds one of the 7 grahas", r_chatussagara),
    ("Vasumati", "If benefic(s) occupy the Upachaya(s) (3, 6, 10 and 11) either from the ascendant or from the Chandra, "
     "the combination goes under the name of Vasumathi Yoga.", "all benefics (Budha, Guru, Shukra, waxing Chandra) in "
     "upachayas, all counted from Lagna or all from Chandra (Phaladeepika 6.19: 'all the benefics')", r_vasumati),
    ("Rajalakshana", "Brihaspati, Shukra, Budha and the Chandra should be in Lagna or they should be placed in Kendra.",
     "all four in houses 1/4/7/10 from Lagna", r_rajalakshana),
    ("Vanchana Chora Bheeti", "The Lagna is occupied by a malefic with Gulika in a Trine: or Gulika is associated with "
     "the lords of Kendra(s) and Trikona(s); or the lord of Lagna is combined with Rahu, Shani or Ketu.",
     "malefic (Surya/Mangal/Shani/nodes) in Lagna and Gulika in a trine from it (house 5/9); or Gulika's sign holds any "
     "lord of a kendra or trikona; or Lagna lord shares a sign with Rahu/Shani/Ketu. Gulika: see gulika()", r_vanchana),
    ("Shakata", "The Chandra in the 12th, 6th or 8th from Brihaspati gives rise to Sakata Yoga.",
     "cancelled when Chandra is in a kendra from Lagna", r_shakata),
    ("Amala", "The 10th from the Chandra or Lagna should be occupied by a benefic planet.",
     "Budha/Guru/Shukra (or waxing Chandra) in 10th from Lagna or from Chandra", r_amala),
    ("Parvata", "Benefic(s) being disposed in Kendra(s), the 6th and 8th houses should either be unoccupied or occupied "
     "by benefic planets. This combination goes under the name of Parvata Yoga. According to some, Parvata is also "
     "caused if the lords of Lagna and the 12th are in mutual Kendra(s).",
     "a benefic in a kendra from Lagna and no non-benefic (nodes included) in 6/8; the 'according to some' variant "
     "(lords of 1 and 12 in mutual kendras) is reported but not applied, as Raman gives it only as a minority view",
     r_parvata),
    ("Kahala", "Lords of the fourth and ninth houses should be in Kendras from each other and the lord of Lagna should "
     "be strongly disposed.", "'strongly disposed' = strong() (module docstring)", r_kahala),
    ("Veshi", "If planets other than the Chandra occupy the 2nd from the Surya, Vesi Yoga is formed.",
     "Mangal..Shani (no nodes) in 2nd from Surya", lambda c, x: solar(c, (2,))),
    ("Vasi", "Planets other than the Chandra occupying the 12th from the Surya give rise to Vasi Yoga.",
     "12th from Surya", lambda c, x: solar(c, (12,))),
    ("Obhayachari", "If planets other than the Chandra are present on either side of the Surya, Obhayachari is caused.",
     "both 2nd and 12th from Surya", lambda c, x: solar(c, (2, 12))),
    ("Hansa", "Brihaspati should occupy a Kendra which should be his own house or exaltation sign.",
     "kendra from Lagna", mahapurusha("Guru")),
    ("Malavya", "Shukra should occupy a quadrant which should be his own or exaltation sign.",
     "kendra from Lagna", mahapurusha("Shukra")),
    ("Shasha", "Sasa Yoga is given rise to if Shani occupies a Kendra which should be his own or exaltation sign.",
     "kendra from Lagna", mahapurusha("Shani")),
    ("Ruchaka", "Mangala should be exalted in a Kendra or occupy a Kendra which should be his own sign.",
     "kendra from Lagna", mahapurusha("Mangal")),
    ("Bhadra", "Bhadra Yoga is caused by the disposition of Budha in a Kendra which should be identical with his own or "
     "exaltation sign.", "kendra from Lagna", mahapurusha("Budha")),
    ("Budhaditya", "If Budha combines with the Surya, the combination goes under the name of Budha-Aditya Yoga.",
     "same sign", lambda c, x: (c.conj("Budha", "Surya"), f"Budha in {astro.RASHIS[c.sign['Budha']]}, "
                                                         f"Surya in {astro.RASHIS[c.sign['Surya']]}")),
    ("Mahabhagya", "In the case of a man, when the birth is during daytime the Surya, the Chandra and the Lagna should "
     "be in odd signs. In the case of women, when the birth is during night, the Surya, the Chandra and Lagna must be "
     "in even signs.", "day = between astro.sun_events sunrise and sunset; uses the gender argument", r_mahabhagya),
    ("Pushkala", "The lord of the sign occupied by the Chandra (who should be associated with lord of Lagna) should be "
     "in Kendra or in the house of an intimate friend aspecting Lagna and at the same time, Lagna should be occupied by "
     "a powerful planet.", "Chandra conjunct Lagna lord; Chandra's dispositor in a kendra or in an adhimitra's sign "
     "(natural + temporal friend), and in or aspecting Lagna; a strong() graha in Lagna", r_pushkala),
    ("Lakshmi", "If the lord of Lagna is powerful and the lord of 9th occupies own or exaltation sign identical with a "
     "Kendra or Trikona, Lakshmi Yoga is caused.", "Lagna lord strong(); 9th lord in own/exaltation sign that is house "
     "1/4/5/7/9/10 from Lagna", r_lakshmi),
    ("Gauri", "The lord of the Navamsha occupied by the lord of the 10th should join the 10th in exaltation and combined "
     "with the lord of Lagna.", "D9 dispositor of the 10th lord: in house 10, exalted, same sign as Lagna lord", r_gauri),
    ("Bharati", "The lord of the Navamsha occupied by the lords of the 2nd, 5th, and 11th should be exalted and combined "
     "with the 9th lord.", "for any of the 2nd/5th/11th lords, its D9 dispositor is exalted and shares a sign with the "
     "9th lord", r_bharati),
    ("Chapa", "If the ascendant lord is exalted and the 4th and 10th lords have interchanged houses, Chapa Yoga is caused.",
     "4th lord in 10th and 10th lord in 4th", r_chapa),
    ("Shrinatha", "If the exalted lord of the 7th occupies the 10th and the lord of the 10th is with the 9th lord, "
     "Shrinatha Yoga is caused.", "'with' = same sign", r_shrinatha),
    ("Shankha", "The lords of 5th and 6th should be in mutual Kendra(s) and the lord of Lagna must be powerful.",
     "'powerful' = strong()", r_shankha),
    ("Bheri", "If Shukra, lord of Lagna and Brihaspati are in mutual Kendra(s) and the lord of the 9th is powerfully "
     "disposed, Bheri Yoga is formed.", "every pair of the three in houses 1/4/7/10 from each other; 9th lord strong()",
     r_bheri),
    ("Parijata", "The lord of the sign in which the lord of the house occupied by the Lagna lord, or the lord of Navamsha "
     "occupied by the lord of the Rashi in which the Lagna lord is posited, shall join a Kendra, a Trikona or his own or "
     "exaltation places.", "D = Lagna lord's dispositor; D's dispositor or D's navamsha lord in house 1/4/5/7/9/10, "
     "own sign or exaltation", r_parijata),
]


def yogas(pos, jd, lat, lon, gender="M", strengths=None, elevation=0.0):
    """All 37 yogas drikpanchang tests -> [{yoga, present, reason, cancelled, cancel_reason, rule, source}].
    pos = astro.positions(...); strengths = optional {graha: shadbala ratio} for 'powerful' tests;
    elevation (m) feeds Drik's sunrise rule (day/night birth, Gulika)."""
    c = Chart(pos, strengths)
    h0 = timing.sun_h0(elevation)  # Drik's sunrise convention
    rise, sset, _ = astro.sun_events(jd, lat, lon, h0)
    ctx = {"gender": gender.upper()[:1], "day": rise <= jd < sset, "gulika_sign": int(gulika(jd, lat, lon, h0) // 30)}
    out = []
    for name, text, note, f in RULES:
        present, reason, cancel, alt = (list(f(c, ctx)) + [None, None])[:4]
        out.append({"yoga": name, "present": bool(present), "reason": reason, "cancelled": bool(present and cancel),
                    "cancel_reason": cancel if present else None,
                    "rule": f"{text} [implemented as: {note}]", "source": SOURCE + (
                        "; bhanga: Mantreswara, Phaladeepika ch.6" if f in (r_kemadruma, r_shakata) else ""),
                    "_drik_reading": alt})  # what drikpanchang's apparent (non-literal) reading gives; None = not modelled
    return out


# Deliberate departures from drikpanchang; every disagreement with Drik was classified against these.
# Evidence = fake test charts, whole-sign houses.
DIFFERENCES = {
    "bhanga": "a cancelled yoga is reported as not in effect; Drik shows it present (it applies no bhanga)",
    "gender": "Mahabhagya uses the native's gender; Drik always applies the male rule",
}
# Drik follows a different reading of the same text; the rule returns that reading as _drik_reading.
READINGS = {
    "Kala Sarpa": "we cut at the Rahu-Ketu axis by longitude; Drik works in whole signs, so a graha in Rahu's sign "
                  "but behind him still counts as hemmed in (NYC 2016-02-25: Guru R in Simha behind Rahu)",
    "Veshi": "Drik also requires that Chandra is NOT in that house (Sydney 1935-06-03: Budha 2nd from Surya, "
             "but Chandra is there too; Drik says absent)",
    "Vasi": "as Veshi", "Obhayachari": "as Veshi",
    "Vanchana Chora Bheeti": "Drik reads clause 1 as 'a malefic with Gulika, in a trine' and drops 'the Lagna is "
                             "occupied' (New Delhi 1978-02-07: Lagna empty, Gulika with Shani in the 9th; Drik present)",
    "Parijata": "Drik ignores the navamsha alternative (Tokyo 1932-07-14: the dispositor's navamsha lord Chandra is in "
                "the 5th, Drik says absent); its flag matches the dispositor's-dispositor clause in 8 of 9 charts",
}
# Drik's flag contradicts its own tooltip text and no reading of the text reproduces it -> we keep the text.
# value = (Drik values excused, evidence)
OFF_TEXT = {
    "Amala": ({True, False}, "no hypothesis fits (10th from Lagna/Chandra, any offset, with/without Chandra): "
              "Chennai 1928-08-30 is flagged with both 10ths empty (Lagna Mithuna -> Meena, Chandra Makara -> Tula), "
              "Tokyo 1932-07-14 is not flagged with Guru 10th from Chandra"),
    "Parvata": ({True, False}, "London 2011-01-18 (Budha/Guru/Chandra in kendras, 6th and 8th empty) not flagged; "
                "Tokyo 1932-07-14 flagged with Rahu in the 8th"),
    "Kahala": ({True}, "London 2011-01-18 flagged although the 4th lord Guru (Meena) is 11th from the 9th lord "
               "Surya (Makara), not in a kendra"),
    "Shankha": ({True}, "Tokyo 1932-07-14 flagged with the Lagna lord Chandra debilitated in Vrishchika: Drik's "
                "'powerful' is not ours (see Chart.strong)"),
    "Lakshmi": ({True}, "NYC 2016-02-25 flagged with the 9th lord Surya in Kumbha (neither own nor exalted); Drik "
                "flags Lakshmi where its own text fails"),
    "Parijata": ({True}, "Drik flags it where neither clause holds (dispositor's dispositor and dispositor's "
                 "navamsha lord both outside kendra/trikona/own/exaltation)"),
}


def explain_difference(y, drik_present, gender="M"):
    """Which documented difference explains our flag differing from Drik's, or None (= unexplained)."""
    if y["cancelled"] and drik_present and y["present"]:
        return f"bhanga: {y['cancel_reason']}"
    if y["yoga"] == "Mahabhagya" and gender != "M":
        return "gender: " + DIFFERENCES["gender"]
    if y["yoga"] in READINGS and y["_drik_reading"] == drik_present:
        return "Drik's reading: " + READINGS[y["yoga"]]
    if y["yoga"] in OFF_TEXT and drik_present in OFF_TEXT[y["yoga"]][0]:
        return "Drik contradicts its text: " + OFF_TEXT[y["yoga"]][1]
    return None
