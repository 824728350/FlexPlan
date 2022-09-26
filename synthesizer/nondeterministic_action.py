from collections import defaultdict
import argparse
import pickle
import utils

'''
Obtain some of the key information such as variable and metadata name etc,
so that later we could make sure related variables and paramters are non-deterministic. 
'''

def parse_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    src = str(args.src)
    table_dict = defaultdict(list)
    meta_dict = defaultdict()
    metadatas = defaultdict(int)
    touch_dict =  defaultdict()
    version_dict = defaultdict()

    # first pass over p4 program, gathering information
    f = open(src+"-clean-chg.p4", "r")
    result = ""
    line = f.readline()
    while line:
        stack_depth = 0
        if "@name" in line and " table " in line:
            stack_depth += 1
            table_name_start = line.find("table ") + len("table ")
            table_name_end = line.find(" {")
            table_name = line[table_name_start:table_name_end]
            # get a table_dict where key is table and value are actions.
            while stack_depth != 0:
                line = f.readline()
                if " actions " in line and "{" in line:
                    action_depth = 1
                    temp_index = 0
                    while action_depth != 0:
                        line = f.readline()
                        if "{" in line:
                            action_depth += 1
                        elif "}" in line:
                            action_depth -= 1
                        else:
                            if "@defaultonly " in line:
                                action_name_start = line.find("@defaultonly ") + len("@defaultonly ")
                            else:
                                action_name_start = utils.find_none(line, " ")
                            action_name_end = line.find("(") 
                            action_name = line[action_name_start:action_name_end]
                            table_dict[table_name].append([action_name, temp_index])
                            temp_index += 1
                elif "{" in line:
                    stack_depth += 1
                elif "}" in line:
                    stack_depth -= 1
        # get a set that contains metdata data fields used in the parser.
        if "parser ParserImpl" in line:
            while line[0] != "}":
                if "meta." in line and " = " in line:
                    meta_start = line.find("meta.") + 5
                    meta_end = line.find(" = ")
                    meta_name = line[meta_start:meta_end]
                    meta_dict[meta_name] = 1
                line = f.readline()
        # get metadatas where key is metadata field and value is size.
        if "struct metadata {" in line:
            while line[0] != "}":
                if "bit<" in line:
                    size_start = line.find("<")+1
                    size_end = line.find(">")
                    size = line[size_start:size_end]
                    name_start = line.find("_")
                    name_end = line.find(";")
                    name = line[name_start:name_end]
                    metadatas[name] = size
                line = f.readline()
        line = f.readline()
    #print(meta_dict, metadatas)
    f.close()
    
    # second pass over p4 program, add more instrumentations into the version header.
    f = open(src+"-clean-chg.p4", "r")
    w = open(src+"-clean-nde.p4", "w")
    line = f.readline()
    while line:
        result += line
        if "header version_t {" in line:
            # table action representation in the version header.
            for key in table_dict:
                result += "    bit<8> " + "table_" + key + ";\n"
            # make sure we could track and manage the metadata used in the parser.
            for key in meta_dict:
                meta_dict[key] = metadatas[key]
                result += "    bit<" + metadatas[key] + "> " + "meta_" + key + ";\n"
            # variables indicating whether changing component is "touched" on packet execution path.
            while  line[0] != "}":
                line = f.readline()
                if " version_" in line:
                    result += line
                    result += line[:line.find("<")+1] + "2>" + " touch_" + line[line.find("version_") + 8:]
                    result += line[:line.find("<")+1] + "2>" + " TOUCH_" + line[line.find("version_") + 8:]
                    touch_dict["touch_"+ line[line.find("version_") + 8:-2]] = 1
                    version_dict[line[line.find("version_"):-2]] = 1
                else:
                    result += line
        line = f.readline()

    # dump learned information into pickles. TODO: use json instead.
    with open("tables.pickle",'wb') as f:
        pickle.dump(table_dict, f)
    with open("metadata.pickle",'wb') as f:
        pickle.dump(meta_dict, f)
    with open("touchdata.pickle",'wb') as f:
        pickle.dump(touch_dict, f)
    with open("versiondata.pickle",'wb') as f:
        pickle.dump(version_dict, f)
    w.write(result)
    w.close()
    f.close()

if __name__ == "__main__":
    main()
