"""Weapon sound files mirrored between the player and NPC folders: `<dir>/<base>.<tail>` <->
`<dir>/npc/<base>_npc.<tail>` (and the take-number / no-suffix / plr->npc spellings).

Modern (BO6/BO7) weapon foley keeps an NPC copy of a player file one folder down, named the same
with `_npc` appended -- before or after a trailing take number, or not at all -- and fire/mech files
swap a `_plr_` token for `_npc_`. That is a directory insertion *and* a token edit at once, so no
single-edit method (token_edits, slot_swap, sound_tail_swap) ever offers it. Runs both directions:
player names give NPC candidates and NPC names give player candidates.

    python contrib/npc_file_mirror.py [--measure] | confirm_list - --game BLACKOP7

Spent by: the modern sound-file corpus as it stands; re-run after it grows.
"""
from pathlib import Path
import argparse
import re
import sys

ROOT = Path(__file__).resolve().parent
while not (ROOT / "scripts" / "snapshot.py").is_file() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
TAIL = re.compile(r"^(.*?)(\.[a-z]nn\.\d+\.\d+\.[a-z_]+)$")
TAKE = re.compile(r"^(.*?)((?:_\d{1,3})?)$")


def corpus():
    srcs = [ROOT / "cod-name-db" / "csv" / "fnv1a_xsounds_v2.csv"]
    for folder in ("findings", "submissions", "all_names"):
        srcs += list((ROOT / folder).rglob("sound_asset*.txt"))
    out = set()
    for p in srcs:
        if not p.is_file():
            continue
        for line in p.open(encoding="utf-8", errors="replace"):
            k, sep, v = line.rstrip("\r\n").partition(",")
            v = (v if sep else k).strip().lower().replace("\\", "/")
            if "/wpn/" in v and TAIL.match(v):
                out.add(v)
    return out


def to_npc(d, base):
    stem, take = TAKE.match(base).groups()
    bases = {base + "_npc", stem + "_npc" + take, base}
    if "_plr" in base:
        bases |= {b.replace("_plr", "_npc") for b in list(bases)}
        bases.add(base.replace("_plr", "_npc"))
    return {d + "/npc/" + b for b in bases if b}


def to_plr(d, base):
    parent = d[:-4]
    stem, take = TAKE.match(base).groups()
    bases = {base, base.replace("_npc", "", 1), stem.removesuffix("_npc") + take,
             base.replace("_npc", "_plr", 1)}
    return {parent + "/" + b for b in bases if b}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", action="store_true", help="twin rate among known names, to stderr")
    a = ap.parse_args()
    names = corpus()
    cands = set()
    twins = plr = 0
    for n in names:
        path, tail = TAIL.match(n).groups()
        d, _, base = path.rpartition("/")
        if d.endswith("/npc"):
            got = {c + tail for c in to_plr(d, base)}
        else:
            plr += 1
            got = {c + tail for c in to_npc(d, base)}
            twins += bool(got & names)
        cands |= got
    cands -= names
    if a.measure:
        print(f"{len(names):,} weapon sound files; {plr:,} non-npc, {twins:,} with a named npc twin",
              file=sys.stderr)
    print(f"{len(cands):,} candidates", file=sys.stderr)
    sys.stdout.write("\n".join(sorted(cands)) + "\n")


if __name__ == "__main__":
    main()
