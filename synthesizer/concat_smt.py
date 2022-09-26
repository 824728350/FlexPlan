from collections import defaultdict
import argparse
import pickle
import utils

'''
This file describes how to generate the synthesis & and verification SMT formulas from the original template. 
It explains how to enforce different exploration startegies for tradeoffs on resource v.s. num of steps.
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orig", help="output file")
    #parser.add_argument("--old", help="new smt file")
    parser.add_argument("--new", help="smt file prefixes")
    parser.add_argument("--iter", help="num of iteration")
    parser.add_argument("--state", help="synthesis or verify?")
    parser.add_argument("--constraint", help="constraint")
    parser.add_argument("--maxsat", help="use maxsat?")
    parser.add_argument("--minimize", help="minimize resource usage?")
    parser.add_argument("--cause", help="find root cause?")
    parser.add_argument("--incremental", help="incremental objective?")

    args = parser.parse_args()
    return args

def extract(line, key):
    name_start = line.find(".")
    name_end = line.find(key) + len(key)
    name = line[name_start:name_end]
    label_start = utils.find_nth(line, "_", -1)+1
    label_end = -1
    label = line[label_start:label_end]
    return name, name_start, name_end, label

def main():
    args = parse_args()
    origSMT = str(args.orig)
    newSMT = str(args.new)
    iterNUM = str(args.iter)
    state = str(args.state)
    #constraint = int(args.constraint)
    maxsat = str(args.maxsat)
    minimize = str(args.minimize)
    cause = str(args.cause)
    incremental = str(args.incremental)
    fo = open(origSMT, "w")
    try:
        fp = open("assignments.pickle", "rb")
        iterNUM = 1
        while True:
            try:
                pickle.load(fp)
                iterNUM += 1
            except EOFError:
                break
        fp.close()
    except: pass
    iterNUM = str(iterNUM)
    print("Actual iterNUM: ", iterNUM)

    true_count = int(iterNUM)
    if state == "verify":
        iterNUM = "1"
    result_declare, result_assert = "", ""
    last_sentence = ["" for i in range(int(iterNUM))]
    version_dict = defaultdict(list)
    firsttime_flag = 0
    last_ones = defaultdict()
    total_changes = 0
    total_hex = ""
    
    try:
        with open("versiondata.pickle",'rb') as f:
            versiondata = pickle.load(f)
            for key in versiondata:
                total_changes += 1
            if len(str(hex(total_changes))[2:]) == 1:
                total_hex = "#x0" + str(hex(total_changes))[2:]
            else:
                total_hex = "#x" + str(hex(total_changes))[2:]
    except:
        versiondata = defaultdict()

    curr_dict = defaultdict()
    usage_dict = defaultdict(list)
    diff_dict = defaultdict(list)
    VERSION_dict = defaultdict(list)
    LENGTH_dict = defaultdict(list)
    resource_dict = defaultdict(list)

    # Parsing phase, grabbing REAL, DIFF, VERSUIB, LENGTH etc. from the smt file.
    for i in range(1):
        fn = open(newSMT, "r")
        line = fn.readline()
        #new_var_dict = defaultdict()
        new_var_set = set()
        new_version_set = set()
        while line:
            if "declare-fun" in line:
                if "_meta_REAL" in line:
                    name, name_start, name_end, label = extract(line, "REAL")
                    usage_dict[(name, line[line.find("99000"):-1])].append([int(label), line[name_start:-1]+"___0"])
                if "_meta_DIFF" in line:
                    name, name_start, name_end, label = extract(line, "DIFF")
                    diff_dict[(name, line[line.find("99000"):-1])].append([int(label), line[name_start:-1]+"___0"])
                if "VERSION" in line:
                    name, name_start, name_end, label = extract(line, "VERSION")
                    VERSION_dict[(name, line[line.find("99000"):-1])].append([int(label), line[name_start:-1]+"___0"])
                if "LENGTH" in line:
                    name, name_start, name_end, label = extract(line, "LENGTH")
                    LENGTH_dict[(name, line[line.find("99000"):-1])].append([int(label), line[name_start:-1]+"___0"])
                if "_meta_RESOURCE" in line:
                    name, name_start, name_end, label = extract(line, "RESOURCE")
                    resource_dict[(name, line[line.find("99000"):-1])].append([int(label), line[name_start:-1]+"___0"])
                if " rho_" in line:
                    start = line.find(" rho_") + 1
                elif " ." in line:
                    start = line.find(" .") + 1
                    if firsttime_flag == 0 and ("hdr_ParserImpl" in line or "hdr_MyParser" in line):
                        firsttime_flag = 1
                elif " |" in line:
                    start = line.find(" |") + 1
                else:
                    start = -1
                    print("parsing error!", line)
                
                # get version_dict for version number control
                flag = 0
                for index in range(start, len(line)):
                    if " " == line[index]:
                        new_var_set.add(line[start:index])
                        if "version.version_" in line and "PSAImpl_ingress_start" in line:
                            name = line[line.find(".hdrs"):index]
                            new_version_set.add(line[start:index])
                            for ii in range(0,int(iterNUM)):
                                version_dict[name].append(line[start:index]+"___"+str(ii))
                        flag = 1
                        break
                if flag == 0:
                    new_var_set.add(line[start:-1])
                    if "version.version_" in line and "PSAImpl_ingress_start" in line:
                        name = line[line.find(".hdrs"):-1]
                        new_version_set.add(line[start:-1])
                        for ii in range(0,int(iterNUM)):
                            version_dict[name].append(line[start:-1]+"___"+str(ii))
                      
                if "CURR" in line:
                    curr_index_start = utils.find_nth(line, "_", 1)+1
                    curr_index_end = utils.find_nth(line, "_", 2)
                    curr_name_start = line.find(".")
                    curr_name_end = line.find("\n")
                    curr_dict[(line[curr_index_start:curr_index_end], line[line.find("99000"):curr_name_end])] = line[curr_name_start:curr_name_end]

            line = fn.readline()
        fn.close()

        # read again from the beginning of SMT file, this time to get all needed variables and assertions.
        fn = open(newSMT, "r")
        flag = 0
        line = fn.readline()

        while line:
            if "assert" in line:
                flag = 1
            if True:
                temp = line[:-1].split(" ")
                for index in range(len(temp)):
                    start = 0
                    end = len(temp[index])
                    for j in range(len(temp[index])):
                        if temp[index][j] == "(":
                            start = j+1
                        elif temp[index][j] == ")":
                            end = j
                            break
                    if temp[index][start:end] in new_var_set:
                        if temp[index][start:end][-1] != "|":
                            temp[index] = temp[index][:start] + temp[index][start:end] + "___" + str(i) + temp[index][end:]
                            last_sentence[i] = temp[index][start:end] + "___" + str(i)
                            mark = temp[index][start:end]
                            if (".hdr_ParserImpl_" in mark or ".hdr_MyParser_" in mark) and "version.version" not in mark:
                                temp_index = -1
                                for item in mark[::-1]:
                                    temp_index += 1
                                    if item.isnumeric():
                                        continue
                                    else: break
                                if (mark[:-1*temp_index] not in last_ones or int(last_ones[mark[:-1*temp_index]]) < int(mark[-1*temp_index:])):
                                    last_ones[mark[:-1*temp_index]] = mark[-1*temp_index:]
  
                        else:
                            temp[index] = temp[index][:start] + temp[index][start:end-1] + "___" + str(i) + temp[index][start:end][-1] + temp[index][end:]
                            last_sentence[i] = temp[index][start:end-1] + "___" + str(i) + temp[index][start:end][-1]
                            mark = temp[index][start+1:end-1]
                            if (".hdr_ParserImpl_" in mark or ".hdr_MyParser_" in mark) and "version.version" not in mark:
                                temp_index = -1
                                for item in mark[::-1]:
                                    temp_index += 1
                                    if item.isnumeric():
                                        continue
                                    else: break
                                if (mark[:-1*temp_index] not in last_ones or int(last_ones[mark[:-1*temp_index]]) < int(mark[-1*temp_index:])):
                                    last_ones[mark[:-1*temp_index]] = mark[-1*temp_index:]
       
                if flag == 0:
                    result_declare += " ".join(temp) + line[-1]
                else:
                    result_assert += " ".join(temp) + line[-1]
                
            line = fn.readline()
        fn.close()

    # Create copies for counter examples.
    temp_declare_list, temp_assert_list = [], []
    for i in range(1,int(iterNUM)):
        temp_declare = result_declare[:]
        temp_assert = result_assert[:]
        temp_last = last_sentence[0][:]
        last_sentence[i] = temp_last.replace("___0", "___"+str(i))
        temp_declare_list.append(temp_declare.replace("___0", "___"+str(i)))
        temp_assert_list.append(temp_assert.replace("___0", "___"+str(i)))

    for item in temp_declare_list:
        result_declare += item
    for item in temp_assert_list:
        result_assert += item

    result_version, result_last = "", ""
    
    # Add learned unsat cores into the synthesis formula 
    if state == "synthesis":
        try:
            with open("unsat_lists.pickle",'rb') as f:
                unsat_lists = pickle.load(f)
        except:
            unsat_lists = []
            
        try:
            with open("unsat_program_old_lists.pickle",'rb') as f:
                unsat_program_old_lists = pickle.load(f)
        except:
            unsat_program_old_lists = []

        try:
            with open("unsat_program_new_lists.pickle",'rb') as f:
                unsat_program_new_lists = pickle.load(f)
        except:
            unsat_program_new_lists = []
    else:
        unsat_lists = []
        unsat_program_old_lists = []
        unsat_program_new_lists = []

    # if there is no definition concatenation, only this part will be executed.
    result_unsat = ""
    for unsat_list in unsat_lists:
        temp_unsat = []
        for ele, num in unsat_list:
            for key in version_dict:
                if ele + "99000" in key:
                    temp_unsat.append([key, num])

        temp_unsat.sort(key=lambda x:int(x[0][x[0].find(".hdrs_")+6:x[0].find("_PSA")]))
        temp_unsat.sort(key=lambda x:x[0][x[0].find("99000"):])

        for i in range(len(temp_unsat)//len(unsat_list)-2):
            if len(unsat_list) > 1:
                result_unsat += "(assert (not (and\n"
                for j in range(i*len(unsat_list), (i+1)*len(unsat_list)):
                    result_unsat += "    (= {}___0 {})\n".format(temp_unsat[j][0], temp_unsat[j][1])
                result_unsat += ")))\n"
            else:
                result_unsat += "(assert (not\n"
                for j in range(i*len(unsat_list), (i+1)*len(unsat_list)):
                    result_unsat += "    (= {}___0 {})\n".format(temp_unsat[j][0], temp_unsat[j][1])
                result_unsat += "))\n"
            
    # for properties with definiton concatenation, (e.g. program consistency), the logic below will be executed.
    num_copy = -1
    program_old_stats = []
    # processing the first assertion definition in the spec.
    for unsat_list in unsat_program_old_lists:
        temp_unsat = []
        for ele, num in unsat_list:
            for key in version_dict:
                if ele + "99000" in key:
                    temp_unsat.append([key, num])
        temp_unsat.sort()
        temp_unsat.sort(key=lambda x:x[0][x[0].find("99000"):])
        if num_copy == -1:
            num_copy = len(temp_unsat)//len(unsat_list)
            program_old_stats = ["(assert (or (and \n" for i in range(num_copy)]
        for i in range(len(temp_unsat)//len(unsat_list)):
            if len(unsat_list) > 1:
                program_old_stats[i] += "    (not (and\n"
                for j in range(i*len(unsat_list), (i+1)*len(unsat_list)):
                    program_old_stats[i] += "    (= {}___0 {})\n".format(temp_unsat[j][0], temp_unsat[j][1])
                program_old_stats[i] += "))\n"
            else:
                for j in range(i*len(unsat_list), (i+1)*len(unsat_list)):
                    program_old_stats[i] += "    (not (= {}___0 {}))\n".format(temp_unsat[j][0], temp_unsat[j][1])
    for i in range(num_copy):        
        program_old_stats[i] += ")\n(and \n"

    # processing the second assertion definition in the spec.
    for unsat_list in unsat_program_new_lists:
        temp_unsat = []
        for ele, num in unsat_list:
            for key in version_dict:
                if ele + "99000" in key:
                    temp_unsat.append([key, num])
        temp_unsat.sort()
        temp_unsat.sort(key=lambda x:x[0][x[0].find("99000"):])
        for i in range(num_copy):
            if len(unsat_list) > 1:
                program_old_stats[i] += "    (not (and\n"
                for j in range(i*len(unsat_list), (i+1)*len(unsat_list)):
                    program_old_stats[i] += "    (= {}___0 {})\n".format(temp_unsat[j][0], temp_unsat[j][1])
                program_old_stats[i] += "))\n"
            else:
                for j in range(i*len(unsat_list), (i+1)*len(unsat_list)):
                    program_old_stats[i] += "    (not (= {}___0 {}))\n".format(temp_unsat[j][0], temp_unsat[j][1])
    for i in range(num_copy):
        program_old_stats[i] += ")))\n"
        result_unsat += program_old_stats[i]

    try:
        with open("state.pickle",'rb') as f:
            plan = pickle.load(f)
            maxval = 0
            for key in plan:
                if "VERSION" not in key and "LENGTH" not in key:
                    result_version += "(assert (= " + key  + " " +plan[key] + "))\n"
                maxval += 1
    except:
        plan = defaultdict()

    temp_version_set = set()
    temp_version_dict = defaultdict(list)
    for key in version_dict:
        v_start = utils.find_nth(key, "_", 1) + 1
        v_end = utils.find_nth(key, "_", 2)
        v_name = int(key[v_start:v_end])
        temp_version_dict[v_name].append(sorted(version_dict[key])[0])
        temp_version_set.add(v_name)
    temp_version_list = list(temp_version_set)
    temp_version_list.sort()

    if int(iterNUM) >= 2:
        for key in version_dict:
            result_version += "(assert (= " +" ".join(version_dict[key]) + "))\n"

    if state == "verify":
        try:
            with open("plan.pickle",'rb') as f:
                assignments = pickle.load(f)
        except:
            print("Warning: no transition plan for verification?")
            assignments = defaultdict(list)
        temp_list = []
        for key in assignments:
            temp_list.append([key,assignments[key]])
        temp_list.sort()
        for key, val in temp_list:
            if "VERSION" not in key and "LENGTH" not in key:
                result_version += "(assert (= " + key + " " + val  + "))\n"
        
    elif state == "synthesis":
        example_list = []
        try:
            with open("assignments.pickle",'rb') as f:
                try:
                    index = int(iterNUM) - 1
                    while index > 0:
                        assignments = pickle.load(f)
                        example_list.append(assignments)
                        index -= 1
                except: pass
        except: pass
        
        for index in range(len(example_list)):
            for key in example_list[index]:
                if ".elements[" not in key:
                    result_version += "(assert (= " + key + "___" + str(index) + " " + example_list[index][key] + "))\n"
                elif ".elements[" in key:
                    result_version += "(assert (= |" + key + "___" + str(index) + "| " + example_list[index][key] + "))\n"
        if maxsat == "on":
            for key in curr_dict:
                result_last += "(maximize {}___0)\n".format(curr_dict[key])
                #result_last += "(assert-soft (= {} {}___0))\n".format(total_hex, curr_dict[key])
            for key in diff_dict:
                temp_list = diff_dict[key]
                temp_list.sort()
                result_last += "(maximize {})\n".format(temp_list[-1][-1])
        
        # Most commonly used objectives for reource and number of states.
        if minimize == "on":
            for key in diff_dict:
                temp_list = diff_dict[key]
                temp_list.sort()
                result_last += "(maximize {})\n".format(temp_list[-1][-1])
                #print(temp_list[-1][-1])
            for key in curr_dict:
                #result_last += "(assert-soft (= {} {}___0))\n".format(total_hex, curr_dict[key])
                result_last += "(maximize {}___0)\n".format(curr_dict[key])

        if minimize == "inc":
            for key in diff_dict:
                temp_list = diff_dict[key]
                temp_list.sort()
                result_last += "(maximize {})\n".format(temp_list[-1][-1])
                print("inc:", temp_list[-1][-1])

        if minimize == "reverse":
            for key in diff_dict:
                temp_list = diff_dict[key]
                temp_list.sort()
                result_last += "(maximize {})\n".format(temp_list[-1][-1])
            for key in curr_dict:
                result_last += "(minimize {}___0)\n".format(curr_dict[key])
                #result_last += "(assert-soft (bvule {} {}___0))\n".format(total_hex, curr_dict[key])
        
        if minimize == "nomin":
            for key in curr_dict:
                #result_last += "(minimize {}___0)\n".format(curr_dict[key])
                result_last += "(assert-soft (not (bvule {} {}___0)))\n".format(total_hex, curr_dict[key])
            for key in diff_dict:
                temp_list = diff_dict[key]
                temp_list.sort()
                result_last += "(minimize {})\n".format(temp_list[-1][-1])
        
        if minimize == "lower":
            for key in curr_dict:
                result_last += "(minimize {}___0)\n".format(curr_dict[key])
            for key in diff_dict:
                temp_list = diff_dict[key]
                temp_list.sort()
                result_last += "(maximize {})\n".format(temp_list[-1][-1])

        # Deprecated way for guaranteeing program consistency
        if cause == "program_consistency":
            VERSION_list = []
            LENGTH_list = []
            for key in VERSION_dict:
                temp_list = VERSION_dict[key]
                temp_list.sort()
                VERSION_list.append(temp_list[-1][-1])
            for key in LENGTH_dict:
                temp_list = LENGTH_dict[key]
                temp_list.sort()
                LENGTH_list.append(temp_list[-1][-1])
            VERSION_list.sort()
            LENGTH_list.sort()
            for index1 in range(len(VERSION_list)):
                result_last += "(assert (or (and\n"
                for index2 in range(int(iterNUM)):
                    result_last += "(= " + VERSION_list[index1][:-1]+str(index2) + " " + LENGTH_list[index1][:-1]+str(index2) + ")\n"
                result_last += ")\n(and\n"
                for index2 in range(int(iterNUM)):
                    result_last += "(= " + VERSION_list[index1][:-1]+str(index2) + " " + "#x00" + ")\n"
                result_last += ")))\n"

        if "test" in incremental:
            for key in diff_dict:
                temp_list = diff_dict[key]
                temp_list.sort()
                if "metas_0_" in key[0]:
                    DIFF = temp_list[-1][-1]
            for key in resource_dict:
                temp_list = resource_dict[key]
                temp_list.sort()
                if "metas_5_" in key[0]:
                    RESOURCE2 = temp_list[-1][-1]
                if "metas_0_" in key[0]:
                    RESOURCE1 = temp_list[-1][-1]
            result_last += "(declare-fun Objective () (_ BitVec 32))\n"
            result_last += "(assert (= Objective (bvmul {} (bvadd {} {} (bvmul #xffffffff {})))))\n".format(DIFF, "#x00002000", RESOURCE2, RESOURCE1)
            result_last += "(maximize Objective)\n"
       
        # optimization for incremental verification
        if  "optimize" in incremental:
            true_count = int(incremental[incremental.find("_")+1:])
            print("optimized iteration: {}".format(str(true_count)))
            if true_count == 1 or true_count % 2 == 0:
                for key in diff_dict:
                    temp_list = diff_dict[key]
                    temp_list.sort()
                    result_last += "(maximize {})\n".format(temp_list[-1][-1])
                for key in curr_dict:
                    result_last += "(maximize {}___0)\n".format(curr_dict[key])
            else:
                len_temp1, len_temp2 = 0, 0
                for key in curr_dict:
                    if "metas_0_" in curr_dict[key]:
                        CURR1= curr_dict[key]
                    if "metas_5_" in curr_dict[key]:
                        CURR2= curr_dict[key]
                len_temp = max(len_temp1, len_temp2)
                hex_constraint = str(hex(len_temp))[2:]
                metric1 = "#x" + "0"*(2-len(hex_constraint)) + hex_constraint
                result_last += "(assert-soft (bvule (bvadd {}___0 {}) {}___0))\n".format(CURR1, metric1, CURR2)

                for key in diff_dict:
                    temp_list = diff_dict[key]
                    temp_list.sort()
                    result_last += "(maximize {})\n".format(temp_list[-1][-1])
                
        result_last += "(check-sat)\n"
        result_last += "(get-model)"

    fo.write(result_declare+result_assert+result_version+result_unsat+result_last)
    fo.close()

if __name__ == "__main__":
    main()
