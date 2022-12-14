import os
import argparse
import pickle
from collections import defaultdict

'''
Merge ingress and egress pipelines so that we have a single pipeline. 
This means packet clone etc. are currently not supported. TODO: consider
supporting ingress requirements and egress requirements separately?
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    parser.add_argument("--suffix", help="suffix file")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    src = str(args.src)
    # read all files generated by *_spec.py, again "old" and "new" are the 
    # special cases used for definition concatenation, e.g. in program consistency. 
    if os.path.exists(src+"-init.p4"):
        f = open(src+"-init.p4", "r")
        w = open(src+"-merge.p4", "w")
    elif os.path.exists(src+"-old-init.p4"):
        f = open(src+"-old-init.p4", "r")
        w = open(src+"-old-merge.p4", "w")
    elif os.path.exists(src+"-new-init.p4"):
        f = open(src+"-new-init.p4", "r")
        w = open(src+"-new-merge.p4", "w")
    
    result = ""
    line = f.readline()
    result_egress_name = ""
    result_egress_apply = ""

    try:
        with open("ghost_dict.pickle",'rb') as fo:
            ghost_dict = pickle.load(fo)
    except:
        ghost_dict = defaultdict()

    while line:
        if "control egress(" in line:
            # deal with egress logic, by adding egress declarations and control block to intermediate results 
            flag, depth, flag_apply = 0, 0, 0
            while flag == 0 or depth != 0:
                if "apply {" in line:
                    flag_apply = 1
                if "control egress(" in line:
                    result += line
                elif line[0] == "}" in line:
                    # egress logic is completely moved into ingress control block, so here it becomes empty.
                    result += "apply{}\n"
                    result += line
                else:
                    # keep egress declarations and control blocks separately for later merge.
                    if flag_apply == 0:
                        result_egress_name += line
                    else:
                        result_egress_apply += line
                flag = 1
                # make sure we track the boundary of egress logic.
                for item in line:
                    if item == "{":
                        depth += 1
                    elif item == "}":
                        depth -= 1
                line = f.readline()
            continue
        elif "control ingress(" in line:
            flag, depth, flag_apply = 0, 0, 0
            # deal with ingress logic, by merging it with egress logic.
            while flag == 0 or depth != 0:
                if "apply {" in line:
                    # before we start looking into control block, add all egress declarations first.
                    result += result_egress_name
                if line[0] == "}":
                    # add egress control block logic into ingress.
                    temp_result = "\n".join(result.split("\n")[:-2]) + "\n"
                    result = temp_result
                    result += "\n".join(result_egress_apply.split("\n")[1:])
                result += line
                # at the very beginning of the ingress logic, make sure the following ghost variables are set to zero.
                if "apply {" in line:
                    result += "        hdr.version.HITS = 8w0;\n"
                    result += "        hdr.version.VERSION = 8w0;\n"
                    result += "        hdr.version.LENGTH = 8w0;\n"
                    result += "        hdr.version.CONTROL = 7w0;\n"
                    result += "        hdr.version.VIOLATION = 1w0;\n"
                    for key in ghost_dict:
                        ghost_name, _, ghost_init = ghost_dict[key]
                        result += "        hdr.version.{} = {};\n".format(ghost_name, ghost_init)
                    #result += "        hdr.version.sawOld = 1w0;\n"
                    #result += "        hdr.version.sawNew = 1w0;\n"
                flag = 1
                for item in line:
                    if item == "{":
                        depth += 1
                    elif item == "}":
                        depth -= 1
                line = f.readline()
            continue
        else:
            result += line
            line = f.readline()
    w.write(result)
    w.close()
    f.close()

if __name__ == "__main__":
    main()
