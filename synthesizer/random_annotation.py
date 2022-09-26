from collections import defaultdict
import argparse
import pickle
import random

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    parser.add_argument("--num_mod", help="tune the total num of modifications")
    parser.add_argument("--num_add", help="tune the total num of additions")
    parser.add_argument("--num_del", help="tune the total num of deletions")
    args = parser.parse_args()
    return args

# select random changes with tunable portion of add, del and mod
def select_random_changes(args):
    src = str(args.src)
    num_mod = int(args.num_mod)
    num_add = int(args.num_add)
    num_del = int(args.num_del)

    f = open(src+"-clean-init.p4", "r")
    w = open(src+"-clean-anno.p4", "w")
    result = ""
    line = f.readline()

    table_version_dict = defaultdict()
    count, count_add = 0, 0
    count_delete, count_change = 0, 0
    flag_change = 0
    change_name = ""
    change_type_dict = defaultdict()
    while line:    
        if ".apply();" in line:
            for index in range(len(line)):
                if line[index] != " ":
                    table_name_start = index
                    break
            
            table_name_end = line.find(".apply();")
            table_name = line[table_name_start:table_name_end]
            if "set_primitive_metadata" in table_name:
                flag_change = 0
                line = f.readline()
                continue
            # Cannot handle urpf changes for now, will fix in the future 
            if "urpf" in table_name:
                result += line
                flag_change = 0
                line = f.readline()
                continue 
            # the "new" part of modification, simply the next encountered table after the "old" one.
            if flag_change == 1:
                result += " "*table_name_start + "@mod({}, new) ".format(change_name) + "{" + table_name + ".apply();}\n"
                print(change_name, table_name, "change")
                line = f.readline()
                flag_change = 0
                change_name = ""
                continue
            # randomly 
            choice = random.randint(1,100)
            if choice <= num_add: 
                # consider the table to be added for the new version
                result += " "*table_name_start + "@add({}) ".format(table_name) + "{" + table_name + ".apply();}\n"
                table_version_dict[table_name] = "add"
                print(table_name, "add")
                change_type_dict[table_name] = "add"
                count += 1
                count_add += 1
            elif choice <= num_del+num_add:
                # consider the table to be deleted for the new version
                result += " "*table_name_start + "@del({}) ".format(table_name) + "{" + table_name + ".apply();}\n"
                table_version_dict[table_name] = "delete"
                print(table_name, "delete")
                change_type_dict[table_name] = "delete"
                count += 1
                count_delete += 1
            elif choice <= num_mod+num_del+num_add:
                #the "old" part of a modification,
                result += " "*table_name_start + "@mod({}, old) ".format(table_name) + "{" + table_name + ".apply();}\n"
                table_version_dict[table_name] = "change"
                change_type_dict[table_name] = "change"
                count += 2
                count_change += 2
                flag_change = 1
                change_name = table_name
            else:
                result += line
        else:
            result += line
        line = f.readline()
    # stats on number of changes and maximum number of table spike.
    print("\ncount:", count, "add", count_add, "delete", count_delete, "change", count_change)
    print("total usage: ", count_add + count_change//2)
    w.write(result)
    w.close()
    f.close()
    with open("change_type.pickle",'wb') as f:
        pickle.dump(change_type_dict, f)
    return table_version_dict

# generate a txt file with resource usage of each changing components
# in most of our experiments, we assumed each table has equal size.
def generate_resource_txt(args, table_version_dict):
    src = str(args.src)
    w = open("resource-" + src + ".txt", "w")
    result = ""
    for item in table_version_dict:
        if table_version_dict[item] == "add":
            result += "version_{} 0 100\n".format(item)
        elif table_version_dict[item] == "delete":
            result += "version_{} 100 0\n".format(item)
        elif table_version_dict[item] == "change":
            result += "version_{} 100 100\n".format(item)
    result = result[:-1] + " "
    w.write(result)
    w.close()

# instead, we could randomize resource usage.
def generate_resource_txt_random(args, table_version_dict):
    src = str(args.src)
    w = open("resource-" + src + ".txt", "w")
    result = ""
    for item in table_version_dict:
        if table_version_dict[item] == "add":
            result += "version_{} 0 {}\n".format(item, random.randint(50,1000))
        elif table_version_dict[item] == "delete":
            result += "version_{} {} 0\n".format(item, random.randint(50,1000))
        elif table_version_dict[item] == "change":
            result += "version_{} {} {}\n".format(item, random.randint(50,1000), random.randint(50,1000))
    result = result[:-1] + " "
    w.write(result)
    w.close()

def main():
    args = parse_args()
    table_version_dict = select_random_changes(args)
    generate_resource_txt(args, table_version_dict)

if __name__ == "__main__":
    main()
