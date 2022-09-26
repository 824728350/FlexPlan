from collections import defaultdict
import os
import argparse
from subprocess import STDOUT, check_output
import subprocess
import time
import pickle
'''
Unsat core learning for targeted program and user specifications.
'''
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsl", help="dsl file")
    parser.add_argument("--p4", help="p4 bash")
    parser.add_argument("--id", help="id")
    parser.add_argument("--mode", help="mode")
    parser.add_argument("--period", help="period")
    parser.add_argument("--timeout", help="timeout")
    args = parser.parse_args()
    return args

def find_unsat_cores(filename, period, timeout, unsat_lists, pickle_file):
    start_time = time.time()
    result = []
    flag_sat = 0

    # Initiate distill_init and p4c analysis to generate smt templates
    fo = open(filename, "r")
    fs = open("solve-distill.smt", "w")
    line1 = fo.readline()
    result = ""
    version_unsat_dict = defaultdict(list)
    version_unsat_set = set()
    while line1:
        if "(declare-fun" in line1 and "version.version" in line1 and "_PSAImpl_" in line1:
            version_name_start = line1.find(".hdrs_") + 6
            version_name_end = line1.find("_PSAImpl_")
            version_name = line1[version_name_start:version_name_end]
            version_unsat_dict[version_name].append(line1[line1.find(".hdrs_"):-1])
            version_unsat_set.add(version_name)
        result += line1
        line1 = fo.readline()
    
    # Old and new version of program should take all 0 and all 1 for vsk.
    result_last = ""
    version_unsat_list = list(version_unsat_set)
    version_unsat_list.sort()
    if len(version_unsat_list) >= 3:
        for item in version_unsat_dict[version_unsat_list[1]]:
            result_last += "(assert (= {} {}))\n".format(item, "#b0")
        for item in version_unsat_dict[version_unsat_list[2]]:
            result_last += "(assert (= {} {}))\n".format(item, "#b1")
    result_last += "(check-sat)\n"
    result_last += "(get-model)\n"
    fs.write(result+result_last)
    fs.close()
    fo.close()
    
    try:
        with open("unsat_results.pickle",'rb') as f:
            unsat_results = pickle.load(f)
            result += unsat_results
    except:
        #print("No previous unsat results!")
        unsat_results = ""

    while True:
        #print(time.time() - start_time)
        # Takes too long in the unsat core learning phase...
        if time.time() - start_time > period:
            print("Terminate unsat core learning due to time out!")
            with open("version_unsat_dict.pickle",'wb') as fvv:
                pickle.dump(version_unsat_dict, fvv)
            break
        # Unsat core size is too large or too small for some time...
        if flag_sat >= 20:
            print("Terminate unsat core learning due to unsat core size!")
            with open("version_unsat_dict.pickle",'wb') as fvv:
                pickle.dump(version_unsat_dict, fvv)
            break
        # Determine whether there are still any possible counter examples left
        solver = "timeout " + str(timeout) + " z3 -smt2 solve-distill.smt >output-solve 2>output-solve"
        process = subprocess.Popen(solver, shell=True, stdout=subprocess.PIPE)
        process.wait()
        
        flag_unsat = 2
        ft = open("output-solve", "r")
        line3 = ft.readline()
        # If no more counter example, terminate unsat core learning. 
        while line3:
            if "unsat" in line3:
                flag_unsat = 1
                break
            elif "sat" in line3:
                flag_unsat = 0
            line3 = ft.readline()

        if (flag_unsat == 1):
            print("End of distillation", time.time() - start_time)
            with open("output-fin",'w') as fo:
                fo.write("FIN")
            with open("version_unsat_dict.pickle",'wb') as fvv:
                pickle.dump(version_unsat_dict, fvv)
            break
        elif (flag_unsat == 2):
            print("Terminate unsat core learning because it takes too long to generate next unsat core!", time.time() - start_time)
            with open("version_unsat_dict.pickle",'wb') as fvv:
                pickle.dump(version_unsat_dict, fvv)
            break
        # If there are still counter examples, distill counter example to generate the nextunsat core.
        solver = "python3 distill_example.py"
        process = subprocess.Popen(solver, shell=True, stdout=subprocess.PIPE)
        process.wait()

        solver = "z3 -smt2 distill.smt >output-uc 2>output-uc"
        process = subprocess.Popen(solver, shell=True, stdout=subprocess.PIPE)
        process.wait()
        
        # If no unsat core is generated, don't give up just yet, prevent previous assignment and try again.
        fu = open("output-uc", "r")
        line2 = fu.readline()
        unsat_list = []
        while line2:
            if  line2[:5] == "unsat":
                pass
                #print("unsat")
            elif line2[:3] == "sat":
                pass
                #print("sat")
            if line2[:2] == "(a":
                unsat_list = line2[1:-2].split(" ")
            line2 = fu.readline()
        if len(unsat_list) >= 1:
            print(unsat_list)
        if unsat_list == []:
            flag_sat += 1
            result_ce = ""
            fun = open("unfinished.pickle",'rb')
            assignments = pickle.load(fun)
            result_ce += "(assert (not (and "
            for key in assignments:
                result_ce += "(= {} {})\n".format(key, assignments[key])
            result_ce += ")))\n"
            fw = open("solve-distill.smt", "w")
            fw.write(result+result_ce+result_last)
            fw.close()
            continue
        else:
            pass
        try:
            with open("unsat.pickle",'rb') as fu:
                unsat_dict = pickle.load(fu)
        except:
            #print("End of pickle! No unsat dict.")
            unsat_dict = defaultdict()

        fw = open("solve-distill.smt", "w")
        unsat_final = []
        b0 = 0
        b1 = 0
        for key in unsat_list:
            if unsat_dict[key][1] == "#b1":
                b1 = 1
            else:
                b0 = 1
        # If for some reason unsat.pickle does not give correct unsat core, don't give up just yet.
        #if b1 == 0 and b0 == 0:
        if ("new" in filename and b1 == 1) or ("old" in filename and b0 == 1) or (b1 == 0 and b0 == 0):
            result_ce = ""
            fun = open("unfinished.pickle",'rb')
            assignments = pickle.load(fun)
            #print(assignments)
            result_ce += "(assert (not (and "
            for key in assignments:
                result_ce += "(= {} {})\n".format(key, assignments[key])
            result_ce += ")))\n"
            fw = open("solve-distill.smt", "w")
            fw.write(result+result_ce+result_last)
            fw.close()
            continue
        unsat_lists.append([])
        # install the learned unsat core to the smt template, so that we have less and less counter examples.
        if len(unsat_list) >= 2:
            for key in unsat_list:
                unsat_final.append("(= {} {})".format(unsat_dict[key][0], unsat_dict[key][1]))
                print(unsat_dict[key][0], unsat_dict[key][1])
                unsat_lists[-1].append([unsat_dict[key][0][unsat_dict[key][0].find(".version")+1:], unsat_dict[key][1]])
            result += "(assert (not (and\n        " + "\n        ".join(unsat_final) + ")))\n"
            unsat_results += "(assert (not (and\n        " + "\n        ".join(unsat_final) + ")))\n"
        else:
            for key in unsat_list:
                unsat_final.append("(= {} {})".format(unsat_dict[key][0], unsat_dict[key][1]))
                print(unsat_dict[key][0], unsat_dict[key][1])
                unsat_lists[-1].append([unsat_dict[key][0][unsat_dict[key][0].find(".version")+1:], unsat_dict[key][1]])
            result += "(assert (not\n        " + "\n        ".join(unsat_final) + "))\n"
            unsat_results += "(assert (not\n        " + "\n        ".join(unsat_final) + "))\n"
        if len(unsat_list) >= 5 or len(unsat_list) <= 0:
            flag_sat += 2
        fw.write(result+result_last)
        fw.close()
        with open(pickle_file,'wb') as f:
            pickle.dump(unsat_lists, f)
    return unsat_results, unsat_lists


def main():
    pid = os.getpid()
    with open("uc_pid.pickle",'wb') as f:
        pickle.dump(pid, f)
    args = parse_args()
    ID = str(args.id)
    period = int(args.period)
    timeout = int(args.timeout)
    print(period, timeout)
    unsat_lists = []
    unsat_lists_old = []
    unsat_lists_new = []
    unsat_lists_o = []
    
    for filename in os.listdir("./"):
        if ID in filename and "-dis-" in filename and ".smt" in filename:
            print(filename)
            if "old" in filename:
                try:
                    with open("unsat_program_old_lists.pickle",'rb') as f:
                        unsat_lists = pickle.load(f)
                except:
                    unsat_lists = []
                unsat_results, unsat_lists_temp = find_unsat_cores("./" + filename, 6000, 60, unsat_lists, "unsat_program_old_lists.pickle")
                unsat_lists_old += unsat_lists_temp
            elif "new" in filename:
                try:
                    with open("unsat_program_new_lists.pickle",'rb') as f:
                        unsat_lists = pickle.load(f)
                except:
                    unsat_lists = []
                unsat_results, unsat_lists_temp = find_unsat_cores("./" + filename, 6000, 60, unsat_lists, "unsat_program_new_lists.pickle")
                unsat_lists_new += unsat_lists_temp
            else:
                try:
                    with open("unsat_lists.pickle",'rb') as f:
                        unsat_lists = pickle.load(f)
                except:
                    unsat_lists = []
                unsat_results, unsat_lists_temp = find_unsat_cores("./" + filename, period, timeout, unsat_lists, "unsat_lists.pickle")
                unsat_lists_o += unsat_lists_temp

    if unsat_lists != []:
        with open("unsat_lists.pickle",'wb') as f:
            pickle.dump(unsat_lists_o, f)
        with open("unsat_results.pickle",'wb') as f:
            pickle.dump(unsat_results, f)
    if unsat_lists_old != []:
        with open("unsat_program_old_lists.pickle",'wb') as f:
            pickle.dump(unsat_lists_old, f)
        with open("unsat_program_old_results.pickle",'wb') as f:
            pickle.dump(unsat_results, f)
    if unsat_lists_new != []:
        with open("unsat_program_new_lists.pickle",'wb') as f:
            pickle.dump(unsat_lists_new, f)
        with open("unsat_program_new_results.pickle",'wb') as f:
            pickle.dump(unsat_results, f)
    
if __name__ == "__main__":
    main()
