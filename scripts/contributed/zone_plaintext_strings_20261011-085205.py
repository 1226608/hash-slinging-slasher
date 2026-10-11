"""Every plain string a game's decompressed zones hold, one per line, deduplicated.

A zone (a fast file decompressed, its patch applied) carries text beside its hashed asset
names: script and scriptbundle strings, map entity text, csv/lua/ddl raw files, the names a
struct keeps in clear. This reads the bytes, never the structures:

    a run of printable bytes that ends on a NUL, or is at least 12 long, is text;
    the run itself is a candidate when it holds no blank, and so is each token of it
    (cut at blanks, quotes, commas, semicolons, `=`, brackets, `|`).

    python contrib/zone_plaintext_strings.py <out.txt> <zones dir>... [--jobs N]
    python contrib/zone_string_names.py <out.txt> | confirm_list - --game <TAG> --script contrib/zone_plaintext_strings.py

Decompressed zones come from any extractor that writes them (GrayWolf `zk.py decompress`,
acts). The game itself is not needed after that.
"""
import glob
import multiprocessing
import os
import re
import sys

RUN = re.compile(rb'[\x09\x0a\x0d\x20-\x7e]{4,}')
CUT = re.compile(rb'[\s"\',;=()\[\]{}<>|]+')
CHUNK = 64 << 20


def zone_strings(path):
    out = set()
    with open(path, 'rb') as fh:
        tail = b''
        while True:
            block = fh.read(CHUNK)
            buf = tail + block
            if not buf:
                break
            last = len(buf) if not block else max(0, len(buf) - 4096)
            for m in RUN.finditer(buf):
                if m.start() >= last:
                    break
                e = m.end()
                if e - m.start() < 12 and not (e < len(buf) and buf[e] == 0):
                    continue
                s = m.group().strip().lower()
                if len(s) > 100000:
                    continue
                if 2 < len(s) <= 240 and b' ' not in s and b'\n' not in s and b'\t' not in s:
                    out.add(s)
                for tok in CUT.split(s):
                    if 2 < len(tok) <= 240:
                        out.add(tok)
            if not block:
                break
            tail = buf[last:]
    tmp = path_out(path)
    with open(tmp, 'wb') as fh:
        fh.write(b'\n'.join(sorted(out)))
        fh.write(b'\n')
    return tmp, len(out)


def path_out(path):
    return os.path.join(TMP, '%08x_%s.txt' % (hash(os.path.dirname(path)) & 0xffffffff, os.path.basename(path)))


TMP = None


def init(tmp):
    global TMP
    TMP = tmp


def main():
    args = sys.argv[1:]
    jobs = 8
    if '--jobs' in args:
        i = args.index('--jobs')
        jobs = int(args[i + 1])
        del args[i:i + 2]
    out, dirs = args[0], args[1:]
    tmp = out + '.parts'
    os.makedirs(tmp, exist_ok=True)
    paths = []
    for d in dirs:
        paths += glob.glob(os.path.join(d, '*.bin')) + glob.glob(os.path.join(d, '*.zone'))
    paths.sort(key=os.path.getsize, reverse=True)
    seen = set()
    with multiprocessing.Pool(jobs, init, (tmp,)) as pool:
        for n, (part, count) in enumerate(pool.imap_unordered(zone_strings, paths), 1):
            with open(part, 'rb') as fh:
                seen.update(fh.read().split(b'\n'))
            os.remove(part)
            if n % 50 == 0 or n == len(paths):
                print('%d/%d zones, %d strings' % (n, len(paths), len(seen)), file=sys.stderr, flush=True)
    seen.discard(b'')
    with open(out, 'wb') as fh:
        for s in sorted(seen):
            fh.write(s + b'\n')
    os.rmdir(tmp)


if __name__ == '__main__':
    main()
