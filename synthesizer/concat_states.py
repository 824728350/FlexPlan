from collections import defaultdict
import argparse
import pickle
import utils
'''
Connecting transition states and distinguish vairiable names. 
TODO: how to get longer update plan formula without invoking frontend translation
      multiple times? This should speed up the tool when user spec is simple...
'''
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="output file")
    parser.add_argument("--input", help="smt file prefixes")
    parser.add_argument("--iter", help="iter num")
    parser.add_argument("--cause", help="hard root cause analysis")
    parser.add_argument("--incremental", help="incremental")
    args = parser.parse_args()
    outSMT = str(args.output)
    inSMT = str(args.input)
    iterNUM = int(args.iter)
    cause = str(args.cause)
    incremental = str(args.incremental)
    fo = open(outSMT, "w")
    result_declare = ""
    result_assert = ""
    version_dict = defaultdict(list)

    fn = open(inSMT, "r")
    line = fn.readline()
    new_var_dict = defaultdict()
    new_var_set = set()
    new_version_set = set()
    while line:
        if "declare-fun" in line:
            if "_meta_REAL" in line:
                name_start = line.find(".")
                name_end = line.find("REAL") + 4
                name = line[name_start:name_end]
            if " rho_" in line:
                start = line.find(" rho_") + 1
            elif " ." in line:
                start = line.find(" .") + 1
            elif " |" in line:
                start = line.find(" |") + 1
            else:
                start = -1
                print("parsing error!", line)
            end = -1
            for index in range(start, len(line)):
                if " " == line[index]:
                    end = index
                    break
            var_name = line[start:end]
            new_var_set.add(line[start:end])
            if "version.version_" in line and "PSAImpl_ingress_start" in line:
                name = line[line.find(".hdrs"):end]
                new_version_set.add(line[start:end])
                version_dict[name].append(line[start:end])

            temp_lines = []
            depth, start_flag = 0, 0
            while depth != 0 or start_flag == 0:
                temp_lines.append(line)
                for item in line:
                    if item == "(":
                        depth += 1
                    elif item == ")":
                        depth -= 1
                start_flag = 1
                line = fn.readline()
            new_var_dict[var_name] = temp_lines
            if start_flag == 1:
                continue
        line = fn.readline()
    fn.close()

    fn = open(inSMT, "r")
    flag = 0
    fork_flag = 0
    line = fn.readline()
    fork_var_set = set()
    while line:
        if "(assert" in line:
            flag = 1
        if flag == 1:
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
                if temp[index][start:end] in new_var_set and ("hdrs" in temp[index][start:end] or ("metas_" in temp[index][start:end] and "metas__" not in temp[index][start:end])): 
                    fork_flag = 1
                if temp[index][start:end] in new_var_set and fork_flag == 0:
                    fork_var_set.add(temp[index][start:end])
                elif temp[index][start:end] in new_var_set and fork_flag == 1:
                    if ".hdr_"  in temp[index][start:end] or ".metas__" in temp[index][start:end]:
                        fork_var_set.add(temp[index][start:end])
        line = fn.readline()
    fn.close()

    for key in new_var_dict:
        if key in fork_var_set:
            for item in new_var_dict[key]:
                result_declare += item

    # add declarations for each distinct transition state
    for n in range(iterNUM):
        for key in new_var_dict:
            if key not in fork_var_set:
                for item in new_var_dict[key]:
                    temp = item[:-1].split(" ")
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
                                temp[index] = temp[index][:start] + temp[index][start:end] + "99000" + str(n) + temp[index][end:]
                            else:
                                temp[index] = temp[index][:start] + temp[index][start:end-1] + "99000" + str(n) + temp[index][start:end][-1] + temp[index][end:]
                    result_declare += " ".join(temp) + item[-1]

    fn = open(inSMT, "r") 
    line = fn.readline()
    flag, fork_flag, start_flag = 0, 0, 0
    norm_assert_dict = defaultdict()
    fork_assert_dict = defaultdict()
    t_index = 0
    while line:
        if "(assert" in line:
            flag = 1
            t_index += 1
        if flag == 1:
            temp_lines = []
            depth, start_flag, fork_flag = 0, 0, 0
            while depth != 0 or start_flag == 0:
                temp_lines.append(line)
                for item in line:
                    if item == "(":
                        depth += 1
                    elif item == ")":
                        depth -= 1
                start_flag = 1
                line = fn.readline()
            for item in temp_lines:
                temp = item[:-1].split(" ")
                for index in range(len(temp)):
                    start = 0
                    end = len(temp[index])
                    for j in range(len(temp[index])):
                        if temp[index][j] == "(":
                            start = j+1
                        elif temp[index][j] == ")":
                            end = j
                            break
                    if temp[index][start:end] in new_var_set and temp[index][start:end] not in fork_var_set:
                        fork_flag = 1
            if fork_flag == 1:
                fork_assert_dict[t_index] = temp_lines
            else:
                norm_assert_dict[t_index] = temp_lines
            if start_flag == 1:
                continue
        line = fn.readline()
    fn.close()    

    for key in norm_assert_dict:
        for item in norm_assert_dict[key]:
            result_assert += item
    for n in range(iterNUM):
        for key in fork_assert_dict:
            for item in fork_assert_dict[key]:
                temp = item[:-1].split(" ") 
                for index in range(len(temp)):
                    start = 0
                    end = len(temp[index])
                    for j in range(len(temp[index])):
                        if temp[index][j] == "(":
                            start = j+1
                        elif temp[index][j] == ")":
                            end = j
                            break
                    if temp[index][start:end] in new_var_set and temp[index][start:end] not in fork_var_set:
                        if temp[index][start:end][-1] != "|":
                            temp[index] = temp[index][:start] + temp[index][start:end] + "99000" + str(n) + temp[index][end:]
                        else:
                            temp[index] = temp[index][:start] + temp[index][start:end-1] + "99000" + str(i) + temp[index][start:end][-1] + temp[index][end:]
                result_assert += " ".join(temp) + item[-1] 

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
    result_version = ""

    if len(temp_version_list) >= 3:
        list1 = sorted(temp_version_dict[temp_version_list[-1]])
        list2 = sorted(temp_version_dict[temp_version_list[-2]])
        list3 = sorted(temp_version_dict[temp_version_list[0]])
        plan = defaultdict()
        try:
            with open("constrained_variables.pickle",'rb') as f:
                constrained_variables = pickle.load(f)
        except:
            constrained_variables = []
        for n in range(iterNUM):
            if n+1 < iterNUM:
                for index in range(len(list1)): 
                    result_version += "(assert (= {} {}))\n".format(list1[index]+"99000"+str(n), list2[index]+"99000"+str(n+1))
        for index in range(len(list1)):
            if cause == "on":
                result_version += "(assert-soft (= {} {}))\n".format(list1[index]+"99000"+str(iterNUM-1), "#b1")
            elif cause == "unfree":
                flag_constrained = 0
                for item in constrained_variables:
                    if "version_" + item in list1[index]:
                        print(list1[index], "version_" + item)
                        result_version += "(assert (= {} {}))\n".format(list1[index]+"99000"+str(iterNUM-1), "#b1")
                        flag_constrained = 1
                        break
                if flag_constrained == 0:
                    result_version += "(assert (= {} {}))\n".format(list1[index]+"99000"+str(iterNUM-1), "#b0")
            else:
                result_version += "(assert (= {} {}))\n".format(list1[index]+"99000"+str(iterNUM-1), "#b1")
        for index in range(len(list1)):
            if incremental == "off":
                result_version += "(assert (= {} {}))\n".format(list2[index]+"99000"+str(0), "#b0")
            else:
                result_version += "(assert (= {} {}))\n".format(list2[index]+"99000"+str(0), "#b0")
                plan[list3[index]+"99000"+str(0)+"___0"] = "#b0"

    result_check = ""
    fo.write(result_declare+result_assert+result_version+result_check)
    fo.close()

if __name__ == "__main__":
    main()
