"""Composite world materials of the modern titles, enumerated whole.

Half of the known materials of Black Ops 6 are named by a grammar with no words in it: a technique
(`twc`, `tw`, `twcj`, `twck`, `wc`, `twj`, `twk`, `w`), a slash and a star, then two to four layers
joined by `_`, each a number followed by `n`, `dn` or nothing (`twc`, slash, star, `866n_837n_838n`).
Every such name of two layers (numbers to 20,000) and of three (numbers to 8,000) was hashed on a
GPU with codehash (github.com/Kenshin9977/codehash, built with the IW basis 0x47F5817A5EF961BA and
HASH_BITS=63) against the unnamed materials of the four titles: 2.9e10 and 1.4e13 per technique.
At three layers about three chance matches per technique are expected among the hits.

This prints the names codehash found, for confirm_list to file per game:

    python contrib/composite_materials.py <found.txt>... | confirm_list - --game <TAG> --script contrib/composite_materials.py

`--elements <top>` prints the layer dictionary instead (one element per line), the `--dict` of the search.
"""
import sys


def main():
    args = sys.argv[1:]
    if args and args[0] == '--elements':
        for s in ('n', 'dn', ''):
            for i in range(int(args[1]) + 1):
                print('%d%s' % (i, s))
        return
    seen = set()
    for path in args:
        for line in open(path, encoding='utf-8', errors='replace'):
            name = line.strip().split(',')[-1].split()[-1] if line.strip() else ''
            if name and name not in seen:
                seen.add(name)
                print(name)


if __name__ == '__main__':
    main()
