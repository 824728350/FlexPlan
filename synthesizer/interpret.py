import pickle
from collections import defaultdict
import argparse
import utils

'''
Interpret the result generated by update plan synthesizer, generate output
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--constraint", help="constraint")
    args = parser.parse_args()
    constraint = str(args.constraint)

    finished_states = 0
    total_states = 0

    try:
        with open("state.pickle",'rb') as f:
            assignments = pickle.load(f)
    except:
        print("Warning: no transition plan for verification?")
        assignments = defaultdict(list)

    try:
        with open("usage.pickle",'rb') as f:
            usages = pickle.load(f)
    except:
        print("Warning: no resource usage for verification?")
        usages = defaultdict(list)

    temp_list = []
    value_set = set()
    for key in assignments:
        if "version.version" not in key:
            continue
        if "#b1" in assignments[key]:
            finished_states += 1
        total_states += 1
        value = int(key[key.find("_")+1:utils.find_nth(key,"_",2)])
        temp_list.append([value, key, assignments[key]])
        value_set.add(value)
        #print(key, assignments[key])
    temp_list.sort()
    value_list = list(value_set)
    value_list.sort()
    value_list = value_list[:-2]
    temp_list.sort(key=lambda x:x[1][x[1].find("99000"):])
    
    output = ""
    for value, var, assign in temp_list:
        if value in value_list:
            output += var + "  " + assign + "\n"
    #print(temp_list)

    with open("output-plan",'w') as fo:
        fo.write(output)
    
    final_dict = defaultdict(int)
    for _, key, value in temp_list:
        index = int(key[key.find("_")+1:key.find("_PSAImpl")])
        if value == "#b1":
            final_dict[index] += 1
        #print(key, value)
    final_list = []
    for key in final_dict:
        final_list.append(key)
    final_list.sort()
    result_list = []
    for key in final_list:
        result_list.append(final_dict[key])
    #print(total_states, finished_states)
    print("number of changes made so far: ", result_list)
    if len(result_list) >= 2:
        if result_list[-1] == result_list[-2] and args.constraint == "100000":
            print("Introspection figured out enlarging sequence length does not help anymore, exit CEGIS loop!")
            ft = open("termination", "w")
            ft.write("EXIT!")
            ft.close()

    for key in usages:
        usage_list = usages[key]
        usage_list.sort()
        if "DIFF" in key:
            #print(key, usage_list[-1])
            print("resource spike: ", int(constraint) - int("0"+usage_list[-1][-1][1:], 16))

if __name__ == "__main__":
    main()