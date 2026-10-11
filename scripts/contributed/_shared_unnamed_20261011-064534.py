"""Analysis: for each BO6/BO7 pool, how many unnamed ids also exist in the other modern captures."""
import os, sys
sys.path.insert(0, "scripts")
import snapshot
M = snapshot.ID_MASK
G = ["BLACKOP6", "BLACKOP7", "YAMYAMOK", "MODWAR22", "MODWAR7"]
ids = {}
for g in G:
    s = snapshot.read("snapshots/%s.ids" % g.lower())
    ids[g] = {k: set(i & M for i in v) for k, v in s.by_pool().items()}
for g in ["BLACKOP6", "BLACKOP7"]:
    for k in ["image", "material", "sound_asset", "xanim"]:
        un = set(int(x, 16) for x in open("state/an/%s_%s.unnamed" % (g, k)) if x.strip())
        row = [g, k, len(un)]
        for o in G:
            if o != g:
                row.append("%s:%d" % (o[:4] + o[-1], len(un & ids[o].get(k, set()))))
        anyo = set().union(*[ids[o].get(k, set()) for o in G if o != g])
        row.append("only:%d" % len(un - anyo))
        print(*row)
