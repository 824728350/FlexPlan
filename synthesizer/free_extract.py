from collections import defaultdict
import argparse
import pickle

'''
Introspection check, find free variables.
'''
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", help="id")
    args = parser.parse_args()
    return args

# Deprecated, will be removed in the future.
def extract_from_smt():
    args = parse_args()
    ID = str(args.id)

    try:
        fo = open("direct-{}-{}-merge.smt".format(ID, "free"), "r")
    except:
        return
    line1 = fo.readline()
    version_unsat_dict = defaultdict(list)
    version_unsat_set = set()
    while line1:
        if "(declare-fun" in line1 and "version.version" in line1 and "_PSAImpl_" in line1:
            version_name_start = line1.find(".hdrs_") + 6
            version_name_end = line1.find("_PSAImpl_")
            version_name = line1[version_name_start:version_name_end]
            version_unsat_dict[version_name].append(line1[line1.find(".hdrs_"):-1])
            version_unsat_set.add(version_name)
        
        line1 = fo.readline()
    
    version_unsat_list = list(version_unsat_set)
    print(version_unsat_dict)
    version_unsat_list.sort()
    constrained_variables = []
    if len(version_unsat_list) >= 2:
        '''
        for item in version_unsat_dict["hdr"]:
            constrained_variables.append(item[item.find(".version_")+9:])
        '''
        for item1, item2 in zip(version_unsat_dict[version_unsat_list[0]], version_unsat_dict[version_unsat_list[1]]):
            constrained_variables.append(item1[item1.find(".version_")+9:])
    fo.close()
    print(constrained_variables, len(constrained_variables))
    with open("constrained_variables.pickle",'wb') as f:
        pickle.dump(constrained_variables, f)

# By free variables, we mean version numbers that could be changed anytime.
# The benefit of finding them before cegis is because we could fix free delete to be in the
# first transtion state, while free add to be in the last transition state, reducing the
# search space for both cegis and introspection.
def extract_from_uc():
    try:
        with open("unsat_lists.pickle",'rb') as f:
            unsat_lists = pickle.load(f)
    except:
        unsat_lists = []
        #print("No unsat at this point!")
    try:
        with open("unsat_program_old_lists.pickle",'rb') as f:
            unsat_program_old_lists = pickle.load(f)
    except:
        unsat_program_old_lists = []
        #print("No unsat program old at this point!")
    try:
        with open("unsat_program_new_lists.pickle",'rb') as f:
            unsat_program_new_lists = pickle.load(f)
    except:
        unsat_program_new_lists = []
        #print("No unsat program new at this point!")
    constrained_variables_set = set()
    for uc in unsat_lists+unsat_program_old_lists+unsat_program_new_lists:
        for name, val in uc:
            constrained_variables_set.add(name[name.find("version_")+8:])
    constrained_variables = list(constrained_variables_set)
    #print(constrained_variables, len(constrained_variables))
    with open("constrained_variables.pickle",'wb') as f:
        pickle.dump(constrained_variables, f)

if __name__ == "__main__":
    extract_from_uc()
