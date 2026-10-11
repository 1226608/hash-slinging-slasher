"""Names read out of the game's own zones: every string the zones hold, and the variants of each.

The strings come from a zone walk (GrayWolf's zonekit reads every fast file offline and gives
each zone's decrypted strings); this script takes them as text files, one string per line or
`hash,name` csv, and prints each string with the spellings an asset name is derived from it by:

    the string itself
    the file name of a path, and the path with its extension dropped
    each side of a `::` pair
    a sound path with `/` as `.` and as a backslash (the tables' export spelling undone)

Nothing is composed: every candidate is a string the build ships, so the expected number of
coincidental matches is candidates x wanted / 2^63 (under 0.001 for ten million strings).

    python contrib/zone_string_names.py <file or folder>... | confirm_list - --game <TAG> --script contrib/zone_string_names.py
"""
import glob
import os
import sys


def variants(s):
    yield s
    if '::' in s:
        for part in s.split('::'):
            if part:
                yield part
    base = s.replace('\\', '/')
    if '/' in base:
        yield base.rsplit('/', 1)[1]
    tail = base.rsplit('/', 1)[-1]
    if '.' in tail:
        yield base[:base.rindex('.')]
        yield tail[:tail.rindex('.')]
        yield base[:len(base) - len(tail)] + tail.split('.', 1)[0]
        yield tail.split('.', 1)[0]


def lines(paths):
    for path in paths:
        files = [path]
        if os.path.isdir(path):
            files = sorted(glob.glob(os.path.join(path, '**', '*.*'), recursive=True))
        for f in files:
            if not os.path.isfile(f):
                continue
            with open(f, encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    line = line.rstrip('\r\n')
                    if not line:
                        continue
                    head, sep, rest = line.partition(',')
                    if sep and len(head) <= 16 and all(c in '0123456789abcdefABCDEF' for c in head):
                        line = rest
                    yield line


def main():
    seen = set()
    out = sys.stdout
    for s in lines(sys.argv[1:]):
        s = s.strip().lower()
        if not 2 < len(s) < 240 or ' ' in s:
            continue
        for v in variants(s):
            if len(v) > 2 and v not in seen:
                seen.add(v)
                out.write(v + '\n')


if __name__ == '__main__':
    main()
