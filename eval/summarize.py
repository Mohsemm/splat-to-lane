"""dump all the results csvs into SUMMARY.md"""
import csv
import glob
import os
import re

R = "lane/results"
def table(path, title):
    if not os.path.exists(path):
        return f"\n## {title}\n(missing: {path})\n"
    rows = list(csv.reader(open(path)))
    out = f"\n## {title}\n`{path}`\n\n| " + " | ".join(rows[0]) + " |\n|" + "---|" * len(rows[0]) + "\n"
    return out + "".join("| " + " | ".join(r) + " |\n" for r in rows[1:])
md = "# Street-in-3D night run summary (2026-10-28/29)\n\nOffsets in cm = mean absolute error of the lane-position net on REAL frames; walks at 0.03 / 0.93 / 1.93 / 3.07 m (COLMAP). " \
     "Caveats: R trained on walk 2; G2/B worlds saw walk 2; closed loops run inside splat worlds (render domain).\n"
md += table(f"{R}/real_errors.csv", "First run: W / G / G2 / R on real walks")
md += table(f"{R}/robust_summary.csv", "Seeds (3 per net) + W warp height 1.2 / 1.6 m (mean +- std cm)")
md += table(f"{R}/closed_loop_summary.csv", "Closed loop, target 0 m (walk-0 line), 10 starts/net/world")
md += table(f"{R}/cl_road_summary.csv", "Closed loop, target 1.5 m (in the road), 10 starts/net/world")
for q, t in (("quality_q1", "Q1 strict world A (points seen only by walk 0)"), ("quality_q2", "Q2 splatfacto-big worlds"),
             ("quality_q3", "Q3 20k renders, 30 epochs"), ("quality_all", "ALL variants (seed mean +- std where available)")):
    md += table(f"{R}/{q}.csv", t)
for c in sorted(glob.glob("eval/by_offset_*.csv")):
    rows = list(csv.DictReader(open(c))); acc = {}
    for r in rows: acc.setdefault(r["walk"], []).append(float(r["psnr"]))
    md += f"\nRender quality {os.path.basename(c)}: " + ", ".join(f"{w} {sum(v)/len(v):.2f} dB" for w, v in sorted(acc.items())) + "\n"
for f in ("q3_choice.txt", "q4_pick.txt"):
    if os.path.exists(f"{R}/{f}"): md += f"\n{f}: " + open(f"{R}/{f}").read().replace("\n", "; ") + "\n"
md += "\n## Job durations and temperatures\n"
for lg in sorted(glob.glob("logs/*-2026102*.log")):
    t = open(lg, errors="ignore").read()
    durs = re.findall(r"== DURATION (\S+) (\d+) s", t)
    temps = [float(x) for x in re.findall(r"== GPU [^:]+:[^:]*: ([0-9.]+),", t)]
    flags = [l for l in t.splitlines() if l.startswith("== FAILED") or l.startswith("== ABORT") or "skipped" in l]
    if durs or temps or flags:
        md += f"- {os.path.basename(lg)}: " + ", ".join(f"{n} {int(s)//60}m{int(s)%60:02d}s" for n, s in durs) + \
              (f" | max logged GPU {max(temps):.1f} C" if temps else "") + (f" | {'; '.join(flags)}" if flags else "") + "\n"
md += "\nFiles: lane/results/ (plots *.png, videos *.mp4, demo_hd.mp4), lane/models/, exports/street_all_1080b/{splat,splat_yup}.ply\n"
open(f"{R}/SUMMARY.md", "w").write(md)
print("== SUMMARY.md written")
