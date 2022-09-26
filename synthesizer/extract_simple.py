import pickle
from collections import defaultdict
import argparse
import utils

'''
Extract counter example and determine what to do with that result
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", help="type")
    args = parser.parse_args()
    return args


def process_output(name):
    with open("mapping.pickle",'rb') as f:
        mapping = pickle.load(f)
    rawassigns = defaultdict()
    assignments = defaultdict()
    vardict = defaultdict(list)
    f = open(name, "r")
    line = f.readline()
    result = ""

    while line:
        if "unsat" in line:
            result += "UNSAT"
        elif "sat" in line:
            result += "SAT"
        if (".hdr_ParserImpl_" in line or "metas__parse_and_run" in line) and "version.version" not in line:
            name_start = line.find(".")
            if "elements" in line:
                name_end = utils.find_nth(line,"|",-1)
            else:
                name_end = line.find(" ()")
            name = line[name_start:name_end]
            line = f.readline()
            index = 0
            for item in line:
                if item != " ":
                    size_start = index
                    break
                index += 1
            size_end = line.find(")")
            rawassigns[name] = line[size_start:size_end]
            name_pr = name[:utils.find_nth(name,"_",-1)]
            name_su = name[utils.find_nth(name,"_",-1)+1:]
            vardict[name_pr].append(int(name_su))
        line = f.readline()

    for key in vardict:
        vardict[key].sort()
        realkey = key+"_"+str(vardict[key][-1])
        if realkey in mapping and realkey in rawassigns:
            assignments[mapping[realkey]] = rawassigns[realkey]
    f.close()
    with open("assignments.pickle",'ab') as f:
        pickle.dump(assignments, f)
    return result

def main():
    args = parse_args()
    TYPE = str(args.type)

    w = open("result", "w")
    if TYPE == "normal":
        result = process_output("output1")
        if result == "UNSAT":
            w.write("UNSAT\n")
        elif result == "SAT":
            w.write("SAT\n")
    elif TYPE == "program_consistency":
        result1 = process_output("output1")
        result2 = process_output("output2")
        if result1 == "UNSAT" or result2 == "UNSAT":
            w.write("UNSAT\n")
        elif result1 == "SAT" and result2 == "SAT":
            w.write("SAT\n")
    elif TYPE == "correct":
        w.write("UNSAT\n")
    w.close()

if __name__ == "__main__":
    main()
