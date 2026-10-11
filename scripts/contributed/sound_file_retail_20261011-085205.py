"""Every known sound file of every modern title, under every encoding tail any title uses.

A sound file is `<dir>/<stem>.<tail>`, the tail naming its encoding (`snn.20.48000.english`,
`tnn.85.48000.all`, ...). A later title re-ships an earlier title's file under another tail:
Black Ops 7 holds MWII's `iw9/op/nikto/dx_op_nkto_..._opg3` as `.snn.20.48000.english` where
the MWII table spells it `.sn.75.48000.english`. This writes a plan crossing every `<dir>/<stem>`
found in the tables, the registry and the findings (all titles) with every tail seen anywhere.

    python contrib/sound_file_retail.py            writes plans/sound_retail.txt and its two lists
    confirm_plan plans/sound_retail.txt --game <TAG>
"""
import glob
import os
import re

TAIL = re.compile(r'^[a-z]{2,3}\.\d+\.\d+\.[a-z_]+$')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    stems, tails = set(), {}
    files = glob.glob(os.path.join(ROOT, 'cod-name-db', 'csv', 'fnv1a_xsounds_v2.csv'))
    for pool in ('sound_asset', 'sndasset'):
        files += glob.glob(os.path.join(ROOT, 'all_names', '*', pool + '.txt'))
        files += glob.glob(os.path.join(ROOT, 'findings', '*', '**', pool + '*.txt'), recursive=True)
        files += glob.glob(os.path.join(ROOT, 'submissions', '**', pool + '_*.txt'), recursive=True)
    for f in files:
        with open(f, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                name = line.rstrip('\r\n').partition(',')[2].strip().lower().replace('\\', '/')
                d, _, base = name.rpartition('/')
                stem, dot, tail = base.partition('.')
                if not dot or not stem or not TAIL.match(tail):
                    continue
                stems.add((d + '/' if d else '') + stem)
                # MWII and MWIII spell the directories with periods, BO6 and BO7 with slashes
                stems.add((d.replace('/', '.') + '.' if d else '') + stem)
                tails[tail] = tails.get(tail, 0) + 1
    os.makedirs(os.path.join(ROOT, 'plans'), exist_ok=True)
    with open(os.path.join(ROOT, 'plans', 'sound_retail_stems.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(sorted(stems)) + '\n')
    with open(os.path.join(ROOT, 'plans', 'sound_retail_tails.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join('.' + t for t in sorted(tails, key=lambda t: -tails[t]) if tails[t] >= 5) + '\n')
    with open(os.path.join(ROOT, 'plans', 'sound_retail.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('label: known sound files of every title under every encoding tail\n')
        fh.write('stem: @plans/sound_retail_stems.txt\nend: @plans/sound_retail_tails.txt\n')
    print('%d stems, %d tails' % (len(stems), len(tails)))


if __name__ == '__main__':
    main()
