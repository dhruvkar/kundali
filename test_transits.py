"""Self-check for transits.py: ingress/station instants bracket the change; Sade Sati spans hold Shani in 12/1/2."""
import astro, transits as T

jd0 = astro.jd_ut("2026-01-01", "00:00", "UTC")
for g in ("Surya", "Guru", "Shani", "Rahu"):
    for e in T.events(g, jd0, jd0 + 400):
        before, after = T.sid(e["jd"] - 1e-3, g), T.sid(e["jd"] + 1e-3, g)
        if e["event"] == "enters":
            assert int(before[0] // 30) != int(after[0] // 30) and astro.RASHIS[int(after[0] // 30)] == e["rashi"], e
        else:
            assert (before[1] < 0) != (after[1] < 0), e
moon = 2  # Mithuna
for s, t in T.sade_sati(moon, jd0 - 9000, jd0 + 9000):
    mid = (s + (t or s + 1)) / 2
    assert (int(T.sid(mid, "Shani")[0] // 30) - moon) % 12 in T.SADE_SATI
# well-known: Makar Sankranti (Surya enters Makara) falls on 14/15 January
mk = [e for e in T.events("Surya", jd0, jd0 + 365) if e["rashi"] == "makara"][0]
assert T.local_str(mk["jd"], "Asia/Kolkata")[:10] in ("2026-01-14", "2026-01-15"), mk
print("ok")
