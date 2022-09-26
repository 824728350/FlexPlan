import argparse
import subprocess
import sys
import os
import json
import subprocess
import sys
from subprocess import DEVNULL
import pickle

'''
This file is in charge of cleaning and reformatting raw P4 code.
'''

def version(prog):
    try:
        subprocess.check_call(['p4test', '--parse-only', prog], stderr=DEVNULL, stdout=DEVNULL)
        return 16
    except:
        try:
            subprocess.check_call(['p4test', '--parse-only', '--std', 'p4-14', prog], stderr=DEVNULL, stdout=DEVNULL)
            return 14
        except:
            return 0

def add_suffix(file, suf):
    bnm = os.path.basename(file)
    exs = os.path.splitext(bnm)
    return exs[0] + '-' + suf + exs[1]

def add_suffix_and_join(file, suf, outdir):
    return os.path.join(outdir, add_suffix(file, suf))

def parse_args():
    parser = argparse.ArgumentParser(description='convert v1 model program to v1 with field lists or psa')
    parser.add_argument('-o', default='.', help='output directory')
    parser.add_argument('p4file', help='input p4 program')
    parser.add_argument('--std', choices=['p4-16', 'p4-14'])
    parser.add_argument('--psa', action='store_true', help='set if converting to psa, otherwise v1 with field lists')
    parser.add_argument('--validate', action='store_true', help='set if you don\'t want to validate output')

    parser.add_argument('--integration-file', default='./v1_integration.p4',
        help='select integration file')

    parser.add_argument('--cleanup-only', action='store_true',
        help='only clean up phase')

    parser.add_argument(
        '--bf4-exec', help='location of bf4 exec (default:p4c-analysis)', default='p4c-analysis')

    parser.add_argument(
        '--p4c-bm2-ss-exec', help='location of p4c-bm2-ss exec (default:p4c-bm2-ss)', default='p4c-bm2-ss')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    arglist=[args.p4c_bm2_ss_exec]
    crt_std = 'p4-16'
    if args.std is not None:
        crt_std = args.std
    else:
        print('args p4file: ', args.p4file)
        vr = version(args.p4file)
        print(vr)
        if vr == 14:
            crt_std = 'p4-14'
        elif vr == 16:
            crt_std = 'p4-16'
        else:
            print('problems parsing {}'.format(args.p4file))
            sys.exit(1)
    arglist.extend(['--std', crt_std])

    outdir = args.o
    cleanout = add_suffix_and_join(args.p4file, 'clean', outdir)
    if args.psa:
        arglist.extend(['--v1-psa', cleanout])
    else:
        arglist.extend(['--make-field-lists', cleanout])

    arglist.append(args.p4file)
    print('arglist: ', arglist)
    subprocess.check_call(arglist)
    print('cleaned up {} -> {}. Validating...'.format(args.p4file, cleanout))
    if args.validate:
        arglist=['p4test', '--validate', args.o]
        subprocess.check_call(arglist)

    #with open("p4_vr.json",'wb') as f:
        #json.dump(vr, f)

if __name__ == "__main__":
    main()
