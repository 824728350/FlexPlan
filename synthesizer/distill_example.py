import sys
import os
import pickle
from collections import defaultdict

'''
Analyze the counter example and generate unsat core.
'''
# There are two information we need: counter example (assignments) and the transition state (plan)
def distill_ce_and_plan():
    f = open("output-solve", "r")
    w = open("result", "w")
    result = ""
    line = f.readline()
    rawassigns = defaultdict()
    last_ones = defaultdict()
    assignments = defaultdict()
    plan = defaultdict()
    while line:
        if "unsat" in line:
            result += "UNSAT\n"
        elif "sat" in line:
            result += "SAT\n"
        if (".hdr_ParserImpl_" in line or "metas__parse_and_run" in line) and "version.version" not in line and "version.touch" not in line and "version.TOUCH" not in line:
            if "|" in line:
                name_start = line.find("|")
            else:
                name_start = line.find(".")
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
        if "hdrs_5_PSAImpl_ingress_start" in line and  "version.version" in line:
            name_start = line.find(".")
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
            plan[name] = line[size_start:size_end]
        line = f.readline()
    for key in rawassigns:
        assignments[key] = rawassigns[key]
    '''
    for key in assignments:
        print(key, assignments[key])
    for key in plan:
        print(key, plan[key])
    '''
    w.write(result)
    w.close()
    f.close()
    return plan, assignments

# Suppose the counter example is fixed as a concrete packet, and the corresponding version sketch is also fixed. 
# Then it will always lead to "unsat" if the problem is to find a packet that does not trigger violation.
# We could use this formula to extract unsat core: if we remove some assumption from the version sketch (e.g.,
# we do not care about some version numbers, but the problem is still unsat, then we have distilled a unsat core 
# that covers much larger possible transition states space.
def generate_uc(plan, assignments):
    f = open("solve-distill.smt", "r")
    result = "(set-option :produce-unsat-cores true)\n"
    result += "(set-option :smt.core.minimize true)\n"
    line = f.readline()
    index = 1
    delta = 0
    unsat_dict = defaultdict()
    while line:
        if "check-sat" in line:
            for key in assignments:
                result += "(assert (= {} {}))\n".format(key, assignments[key])
            for key in plan:
                result += "(assert (! (= {} {}) :named a{}))\n".format(key, plan[key], str(index))
                unsat_dict["a"+str(index)] = [key, plan[key]]
                index += 1
        if "meta_VIOLATION" in line and "declare-fun" in line:
            name = line[line.find("."):-1]
        if "meta_VIOLATION" in line and "declare-fun" not in line:
            delta += 1
        if "meta_VIOLATION" in line and "declare-fun" not in line and delta > 2 and name in line:
            if "#b" in line:
                pass
            else:
                result += line
                line = f.readline()
            bool_index = line.find("#b") + 2
            if line[bool_index] == "0":
                result += line[:bool_index] + "1" + line[bool_index+1:]
            elif line[bool_index] == "1":
                result += line[:bool_index] + "0" + line[bool_index+1:]
        else:
            result += line
        line = f.readline()
    result += "(get-unsat-core)\n"
    w = open("distill.smt", "w")
    w.write(result)
    f.close()
    w.close()
    with open("unsat.pickle",'wb') as f:
        pickle.dump(unsat_dict, f)
    with open("unfinished.pickle",'wb') as f:
        pickle.dump(plan, f)

def main():
    plan, assignments = distill_ce_and_plan()
    generate_uc(plan, assignments)

if __name__ == "__main__":
    main()
