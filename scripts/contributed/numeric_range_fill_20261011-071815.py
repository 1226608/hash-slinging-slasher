"""Every number in a numbered family's range, and a little past its end, in the family's own padding.

`ui_playercard_<n>`, `i/sticker_iw9_<n>`, `mtl_..._body_<nnnn>_m1_v2`: a family is a modern
image/material name with one 3-5 digit token cut out (prefix, suffix). Neighbour methods step +-k
from known numbers; this fills the whole range 1..max+--past for every family with >= --min known
numbers, at each zero-padded width the family is seen in. Seeds are every modern name known.

    python contrib/numeric_range_fill.py | confirm_list - --game BLACKOP7

Spent by: the image/material corpus as it stands; re-run after it grows (new maxima extend ranges).
"""
from collections import defaultdict
from pathlib import Path
import argparse
import re
import sys

ROOT = Path(__file__).resolve().parent
while not (ROOT / "scripts" / "snapshot.py").is_file() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
TABLES = {"image": "fnv1a_ximages_v2.csv", "material": "fnv1a_xmaterials_v2.csv"}
NUM = re.compile(r"(?:(?<=_)|(?<=/)|^)(\d{1,5})(?=_|$)")


def names():
    for kind, table in TABLES.items():
        srcs = [ROOT / "cod-name-db" / "csv" / table]
        for folder in ("findings", "submissions", "all_names"):
            srcs += list((ROOT / folder).rglob(kind + "*.txt"))
        for p in srcs:
            if not p.is_file():
                continue
            for line in p.open(encoding="utf-8", errors="replace"):
                k, sep, v = line.rstrip("\r\n").partition(",")
                v = (v if sep else k).strip().lower()
                if v and "~" not in v[1:] and "*" not in v:
                    yield v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--past", type=int, default=300)
    ap.add_argument("--cap", type=int, default=20000, help="skip families whose range is wider")
    a = ap.parse_args()
    fam = defaultdict(set)
    widths = defaultdict(set)
    known = set()
    for n in names():
        known.add(n)
        for m in NUM.finditer(n):
            key = (n[:m.start()], n[m.end():])
            fam[key].add(int(m.group(1)))
            widths[key].add(len(m.group(1)) if m.group(1).startswith("0") else 0)
    out = 0
    for key, nums in fam.items():
        if len(nums) < a.min or max(nums) + a.past > a.cap:
            continue
        pre, suf = key
        for i in range(0, max(nums) + a.past + 1):
            for w in widths[key]:
                c = f"{pre}{i:0{w}d}{suf}" if w else f"{pre}{i}{suf}"
                if c not in known:
                    print(c)
                    out += 1
    print(f"{out:,} candidates", file=sys.stderr)


if __name__ == "__main__":
    main()
