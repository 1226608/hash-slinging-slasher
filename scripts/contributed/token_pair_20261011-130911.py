"""Two tokens of a known name replaced at once, each from the alphabet of its own slot.

One-token substitution (token_substitution.py) cannot reach a name two steps from everything
known. Here every pair of slots of every known name is crossed, but each slot only takes the words
its place calls for: the words seen after the same left neighbour or before the same right
neighbour (digits folded, so `_01_` and `_07_` are one neighbour), the `--cap` commonest of them.
This builds inputs for one asset type over several modern games. The original native backend
source is absent from this submission, so this wrapper never launches it. To import a text
result, pass --hits-file; every result is rehashed against the requested typed targets:

    python contrib/token_pair.py <kind> <work dir> <names.tsv>... [--cap 60] [--min-count 2] [--count] [--hits-file <hits.txt>]
        | confirm_list - --game <TAG> --script contrib/token_pair.py

    names.tsv: <kind> <tab> <id hex> <tab> <name>, the known names of one game, the file named
    names_<TAG>.tsv; the targets are the unnamed ids of the kind in every one of those games.
"""
import collections
import os
import re
from pathlib import Path
import sys

ROOT = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import snapshot  # noqa: E402
from token_hits_20261011 import read_hits  # noqa: E402

M63 = (1 << 63) - 1
IW, TA = '47f5817a5ef961ba', 'cbf29ce484222325'
TOKEN = re.compile('[^_/.]+')


def shape(t):
    return re.sub(r'\d+', '#', t)


def option(args, flag, default):
    if flag in args:
        i = args.index(flag)
        v = args[i + 1]
        del args[i:i + 2]
        return type(default)(v)
    return default


def main():
    args = sys.argv[1:]
    hits_file = option(args, '--hits-file', '')
    counting = '--count' in args
    if counting:
        args.remove('--count')
    cap = option(args, '--cap', 60)
    min_count = option(args, '--min-count', 2)
    kind, work, files = args[0], args[1], args[2:]
    if kind not in snapshot.IMPORTANT or not files:
        raise ValueError('provide a supported asset kind and at least one names TSV')
    os.makedirs(work, exist_ok=True)
    skeletons, targets = {}, set()
    by_game = {s.game: s for s in (snapshot.read(p) for p in snapshot.snapshots())}
    for path in files:
        tag = os.path.basename(path)[len('names_'):-len('.tsv')]
        if tag not in snapshot.MODERN or not snapshot.searchable(tag, kind):
            raise ValueError('pair search requires modern searchable asset pools')
        named = set()
        for line in open(path, encoding='utf-8'):
            k, i, name = line.rstrip('\n').split('\t', 2)
            if k != kind:
                continue
            named.add(int(i, 16) & M63)
            if len(name) <= 160 and '~' not in name and not name.startswith('$'):
                skeletons.setdefault(name, TOKEN.findall(name))
        targets |= {i & M63 for i in by_game[tag].by_pool().get(kind, ())} - named
    left, right = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for toks in skeletons.values():
        sh = ['^'] + [shape(t) for t in toks] + ['$']
        for j, t in enumerate(toks):
            left[sh[j]][t] += 1
            right[sh[j + 2]][t] += 1
    words, alphabets, rows, total = {}, {}, [], 0
    for name, toks in skeletons.items():
        if len(toks) < 2 or len(toks) > 60:
            continue
        sh = ['^'] + [shape(t) for t in toks] + ['$']
        ids = []
        for j, t in enumerate(toks):
            key = (sh[j], sh[j + 2])
            if key not in alphabets:
                c = left[key[0]] + right[key[1]]
                chosen = [w for w, n in c.most_common(cap) if n >= min_count]
                alphabets[key] = (len(alphabets), [words.setdefault(w, len(words)) for w in chosen])
            ids.append(alphabets[key][0])
        sizes = [len(a[1]) for a in (alphabets[(sh[j], sh[j + 2])] for j in range(len(toks)))]
        s1, s2 = sum(sizes), sum(x * x for x in sizes)
        total += (s1 * s1 - s2) // 2
        rows.append(name + '\t' + ','.join(map(str, ids)))
    print('%s: %d targets, %d skeletons, %d alphabets, %d words, %.3g candidates'
          % (kind, len(targets), len(rows), len(alphabets), len(words), total), file=sys.stderr)
    if counting:
        return
    paths = [os.path.join(work, 'pair_%s_%s.txt' % (kind, x)) for x in ('targets', 'words', 'alphabets', 'skeletons')]
    content = (('%016x' % t for t in targets), list(words),
               (' '.join(map(str, a[1])) for a in sorted(alphabets.values())), rows)
    for path, lines in zip(paths, content):
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines) + '\n')
    if not hits_file:
        print('Inputs written. Native backend source was not supplied; no executable is run. '
              'Use --hits-file to import precomputed results.', file=sys.stderr)
        return
    seen = set(skeletons)
    for name in read_hits(hits_file, targets, tag, kind):
        if name not in seen:
            seen.add(name)
            print(name)


if __name__ == '__main__':
    main()
