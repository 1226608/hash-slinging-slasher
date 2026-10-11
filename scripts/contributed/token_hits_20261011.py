"""Read precomputed token-search hits as data; never launch an external backend.

The original native search sources were not submitted. The companion wrappers
still write their input files, and --hits-file imports a separately produced text
result only after rehashing each name against the requested typed targets.
"""
import snapshot


def read_hits(path, targets, game, kind):
    targets = set(targets)
    seen = set()
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            raw, sep, name = line.rstrip("\r\n").partition(",")
            if not sep or not name or name != name.strip() or any(ord(c) < 32 for c in name):
                raise ValueError(f"invalid hit row {number}")
            key = int(raw, 16)
            full = (snapshot.fnv1a_nofold(name) if game == "BLKOPS04" and kind == "sound_asset"
                    else snapshot.fnv1a(name, game, kind))
            masked = full & snapshot.ID_MASK
            if key not in (full, masked) or masked not in targets:
                raise ValueError(f"hit row {number} does not match the requested hash/pool")
            if name not in seen:
                seen.add(name)
                yield name
