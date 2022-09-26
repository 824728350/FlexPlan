import sys
import os
import pickle
from collections import defaultdict
import argparse
import utils

'''
Extract counter example from previous rounds.
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="src")
    args = parser.parse_args()
    return args

def process_output(name):
    f = open(name, "r")
    line = f.readline()
    packet = ""
    vardict = defaultdict(list)
    name_pr = ""
    name_su = ""
    prefix_meta = ""
    prefix_parse = ""
    while line:
        if (".hdr_ParserImpl_" in line or "metas__parse_and_run" in line) and "version.version" not in line and ("___0" in line or "___" not in line) and "declare" in line:
            #print(line)
            name_start = line.find(".")
            if "___0" in line:
                name_end = line.find("___0")
            else:
                if "elements" in line:
                    name_end = utils.find_nth(line,"|",-1)
                else:
                    name_end = line.find(" ()")
            name = line[name_start:name_end]
            if "metas__parse_and_run" in line:
                prefix_meta = name[:utils.find_nth(name,".",2)]
            else:
                prefix_parse = name[:utils.find_nth(name,".",2)]
            name_pr = name[utils.find_nth(name,".",2)+1:utils.find_nth(name,"_",-1)]
            name_su = name[utils.find_nth(name,"_",-1)+1:]
            #print(name)
            if "metas__parse_and_run" in line:
                vardict[(name_pr, "meta")].append(int(name_su))
            else:
                vardict[(name_pr, "parse")].append(int(name_su))
            #print(name)
        line = f.readline()
    return vardict, prefix_meta, prefix_parse

def main():
    args = parse_args()
    #print("extract from ", str(args.src))
    vardict1, prefix_meta1, prefix_parse1 = process_output(str(args.src))
    #print("extract from solve_prev.smt.")
    if os.path.exists("./solve_prev.smt") and os.path.exists("./assignments.pickle"):
        example_list = []
        with open("assignments.pickle",'rb') as f:
            try:
                while True:
                    #print("Prev counter example in place.")
                    assignments = pickle.load(f)
                    example_list.append(assignments)
            except:
                pass
        vardict2, prefix_meta2, prefix_parse2 = process_output("solve_prev.smt")
        mapping = defaultdict()
        for key, prefix in vardict1:
            if (key, prefix) in vardict2:
                vardict1[(key, prefix)].sort()
                vardict2[(key, prefix)].sort()
                if prefix == "meta":
                    for index in range(min(len(vardict1[(key, prefix)]), len(vardict2[(key, prefix)]))):
                        map_key = prefix_meta2 + "." + key + "_" + str(vardict2[(key, prefix)][index])
                        map_val = prefix_meta1 + "." + key + "_" + str(vardict1[(key, prefix)][index])
                        mapping[map_key] = map_val
                elif prefix == "parse":
                    for index in range(min(len(vardict1[(key, prefix)]), len(vardict2[(key, prefix)]))):
                        map_key = prefix_parse2 + "." + key + "_" + str(vardict2[(key, prefix)][index])
                        map_val = prefix_parse1 + "." + key + "_" + str(vardict1[(key, prefix)][index])
                        mapping[map_key] = map_val
            else:
                pass
        
        for assignments in example_list:
            assignments_prev = defaultdict()
            for key in assignments:
                if key in mapping:
                    assignments_prev[mapping[key]] = assignments[key]
            with open("assignments_prev.pickle",'ab') as f:
                pickle.dump(assignments_prev,f)
    else:
        print("No previous counter examples!")

if __name__ == "__main__":
    main()
