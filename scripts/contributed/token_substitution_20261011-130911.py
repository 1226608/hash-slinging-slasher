"""One token of a known name replaced by a word the same asset type already uses.

Every known name of one type is a skeleton; each of its tokens (cut at `_`, `/`, `.`) is replaced
in turn by every word of the type's vocabulary, and the result is hashed against the ids of that
type the game holds and nobody has named. The crossing is too large for a pipe (tens of billions
per type), so `token_substitution.c` does it and prints only the hits; this script builds its
three inputs and prints the hit names, to be filed by confirm_list:

    gcc -O3 -fopenmp -o <work dir>/token_substitution contrib/token_substitution.c
    python contrib/token_substitution.py <TAG> <kind> <work dir> <names.tsv>... [--insert]
        [--min-count 2] [--max-words 60000] [--rounds 6] [--other-kinds 5] [--words-file <txt>]
        | confirm_list - --game <TAG> --script contrib/token_substitution.py

    names.tsv: <kind> <tab> <id hex> <tab> <name>, the known names of one game. The first file is
    the game searched: its named ids are the ones left out of the targets. Names of the same kind
    in every file are skeletons, and their tokens (seen `--min-count` times) are the words, with
    the tokens the other kinds use `--other-kinds` times or more. Each round's hits are the next
    round's skeletons, which is what fills a family that varies in several places.
    `--words-file` replaces the vocabulary by the words of a file the names do not already use
    (a wiki's page titles, a glossary).

Aliases hash from the Treyarch basis, every other modern type from the IW one.
"""
import collections
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import snapshot  # noqa: E402

M63 = (1 << 63) - 1
IW, TA = '47f5817a5ef961ba', 'cbf29ce484222325'
CUT = re.compile('[_/.]')


def option(args, flag, default):
    if flag in args:
        i = args.index(flag)
        v = args[i + 1]
        del args[i:i + 2]
        return type(default)(v)
    return default


def main():
    args = sys.argv[1:]
    insert = '--insert' in args
    if insert:
        args.remove('--insert')
    min_count = option(args, '--min-count', 2)
    max_words = option(args, '--max-words', 60000)
    rounds = option(args, '--rounds', 6)
    other_min = option(args, '--other-kinds', 5)
    words_file = option(args, '--words-file', '')
    tag, kind, work, files = args[0], args[1], args[2], args[3:]
    os.makedirs(work, exist_ok=True)
    named, skeletons = set(), set()
    words, other = collections.Counter(), collections.Counter()
    for n, path in enumerate(files):
        for line in open(path, encoding='utf-8'):
            k, i, name = line.rstrip('\n').split('\t', 2)
            if len(name) > 160 or '~' in name or name.startswith('$'):
                continue
            if k != kind:
                other.update(set(CUT.split(name)))
                continue
            if n == 0:
                named.add(int(i, 16) & M63)
            skeletons.add(name)
            words.update(set(CUT.split(name)))
    snap = [s for s in (snapshot.read(p) for p in snapshot.snapshots()) if s.game == tag][0]
    targets = {i & M63 for i in snap.by_pool().get(kind, ())} - named
    chosen = [w for w, c in words.most_common(max_words) if c >= min_count and w]
    have = set(chosen)
    extra = [w for w, c in other.most_common() if c >= other_min and w and w not in have]
    chosen += extra[:max(0, max_words - len(chosen))]
    if words_file:
        own = set(words) | set(other)
        chosen = [w for w in dict.fromkeys(l.strip().lower() for l in open(words_file, encoding='utf-8')) if w and w not in own]
    paths = [os.path.join(work, '%s_%s_%s.txt' % (tag, kind, x)) for x in ('targets', 'skeletons', 'words')]
    exe = os.path.join(work, 'token_substitution')
    basis = TA if kind == 'sound_alias' or tag not in snapshot.MODERN else IW
    seen, new = set(skeletons), sorted(skeletons)
    for r in range(rounds):
        for path, rows in zip(paths, (('%016x' % t for t in targets), new, chosen)):
            with open(path, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write('\n'.join(rows) + '\n')
        print('%s %s round %d: %d targets, %d skeletons, %d words'
              % (tag, kind, r + 1, len(targets), len(new), len(chosen)), file=sys.stderr)
        cmd = [exe, basis] + paths + (['insert'] if insert else [])
        out = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout.decode('utf-8', 'replace')
        new = []
        for line in out.splitlines():
            i, _, name = line.partition(',')
            if name not in seen:
                seen.add(name)
                new.append(name)
                targets.discard(int(i, 16) & M63)
                print(name)
        sys.stdout.flush()
        print('  %d new names' % len(new), file=sys.stderr)
        if not new or not targets:
            break


if __name__ == '__main__':
    main()
