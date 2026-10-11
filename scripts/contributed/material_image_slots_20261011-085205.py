"""Images named from the material that holds them, slot by slot.

A zone stores a material as its 0x80-byte struct followed by its image table: the ids of its
images, 8 bytes apart, in slot order. Reading every decompressed zone for u64 values that are
ids of the capture gives (material, image, slot) without walking a structure:

    links file:  <material id hex> <tab> <image id hex> <tab> <slot>
    names file:  <kind> <tab> <id hex> <tab> <name>        (material / image, known names)

On the pairs where both are named, the image is the material's core (its file name, `mtl_`
kept or dropped, cut by 0-3 trailing tokens) plus a suffix; the suffixes are counted per slot.
Then for each unnamed image of a named material:

    material core (each cut) + the 80 commonest suffixes of that slot and the 120 commonest of all
    the stem of each named sibling image of the same material + every channel ending seen

    python contrib/material_image_slots.py <links.tsv> <names.tsv> | confirm_list - --game <TAG> --script contrib/material_image_slots.py
"""
import collections
import sys


def cores(mat):
    s = mat.rpartition('/')[2]
    out = []
    for b in dict.fromkeys((s, s[4:] if s.startswith('mtl_') else s)):
        t = b.split('_')
        for k in range(0, min(3, len(t) - 1) + 1):
            out.append(('_'.join(t[:len(t) - k]), k))
    return out


def main():
    links_path, names_path = sys.argv[1], sys.argv[2]
    mat, img = {}, {}
    for line in open(names_path, encoding='utf-8'):
        k, i, n = line.rstrip('\n').split('\t', 2)
        if k == 'material':
            mat[int(i, 16)] = n
        elif k == 'image':
            img[int(i, 16)] = n
    by = collections.OrderedDict()
    for line in open(links_path):
        m, i, s = line.split()
        by.setdefault(int(m, 16), []).append((int(i, 16), int(s)))
    per_slot = collections.defaultdict(collections.Counter)
    every = collections.Counter()
    endings = collections.Counter()
    for m, lst in by.items():
        if m not in mat:
            continue
        for i, slot in lst:
            n = img.get(i)
            if not n or n.startswith('$') or '~' in n:
                continue
            for core, k in cores(mat[m]):
                at = n.find(core)
                if at >= 0 and len(core) >= 4:
                    rule = (k, n[:at], n[at + len(core):])
                    per_slot[slot][rule] += 1
                    every[rule] += 1
                    break
            if '_' in n:
                endings['_' + n.rsplit('_', 1)[1]] += 1
    top_all = [r for r, _ in every.most_common(120)]
    top_end = [e for e, c in endings.most_common(150)]
    out = sys.stdout
    seen = set()
    for m, lst in by.items():
        if m not in mat or all(i in img for i, _ in lst):
            continue
        cs = cores(mat[m])
        named = [img[i] for i, _ in lst if i in img and not img[i].startswith('$') and '~' not in img[i]]
        for i, slot in lst:
            if i in img:
                continue
            rules = [r for r, _ in per_slot[slot].most_common(80)] + top_all
            for k, pre, suf in dict.fromkeys(rules):
                for core, kk in cs:
                    if kk == k:
                        c = pre + core + suf
                        if c not in seen:
                            seen.add(c)
                            out.write(c + '\n')
        for n in named:
            if '_' in n:
                stem = n.rsplit('_', 1)[0]
                for e in top_end:
                    c = stem + e
                    if c not in seen:
                        seen.add(c)
                        out.write(c + '\n')


if __name__ == '__main__':
    main()
