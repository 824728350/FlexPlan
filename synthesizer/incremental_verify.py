from collections import defaultdict
import argparse
import pickle
import utils

'''
incremental verification (Snap V) optimization, to reduce verification time
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    args = parser.parse_args()
    src = str(args.src)
    result = ""

    try:
        with open("plan.pickle",'rb') as f:
            assignments = pickle.load(f)
    except:
        print("Warning: no transition plan for verification?")
        assignments = defaultdict(list)

    temp_set = set()
    temp_dict = defaultdict(list)
    for key in assignments:
        if "version.version" not in key:
            continue
        temp_dict[(key[utils.find_nth(key, "_", 1): utils.find_nth(key, "_start", 1)], key[key.find("99000"):])].append(assignments[key])

    # find the snapshots that are actually transition states.
    # i.e. there are some changeing components that are old, and there are some that are new.
    max_count = 0
    for key in temp_dict:
        count, count_1 = 0, 0
        for item in temp_dict[key]:
            count += 1
            if item == "#b1":
                count_1 += 1
        max_count = max(max_count, count_1)
        if count != count_1 and count_1 != 0:
            temp_set.add(key)

    index = 1
    version_num = ""
    temp_list = list(temp_set)
    temp_list.sort()
    for key in temp_list:
        ele1 = key[0]
        fn = open(src + ".smt", "r")
        line = fn.readline()
        while line:
            if ".hdrs_0_PSAImpl_ingress_start" in line and "declare-fun" in line and ("version.version" in line or "version.VERSION" in line):
                version_num = line[line.find("."):line.find(".version.")]
            result += line
            line = fn.readline()

        LENGTH, VERSION = "", ""
        result_old, result_new = "", ""
        for version_key in assignments:
            if ele1 in version_key and "VERSION" not in version_key and "LENGTH" not in version_key and "version.version" in version_key:
                result += "(assert (= {} {}))\n".format(version_num+version_key[version_key.find(".version"):version_key.find("___0")], assignments[version_key])
            if ele1 in version_key and "VERSION" in version_key:
                result_old = "(assert (not (= {} {})))\n".format(version_num+version_key[version_key.find(".version"):version_key.find("___0")], "#x00")
                if LENGTH != "":
                    result_new = "(assert (not (= {} {})))\n".format(version_num+version_key[version_key.find(".version"):version_key.find("___0")], LENGTH)
                VERSION = version_num+version_key[version_key.find(".version"):version_key.find("___0")]
            if ele1 in version_key and "LENGTH" in version_key:
                if VERSION != "":
                    result_new = "(assert (not (= {} {})))\n".format(version_num+version_key[version_key.find(".version"):version_key.find("___0")], VERSION)
                LENGTH = version_num+version_key[version_key.find(".version"):version_key.find("___0")]
            if ele1 in version_key and ("sawOld" in version_key or "sawNew" in version_key):
                result_old = "(assert (= {} {}))\n".format(version_num+version_key[version_key.find(".version"):version_key.find("___0")], "#b1")
                #print(version_key)

        fw = open("verify-simple" + str(index) + ".smt", "w")

        result_last = ""
        result_last += "(check-sat)\n"
        result_last += "(get-model)\n"
        fn.close()
        fw.write(result+result_last)
        fw.close()
        fo = open("verify-old" + str(index) + ".smt", "w")
        fo.write(result+result_old+result_last)
        fo.close()
        ff = open("verify-new" + str(index) + ".smt", "w")
        ff.write(result+result_new+result_last)
        ff.close()
        result = ""
        index += 1

if __name__ == "__main__":
    main()
