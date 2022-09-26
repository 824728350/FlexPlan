from collections import defaultdict
import utils
import os
import pickle

def main():
    try:
        with open("resource_dict.pickle",'rb') as f:
            resource_dict = pickle.load(f)
    except:
        resource_dict = defaultdict()

    states = defaultdict(list)
    if not os.path.exists("output-plan"):
        print("Update plan does not exist!!!")
        return
    with open("output-plan",'r') as fo:
        line = fo.readline()
        while line:
            index_start = utils.find_nth(line, ".hdrs_", 1) + len(".hdrs_")
            index_end = utils.find_nth(line, "_", 2)
            index = int(line[index_start:index_end])
            name_start = utils.find_nth(line, ".version__", 1) + len(".version__")
            name_end = utils.find_nth(line, "_299000", 1)
            name = line[name_start:name_end]
            value_start = utils.find_nth(line, "#b", 1) + len("#b")
            value_end = utils.find_nth(line, "\n", 1)
            value = int(line[value_start:value_end])
            states[index].append([name, value])
            line = fo.readline()
    temp_list = list(states.keys())
    temp_list.sort()
    
    transition = []
    for j in range(len(states[temp_list[0]])):  
        if states[temp_list[0]][j][1] == 1:
            transition.append(states[temp_list[0]][j][0])
    if transition != []:
        print("\nduring the 1st transition, you should change the following components: \n")
        for item in transition:
            print("Annotation name: ", item, "    old usage: ", resource_dict["version__"+item][0], "    new usage: ", resource_dict["version__"+item][1])

    for i in range(1,len(temp_list)):
        transition = []
        for j in range(len(states[temp_list[i]])):
            if states[temp_list[i]][j][1] == 1 and states[temp_list[i-1]][j][1] == 0:
                transition.append(states[temp_list[i]][j][0])
        if transition != []:
            print("\nduring the {}th transition, you should change the following components: \n".format(i+1))
            for item in transition:
                print("Annotation name: ", item, "    old usage: ", resource_dict["version__"+item][0], "    new usage: ", resource_dict["version__"+item][1])

    transition = []
    for j in range(len(states[len(temp_list)-1])):  
        if states[temp_list[len(temp_list)-1]][j][1] == 0:
            transition.append(states[temp_list[len(temp_list)-1]][j][0])
            #print(states[temp_list[len(temp_list)-1]][j][0])
    if transition != []:
        print("\nduring the {}th transition, you should change the following components: \n".format(len(temp_list)+1))
        for item in transition:
            print("Annotation name: ", item, "    old usage: ", resource_dict["version__"+item][0], "    new usage: ", resource_dict["version__"+item][1])

if __name__ == "__main__":
    main()