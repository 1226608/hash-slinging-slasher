"""Dialogue files from their aliases: `<root>/<mode>/<zone name>/<alias>.<tail>`.

Found with dialogue_dir_probe.py on Black Ops 6: a level's dialogue lives in a directory
named after the level's zone (`t10/sp/sp_t10_heist/dx_sp_heis_acqr_mrsh_....pnn.75.48000.english`),
the stem being the alias that plays it. This writes a plan crossing

    begin   <root>/<mode>/<zone>/  for every zone name given (and every string of the zones
            that starts with a mode token and holds the title token), mode = the zone's first token
    stem    every known `dx_` alias (tables, registry, findings)
    end     .<tail> for the dialogue tails

    python contrib/dialogue_zone_dirs.py <root,root...> <zones dir or names file>... [--dots] [--names <names.tsv>]
    confirm_plan plans/dialogue_zone.txt --game <TAG>
`--dots` spells the directories with periods (MWII, MWIII).
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAILS = ('pnn.75.48000.english', 'snn.75.48000.english', 'snn.20.48000.english', 'pnn.20.48000.english',
         'sn.75.48000.english', 'pn.75.48000.english', 'pnn.85.48000.english', 'snn.85.48000.english',
         'pnn.100.48000.english', 'snn.100.48000.english', 'lnn.75.48000.english', 'tnn.75.48000.english')
MODES = ('sp', 'mp', 'zm', 'cp', 'wz', 'br', 'op', 'ob', 'fe', 'core', 'global', 'ingame')


def main():
    args = sys.argv[1:]
    dots = '--dots' in args
    if dots:
        args.remove('--dots')
    names_path = None
    if '--names' in args:
        i = args.index('--names')
        names_path = args[i + 1]
        del args[i:i + 2]
    roots, sources = args[0].split(','), args[1:]
    zones = set()
    for s in sources:
        if os.path.isdir(s):
            zones.update(os.path.basename(p)[:-4].lower() for p in glob.glob(os.path.join(s, '*.bin')))
        else:
            zones.update(line.strip().lower() for line in open(s, encoding='utf-8', errors='replace') if line.strip())
    zones = {z[len(p):] if z.startswith(p) else z for z in zones for p in ('', 'eng_', 'ens_', 'ww_', 'fra_')}
    stems = set()
    files = glob.glob(os.path.join(ROOT, 'cod-name-db', 'csv', 'fnv1a_soundbanks_aliases*.csv'))
    files += glob.glob(os.path.join(ROOT, 'all_names', '*', 'sound_alias.txt'))
    files += glob.glob(os.path.join(ROOT, 'findings', '*', 'sound_alias.txt'))
    for f in files:
        for line in open(f, encoding='utf-8', errors='replace'):
            n = line.rstrip('\r\n').partition(',')[2].strip().lower()
            if n.startswith('dx_'):
                stems.add(n)
    if names_path:
        for line in open(names_path, encoding='utf-8'):
            k, _, n = line.rstrip('\n').split('\t', 2)
            if k == 'sound_alias' and n.startswith('dx_'):
                stems.add(n)
    sep = '.' if dots else '/'
    begins = set()
    for z in zones:
        first = z.split('_')[0]
        for r in roots:
            for m in {first} | ({m for m in MODES if m in z.split('_')}):
                begins.add(sep.join((r, m, z)) + sep)
    os.makedirs(os.path.join(ROOT, 'plans'), exist_ok=True)
    for name, rows in (('dialogue_zone_begins.txt', begins), ('dialogue_zone_stems.txt', stems)):
        with open(os.path.join(ROOT, 'plans', name), 'w', newline='\n') as fh:
            fh.write('\n'.join(sorted(rows)) + '\n')
    with open(os.path.join(ROOT, 'plans', 'dialogue_zone.txt'), 'w', newline='\n') as fh:
        fh.write('label: dialogue files from their aliases, under the directory of each zone\n')
        fh.write('begin: @plans/dialogue_zone_begins.txt\nstem: @plans/dialogue_zone_stems.txt\n')
        for t in TAILS:
            fh.write('end: .%s\n' % t)
    print('%d zones, %d beginnings, %d dx aliases' % (len(zones), len(begins), len(stems)))


if __name__ == '__main__':
    main()
