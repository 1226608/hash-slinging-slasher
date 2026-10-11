import sys
sys.path.insert(0, "scripts")
import snapshot
M = snapshot.ID_MASK
b6 = set(i & M for i in snapshot.read("snapshots/blackop6.ids").by_pool().get(sys.argv[1], []))
out = open("state/an/BLACKOP7_%s.only_named" % sys.argv[1], "w", encoding="utf-8")
for n in open("state/an/BLACKOP7_%s.named" % sys.argv[1], encoding="utf-8"):
    n = n.strip()
    if n and (snapshot.fnv1a(n, "BLACKOP7", sys.argv[1]) & M) not in b6:
        out.write(n + "\n")
