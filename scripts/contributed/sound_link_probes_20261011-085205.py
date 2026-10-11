"""Sound files and aliases named across the alias -> file link the zones hold.

In Black Ops 6 and Black Ops 7 a zone stores each alias entry as the alias id and, 16 (or 8)
bytes further, the id of the file that entry plays; an alias with several entries lists its
takes in order. Reading every decompressed zone for u64 values that are ids of the capture
(any byte alignment) gives the links without walking a structure:

    links file:  <alias id hex> <tab> <file id hex> <tab> <position of the file in the alias>
    names file:  <kind> <tab> <id hex> <tab> <name>          (sound_alias / sound_asset, known names)

From a link with one named end:

  unnamed file, a sibling take of the same alias named:   the sibling with every number it
      holds walked 0-40 (both paddings), and the sibling's directory and tail under the
      alias name and the alias name + number
  unnamed file, alias named, no take named:   the alias (and alias + number) under the
      directory and tail of the files of the aliases nearest to it by name (shared leading tokens)
  unnamed alias, a file named:   the file's stem, the stem without its number, without its
      title prefix (iw9_, t10_, jup_ ...), and with the first token of sibling aliases

    python contrib/sound_link_probes.py <links.tsv> <names.tsv> | confirm_list - --game <TAG> --script contrib/sound_link_probes.py
"""
import bisect
import collections
import re
import sys

NUM = re.compile(r'\d+')
TITLES = ('iw8_', 'iw9_', 's6_', 'jup_', 't10_', 'cer_', 'sat_', 'mp_', 'zm_', 'cp_', 'br_')


def split(name):
    d, _, base = name.rpartition('/')
    stem, _, tail = base.partition('.')
    return d, stem, tail


def renumber(stem):
    for m in NUM.finditer(stem):
        w = len(m.group())
        for n in range(0, 41):
            for width in {w, 1, 2}:
                yield stem[:m.start()] + str(n).zfill(width) + stem[m.end():]


def main():
    links_path, names_path = sys.argv[1], sys.argv[2]
    alias, files = {}, {}
    for line in open(names_path, encoding='utf-8'):
        k, i, n = line.rstrip('\n').split('\t', 2)
        if k == 'sound_alias':
            alias[int(i, 16)] = n
        elif k == 'sound_asset':
            files[int(i, 16)] = n
    by = collections.OrderedDict()
    for line in open(links_path):
        a, f, _ = line.split()
        by.setdefault(int(a, 16), []).append(int(f, 16))
    # the (directory, tail) pairs used by the files of each named alias, kept in alias-name order
    frames = {}
    for a, fs in by.items():
        if a in alias:
            fr = collections.Counter()
            for f in fs:
                if f in files:
                    d, stem, tail = split(files[f])
                    if tail:
                        fr[(d, tail)] += 1
            if fr:
                frames[alias[a]] = [k for k, _ in fr.most_common(6)]
    ordered = sorted(frames)
    firsts = collections.Counter(n.split('_')[0] for n in alias.values())
    out = sys.stdout
    seen = set()

    def emit(s):
        if s not in seen:
            seen.add(s)
            out.write(s + '\n')

    for a, fs in by.items():
        named = [files[f] for f in fs if f in files]
        missing = [f for f in fs if f not in files]
        an = alias.get(a)
        if missing:
            near = []
            for n in named:
                d, stem, tail = split(n)
                if not tail:
                    continue
                near.append((d, tail))
                for s in renumber(stem):
                    emit('%s/%s.%s' % (d, s, tail) if d else '%s.%s' % (s, tail))
            if an:
                if not near:
                    at = bisect.bisect_left(ordered, an)
                    for other in ordered[max(0, at - 12):at + 12]:
                        if other.split('_')[:2] == an.split('_')[:2]:
                            near += frames[other]
                for d, tail in dict.fromkeys(near):
                    pre = d + '/' if d else ''
                    emit('%s%s.%s' % (pre, an, tail))
                    for n in range(0, 21):
                        emit('%s%s_%02d.%s' % (pre, an, n, tail))
                        emit('%s%s_%d.%s' % (pre, an, n, tail))
                        emit('%s%s%02d.%s' % (pre, an, n, tail))
        if an is None and named:
            for n in named:
                d, stem, tail = split(n)
                core = re.sub(r'_?\d+$', '', stem)
                for s in {stem, core}:
                    emit(s)
                    for t in TITLES:
                        if s.startswith(t):
                            emit(s[len(t):])
                        else:
                            emit(t + s)
                    toks = s.split('_')
                    for k in range(1, min(4, len(toks))):
                        emit('_'.join(toks[:-k]))
                        emit('_'.join(toks[k:]))


if __name__ == '__main__':
    main()
