import pickle
from collections import defaultdict
import argparse
import utils

'''
Extract concrete update plan from z3 solver results.
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--incremental", help="incremental")
    parser.add_argument("--constraint", help="constraint")
    args = parser.parse_args()
    return args

def find_size(line):
    index = 0
    for item in line:
        if item != " ":
            size_start = index
            break
        index += 1
    size_end = line.find(")")
    size = line[size_start: size_end]
    return size

def find_name(line, needle):
    name_start = line.find(".")
    name_end = line.find(needle) + len(needle)
    name = line[name_start:name_end]
    return name

def main():
    args = parse_args()
    incremental = str(args.incremental)
    constraint = int(args.constraint)
    f = open("output-syn", "r")
    w = open("result", "w")
    result = ""
    line = f.readline()
    assignments = defaultdict()
    usages = defaultdict(list)
    states = defaultdict()
    track_dict = defaultdict(list)
    state_prefix = ""
    while line:
        if "unsat" in line:
            result += "UNSAT\n"
        elif "sat" in line:
            result += "SAT\n"
        # version.version is the prefix for all version variables. This branch simply grabs all of them.
        if "PSAImpl_ingress_start" in line and "version.version" in line and "___0" in line:
            name = find_name(line, "___0")
            orig_line = line
            line = f.readline()
            size = find_size(line)
            assignments[name] = size
            #assignments[name] = line[size_start:size_end]
            if incremental == "on" and "hdrs_5_" in orig_line:
                states[name[name.find(".version.version"):]] = size
            if incremental == "on" and "hdrs_0_" in orig_line:
                state_prefix = name[:name.find(".version.version")]
        # REAL and DIFF are used to keep track of resource usage across states. TBD: Redundancy in the code...
        if "meta_REAL" in line and "___0" in line:
            name = find_name(line, "REAL") + line[line.find("99000"):line.find("___0")]
            label = line[utils.find_nth(line,"_",-5)+1:utils.find_nth(line,"_",-4)]
            line = f.readline()
            size = find_size(line)
            usages[name].append([int(label), size])
        if "meta_DIFF" in line and "___0" in line:
            name = find_name(line, "DIFF") + line[line.find("99000"):line.find("___0")]
            label = line[utils.find_nth(line,"_",-5)+1:utils.find_nth(line,"_",-4)]
            line = f.readline()
            size = find_size(line)
            usages[name].append([int(label), size])
        if "version.VERSION" in line and "___0" in line:
            name = find_name(line, "VERSION")
            label = line[utils.find_nth(line,"_",-5)+1:utils.find_nth(line,"_",-4)]
            line = f.readline()
            size = find_size(line)
            track_dict[name].append([int(label), size])
        if "version.LENGTH" in line and "___0" in line:
            name = find_name(line, "LENGTH")
            label = line[utils.find_nth(line,"_",-5)+1:utils.find_nth(line,"_",-4)]
            line = f.readline()
            size = find_size(line)
            track_dict[name].append([int(label), size])
        if "version.sawOld" in line and "___0" in line:
            name = find_name(line, "sawOld")
            label = line[utils.find_nth(line,"_",-5)+1:utils.find_nth(line,"_",-4)]
            line = f.readline()
            size = find_size(line)
            track_dict[name].append([int(label), size])
        if "version.sawNew" in line and "___0" in line:
            name = find_name(line, "sawNew")
            label = line[utils.find_nth(line,"_",-5)+1:utils.find_nth(line,"_",-4)]
            line = f.readline()
            size = find_size(line)
            track_dict[name].append([int(label), size])
        if "Objective"  in line:
            line = f.readline()
            size = find_size(line)
            print ("Objective:", size)
        line = f.readline()

    for key in track_dict:
        temp_version_list = track_dict[key]
        temp_version_list.sort()
        assignments[key+"_"+str(temp_version_list[-1][0])+"___0"] = temp_version_list[-1][1]

    temp_list = []
    for key in assignments:
        temp_list.append([key, assignments[key]])
    temp_list.sort()
    
    w.write(result)
    w.close()
    f.close()

    with open("plan.pickle",'wb') as f:
        pickle.dump(assignments, f)
    
    # resource usage tracking for incremental mode.
    if incremental == "on":
        temp = defaultdict()
        for key in states:
            temp[state_prefix+key] = states[key]
        with open("state.pickle",'wb') as f:
            pickle.dump(temp, f)
        min1 = -10000
        min2 = -10000
        try:
            print("previous maximum resource usage:")
            with open("usage.pickle",'rb') as f:
                temp_usage = pickle.load(f)
                for key in temp_usage:
                    temp_list = temp_usage[key]
                    temp_list.sort() 
                    if "DIFF" in key:
                        min1 = constraint - int("0"+temp_list[-1][-1][1:], 16)
                        print("previous usage: ", key, temp_list[-1], min1)
        except:
            print("no usage yet!!!")
        for key in usages:
            usage_list = usages[key]
            usage_list.sort()
            if "DIFF" in key:
                min2 = constraint - int("0"+usage_list[-1][-1][1:], 16)
                print("current usage:", key, usage_list[-1], min2)
        print(max(min1,min2))
        if min1 < min2:
            with open("usage.pickle",'wb') as f:
                pickle.dump(usages, f)
    else:
        with open("usage.pickle",'wb') as f:
            pickle.dump(usages, f)

if __name__ == "__main__":
    main()
