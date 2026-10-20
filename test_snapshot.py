"""Snapshot test: every command's --json on FAKE charts vs snapshots/. Offline (explicit lat/lon/tz, no GeoNames).
Run with --update to regenerate after an intended change, then review the diff."""
import json, os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
SNAP = HERE / "snapshots"
CHARTS = {
    "chennai-2000": ["2000-01-01", "12:00", "--lat", "13.08784", "--lon", "80.27847", "--tz", "Asia/Kolkata"],
    "london-1975": ["1975-06-21", "04:30", "--lat", "51.50853", "--lon", "-0.12574", "--tz", "Europe/London"],
    "chicago-1962": ["1962-03-10", "23:45", "--lat", "41.85003", "--lon", "-87.65005", "--tz", "America/Chicago"],
}
CMDS = {
    "chart": ["chart"], "chart-d60": ["chart", "--div", "d60"], "chart-d0": ["chart", "--div", "d0"],
    "panchang": ["panchang"], "dasha": ["dasha", "--depth", "2"], "yogas": ["yogas", "--all"],
    "ashtakavarga": ["ashtakavarga"], "ashtakavarga-drik": ["ashtakavarga", "--drik"], "chart-drik": ["chart", "--drik"],
    "shadbala": ["shadbala"], "bhavabala": ["bhavabala"], "jaimini": ["jaimini"],
    "transits": ["transits", "--at", "2026-01-01T00:00", "--months", "3"],
}


def strip_running(x):
    """Dasha 'running' depends on today's date."""
    if isinstance(x, dict):
        return {k: strip_running(v) for k, v in x.items() if k != "running"}
    if isinstance(x, list):
        return [strip_running(v) for v in x]
    return x


def run(cmd, chart):
    out = subprocess.run([sys.executable, str(HERE / "kundali.py"), cmd[0], *chart, *cmd[1:], "--json"],
                         capture_output=True, text=True, check=True, env={**os.environ, "TZ": "UTC"}).stdout
    return strip_running(json.loads(out))


update = "--update" in sys.argv
SNAP.mkdir(exist_ok=True)
bad = 0
for cname, chart in CHARTS.items():
    for name, cmd in CMDS.items():
        f = SNAP / f"{cname}.{name}.json"
        got = run(cmd, chart)
        if update:
            f.write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n")
        elif json.loads(f.read_text()) != got:
            bad += 1
            print(f"FAIL {f.name}")
print(f"updated {len(CHARTS) * len(CMDS)} snapshots" if update else f"{'ok' if not bad else f'{bad} failed'}")
sys.exit(1 if bad else 0)
