"""The strings a zone keeps encrypted, decrypted: Cold War, MWIII, Black Ops 6 and Black Ops 7.

These games store part of a zone's text (string-table entries: notetrack, bone and part names,
script strings, localized text) as  [id 0x80-0xBF][b1][n][n - 1 bytes] NUL , byte i decrypting
as rol(c ^ k, r) (c kept when c == k) with (r, k) fixed by the cipher (id, b1) selects and the
position i. The cipher table is the one GrayWolf ships per game
(zonekit/profiles/<game>/strings.cipher.txt, tabulated from the game's own DecryptString):

    select <id hex> <cipher number for each b1, -1 none>
    cipher <number> <r as one hex digit, k as two, per position>

This does not walk the structures: every offset whose bytes have that shape and decrypt to
printable text is taken (numpy picks the offsets, the table decrypts). One string per line.

    python contrib/zone_encrypted_strings.py <strings.cipher.txt> <out.txt> <zones dir>... [--jobs N]
    python contrib/zone_string_names.py <out.txt> | confirm_list - --game <TAG> --script contrib/zone_encrypted_strings.py
"""
import glob
import multiprocessing
import os
import sys

import numpy as np

CHUNK = 48 << 20
TABLE = None


def rol(v, r):
    r &= 7
    return ((v << r) | (v >> (8 - r))) & 0xFF


def read(path):
    select, ciphers = {}, []
    for line in open(path):
        w = line.split()
        if not w or w[0].startswith('#'):
            continue
        if w[0] == 'select':
            select[int(w[1], 16)] = [int(n) for n in w[2:]]
        elif w[0] == 'cipher':
            s = w[2]
            ciphers.append([(int(s[j], 16), int(s[j + 1:j + 3], 16)) for j in range(0, len(s), 3)])
    return select, ciphers


def init(path):
    """per cipher: one 256-byte translation per position; and which (id, b1, c0) start printable"""
    global TABLE
    select, ciphers = read(path)
    maps = []
    every = np.arange(256, dtype=np.uint16)
    for pairs in ciphers:
        row = []
        for r, k in pairs:
            v = every ^ k
            v[k] = k
            r &= 7
            row.append((((v << r) | (v >> (8 - r))) & 0xFF).astype(np.uint8).tobytes())
        maps.append(row)
    sel = np.full((256, 256), -1, np.int32)
    for cid, row in select.items():
        sel[cid, :len(row)] = row
    printable = np.zeros(256, bool)
    printable[0x20:0x7f] = True
    first = np.zeros((len(ciphers), 256), bool)
    second = np.zeros((len(ciphers), 256), bool)
    for n, m in enumerate(maps):
        first[n] = printable[np.frombuffer(m[0], np.uint8)]
        second[n] = printable[np.frombuffer(m[1], np.uint8)]
    TABLE = (maps, sel, first, second)


def zone(path):
    maps, sel, first, second = TABLE
    out = set()
    size = os.path.getsize(path)
    with open(path, 'rb') as fh:
        at = 0
        while at < size:
            fh.seek(at)
            raw = fh.read(CHUNK + 512)
            b = np.frombuffer(raw, np.uint8)
            lim = min(len(b) - 5, CHUNK)
            if lim <= 0:
                break
            idx = np.flatnonzero((b[:lim] & 0xC0) == 0x80)
            c = sel[b[idx], b[idx + 1]]
            keep = c >= 0
            idx, c = idx[keep], c[keep]
            n = b[idx + 2].astype(np.int64)
            end = idx + 2 + n
            keep = (n >= 4) & (end < len(b))
            idx, c, n, end = idx[keep], c[keep], n[keep], end[keep]
            keep = (b[end] == 0) & first[c, b[idx + 3]] & second[c, b[idx + 4]]
            for p, cn, ln in zip(idx[keep].tolist(), c[keep].tolist(), n[keep].tolist()):
                enc = raw[p + 3:p + 2 + ln]
                if 0 in enc:
                    continue
                m = maps[cn]
                if len(enc) > len(m):
                    continue
                text = bytes(m[i][ch] for i, ch in enumerate(enc))
                if all(0x20 <= ch < 0x7f for ch in text):
                    out.add(text.lower())
            at += CHUNK
    return out


def main():
    args = sys.argv[1:]
    jobs = 8
    if '--jobs' in args:
        i = args.index('--jobs')
        jobs = int(args[i + 1])
        del args[i:i + 2]
    table, out, dirs = args[0], args[1], args[2:]
    paths = []
    for d in dirs:
        paths += glob.glob(os.path.join(d, '*.bin')) + glob.glob(os.path.join(d, '*.zone'))
    paths.sort(key=os.path.getsize, reverse=True)
    seen = set()
    with multiprocessing.Pool(jobs, init, (table,)) as pool:
        for k, got in enumerate(pool.imap_unordered(zone, paths), 1):
            seen |= got
            if k % 50 == 0 or k == len(paths):
                print('%d/%d zones, %d strings' % (k, len(paths), len(seen)), file=sys.stderr, flush=True)
    with open(out, 'wb') as fh:
        for s in sorted(seen):
            fh.write(s + b'\n')


if __name__ == '__main__':
    main()
