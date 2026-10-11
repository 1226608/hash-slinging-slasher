"""The directory of a dialogue family, searched with files whose stem is already known.

A dialogue file is `<root>/<mode>/<dir>/<alias>.<tail>`: its stem is the alias that plays it
(`iw9/op/alejandro/dx_op_alej_ping_..._ogr2.snn.20.48000.english`, `s6/mp/mp_gamestate/dx_mp_gmst_...`).
The zones link each alias to its files (see sound_link_probes.py), so for a named `dx_` alias
whose files are unnamed the stem is known and only the directory is missing; and one
directory holds a whole family (`dx_<mode>_<code>_...`). This writes a plan:

    begin   <root>/<mode>/  and  <root>/<mode>/<mode>_   for every root any sound file uses
    stem    every token of the zones' strings that could be a directory name
    end     /<alias>.<tail>  for one or two aliases of each of the largest families, each dialogue tail

    python contrib/dialogue_dir_probe.py <links.tsv> <names.tsv> <strings.txt>...   writes plans/dialogue_dir.txt
    confirm_plan plans/dialogue_dir.txt --game <TAG>
A directory found this way is then applied to its whole family with sound_link_probes.py.
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAILS = ('snn.20.48000.english', 'snn.75.48000.english', 'pnn.75.48000.english', 'sn.75.48000.english',
         'snn.20.48000.all', 'snn.75.48000.all')
WORD = re.compile(r'^[a-z][a-z0-9_]{2,23}$')


def main():
    links, names_path, strings = sys.argv[1], sys.argv[2], sys.argv[3:]
    alias, files = {}, {}
    for line in open(names_path, encoding='utf-8'):
        k, i, n = line.rstrip('\n').split('\t', 2)
        if k == 'sound_alias':
            alias[int(i, 16)] = n
        elif k == 'sound_asset':
            files[int(i, 16)] = n
    fam = collections.defaultdict(list)
    for line in open(links):
        a, f, _ = line.split()
        a, f = int(a, 16), int(f, 16)
        n = alias.get(a)
        if n and n.startswith('dx_') and f not in files and n.count('_') >= 3:
            t = n.split('_')
            if n not in fam[(t[1], t[2])]:
                fam[(t[1], t[2])].append(n)
    top = sorted(fam.items(), key=lambda kv: -len(kv[1]))[:60]
    roots = collections.Counter()
    for n in files.values():
        if '/' in n:
            roots[n.split('/')[0]] += 1
    roots = [r for r, c in roots.most_common(40)] + ['t10', 'cer', 'sat', 's1', 's2', 's3', 's4', 's5', 's6', 's7']
    modes = sorted({m for (m, _), _ in top})
    words = set()
    for path in strings:
        with open(path, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                for w in re.split(r'[/.:\\]', line.strip()):
                    if WORD.match(w):
                        words.add(w)
    os.makedirs(os.path.join(ROOT, 'plans'), exist_ok=True)
    with open(os.path.join(ROOT, 'plans', 'dialogue_dir_words.txt'), 'w', newline='\n') as fh:
        fh.write('\n'.join(sorted(words)) + '\n')
    with open(os.path.join(ROOT, 'plans', 'dialogue_dir.txt'), 'w', newline='\n') as fh:
        fh.write('label: dialogue directories, probed with files whose stem (the alias) is known\n')
        for r in dict.fromkeys(roots):
            for m in modes:
                fh.write('begin: %s/%s/\nbegin: %s/%s/%s_\n' % (r, m, r, m, m))
            fh.write('begin: %s/\n' % r)
        fh.write('stem: @plans/dialogue_dir_words.txt\n')
        for (m, c), ns in top:
            for n in ns[:1]:
                for t in TAILS:
                    fh.write('end: /%s.%s\n' % (n, t))
    print('%d families (largest: %s), %d modes, %d roots, %d words' % (
        len(fam), ', '.join('%s_%s:%d' % (m, c, len(ns)) for (m, c), ns in top[:12]), len(modes), len(set(roots)), len(words)))


if __name__ == '__main__':
    main()
