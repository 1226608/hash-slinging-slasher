"""Dump, per modern game and pool, every name already resolved (tables + confirmed) -> state/an/<game>_<pool>.named
and the unnamed ids -> state/an/<game>_<pool>.unnamed (hex). Analysis helper, not a method."""
import os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import snapshot
M = snapshot.ID_MASK
TABLES = {"image": ["fnv1a_ximages_v2", "fnv1a_ximages"], "material": ["fnv1a_xmaterials_v2", "fnv1a_xmaterials"],
          "xanim": ["fnv1a_xanims_v2", "fnv1a_xanims"], "sound_asset": ["fnv1a_xsounds_v2", "fnv1a_xsounds"],
          "sound_alias": ["fnv1a_soundbanks_aliases_v2", "fnv1a_soundbanks_aliases"]}
games = sys.argv[1:] or ["BLACKOP6", "BLACKOP7"]
names_by_kind = {}
for kind, tabs in TABLES.items():
    s = set(snapshot.table_names(*tabs))
    s.update(snapshot.confirmed_names(kind))
    names_by_kind[kind] = s
for g in games:
    snap = snapshot.read("snapshots/%s.ids" % g.lower())
    pools = snap.by_pool()
    for kind in TABLES:
        ids = set(i & M for i in pools.get(kind, []))
        named = {}
        for n in names_by_kind[kind]:
            h = snapshot.fnv1a(n, g, kind) & M
            if h in ids:
                named[h] = n.strip().lower()
        open("state/an/%s_%s.named" % (g, kind), "w", encoding="utf-8").write("\n".join(sorted(set(named.values()))) + "\n")
        open("state/an/%s_%s.unnamed" % (g, kind), "w").write("\n".join("%x" % i for i in sorted(ids - set(named))) + "\n")
        print(g, kind, "ids", len(ids), "named", len(named), "unnamed", len(ids) - len(named), file=sys.stderr)
