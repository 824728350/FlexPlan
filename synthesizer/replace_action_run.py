from collections import defaultdict
import argparse
import pickle

'''
Instrument ghost variables into p4 logic, make sure we could manage
variable/parameter/register, values, table hits, actions taken etc.
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    parser.add_argument("--mode", help= "test or normal")
    args = parser.parse_args()
    return args

# read information learned from previous passes
def read_pickle():
    try:
        with open("tables.pickle",'rb') as f:
            table_dict = pickle.load(f)
    except:
        table_dict = defaultdict(list)
    try:
        with open("touchdata.pickle",'rb') as f:
            touch_dict = pickle.load(f)
    except:
        touch_dict = defaultdict()
    try:
        with open("ghost_dict.pickle",'rb') as f:
            ghost_dict = pickle.load(f)
    except:
        ghost_dict = defaultdict()
    try:
        with open("instrument_list.pickle",'rb') as f:
            instrument_list = pickle.load(f)
    except:
        instrument_list = defaultdict()
    return table_dict, touch_dict, ghost_dict, instrument_list

def instrument_ghosts():
    args = parse_args()
    table_dict, touch_dict, ghost_dict, instrument_list = read_pickle()
    src = str(args.src)
    mode = str(args.mode)

    f = open(src+"-integrated.p4", "r")
    w = open(src+"-integrated-gho.p4", "w")

    result = ""
    line = f.readline()
    touch_list =[]
    para_dict = defaultdict(defaultdict)
    para_num = 0
    
    read_index = 0
    register_dict = defaultdict()
    while line:
        if "angelic_assert(true)" in line:
            # remove redundancy in the instrumented logic
            line = f.readline()
            continue
        elif "register<bit<" in line and "@name" in line:
            # bulid register_dict where key is register name and value is register width. 
            reg_name_start = line.find('(".') + len('(".')
            reg_name_end = line.find('")')
            reg_size_start = line.find("<bit<") + len("<bit<")
            reg_size_end = line.find(">>")
            reg_name = line[reg_name_start: reg_name_end]
            reg_size = line[reg_size_start: reg_size_end]
            register_dict[reg_name] = reg_size
            result += line
        elif ".read(" in line:
            # deal with register read, make sure we have control interface for register value 
            result += line
            for key in register_dict:
                if key in line[:line.find(".read")]:
                    result += " " * line.find(key) + line[line.find(".read(")+len(".read("): line.find(",")] + " = " + "hdr.version.reg_" + key + ";\n"
            read_index += 1
        elif ".write(" in line:
            result += line
        elif "tmp_" in line and "=" in line and "query_" in line:
            result += line
            key = ""
            # very simple test of ownership, TODO: more principled check
            for key1 in table_dict:
                if key1 in line and len(key1) >= len(key):
                    key = key1
            if key != "":
                # if a table is hit, we set the corresponding hit ghost variable in version header to True.
                # TODO: instead of hard coding the logic, make it part of the spec language.
                if mode == "test":
                    result += " "*line.find("_") + "hdr.version.hit_" + key + " = 8w1;\n"
                    result += " "*line.find("_") + "hdr.version.HITS = hdr.version.HITS + 8w1;\n" 
                elif mode == "normal":
                    for instrument_type, instrument_name, instrument_operartion in instrument_list:
                        if instrument_name == key and instrument_type == "@hit":
                            result += " "*line.find("_") + "hdr.version." + instrument_operartion + ";\n"

        elif ".action_run " in line and "if (" in line and "==" in line and "action_type" in line:
            # make sure we could track which action is taken, or specify which action we want to take.
            line_start = line.find("if ")
            real_key = ""
            temp =""
            for key in table_dict:
                if key in line:
                    for item in table_dict[key]:
                        if item[0] in line:
                            if len(real_key) < len(key):
                                real_key = key
                                temp = item[1]
            if temp != "":
                result += " " * line_start + "if (hdr.version.table_" + real_key + " == 8w" + str(temp) + "){\n"
            else:
                result += line
            line = f.readline()
            continue
        elif "query_instrument_table" in line and "=" in line:
            # instrument changing component touch logic, deprecated.
            result += line
            for key in touch_dict:
                result += "        hdr.version." + key + " = 2w2;\n"
        elif "if (hdr.version.version_" in line and " == 1w" in line:
            # make sure we could track whether certain changing component is touched,
            # also record how many old and new components we have seen on the execution path
            # TODO: instead of hard coding the logic, make it part of the spec language.
            touch_list.append("version.touch_" + line[line.find("version_")+8:line.find("=")-1])
            temp_name0 = "hdr.version.touch_" + line[line.find("version_")+8:line.find("=")-1] + " = 2w0;"
            temp_name0 += "hdr.version.LENGTH = hdr.version.LENGTH + 8w1;"
            if mode == "normal":
                for instrument_type, instrument_name, instrument_operartion in instrument_list:
                    if instrument_type == "@old":
                        temp_name0 += "hdr.version." + instrument_operartion + ";"
            
            temp_name1 = "hdr.version.touch_" + line[line.find("version_")+8:line.find("=")-1] + " = 2w1;"
            temp_name1 += "hdr.version.LENGTH = hdr.version.LENGTH + 8w1;"
            temp_name1 += "hdr.version.VERSION = hdr.version.VERSION + 8w1;"
            if mode == "normal":
                for instrument_type, instrument_name, instrument_operartion in instrument_list:
                    if instrument_type == "@new":
                        temp_name1 += "hdr.version." + instrument_operartion + ";"
            
            if "1w0" in line:
                result += line[:-1] + temp_name0 + "}" + " else {" + temp_name1 + "}\n"
            elif "1w1" in line: 
                result += line[:-1] + temp_name1 + "}" + " else {" + temp_name0 + "}\n"
            result += line
        elif "struct flow_def_" in line:
            # one last thing: the parameter in action also need to be tracked and managed,
            # so this part distill the realtionship between table, actions an parameters
            # and put them in para_dict.
            temp_struct = line[line.find("flow_def_")+len("flow_def_") : line.find(" {")]
            struct_name = ""
            for item in temp_struct:
                if item != " ":
                    struct_name += item
            if struct_name[-2:] == "_0":
                struct_name = struct_name[:-2]
            result += line
            while line[0] != "}":
                line = f.readline()
                if " action_run;" in line:
                    result += line
                    line = f.readline()
                    while "@matchKind" not in line and line[0] != "}":
                        index = line.find(">")
                        for ele in range(index+1, len(line)):
                            if line[ele] != " ":
                                final_index = ele
                                break
                        para_size = line[line.find("<")+1:line.find(">")]
                        para_name =  line[final_index:line.find(";")]
                        para_num += 1
                        para_dict[struct_name][para_name] = para_size
                        result += line
                        line = f.readline()
                    result += line
                else:
                    result += line
        elif  "header version_t {" in line:
            # add the learned action parameter information as version header ghost variables.
            result += line
            for key1 in para_dict:
                for key2 in para_dict[key1]:
                    result += "    bit<" + para_dict[key1][key2] + "> " + "para_" + key1 + "_" + key2 + ";\n"
            if mode == "test":
                for key in table_dict:
                    result += "    bit<8> " + "hit_" + key + ";\n"
            elif mode == "normal":
                for key in ghost_dict:
                    ghost_name, ghost_size, _ = ghost_dict[key]
                    result += "    bit<{}> ".format(ghost_size) + ghost_name + ";\n"
        else:
            result += line
        line = f.readline()

    w.write(result)
    w.close()
    f.close()
    #print("list of touch variables: ", touch_list)
    with open("touchlist.pickle",'wb') as f:
        pickle.dump(touch_list, f)
    with open("paradata.pickle",'wb') as f:
        pickle.dump(para_dict, f)
    #print("parameter number:", para_num)
    return para_dict, register_dict

# an additional pass to make sure we have control over action parameters.
def process_parameters(para_dict, register_dict):
    args = parse_args()
    table_dict, touch_dict, _, _ = read_pickle()
    src = str(args.src)
    f = open(src+"-integrated-gho.p4", "r")
    w = open(src+"-integrated-par.p4", "w")
    line = f.readline()
    result = ""
    para_list = []
    for key in para_dict:
        para_list.append(key)
    para_list.sort(key=lambda x:len(x), reverse=True)
    while line:
        if " query_" in line and "(" in line:
            line = f.readline()
            continue
        elif "header version_t {" in line:
            result += line
            for key in register_dict:
                result += "    bit<{}> reg_{};\n".format(register_dict[key], key)
            line = f.readline()
            continue
        elif " end_" in line and "(" in line:
            line = f.readline()
            continue
        elif "key_match" in line:
            line = f.readline()
            continue
        elif "if" in line and ".hit)"in line:
            stack_size = 1
            line = f.readline()
            while stack_size != 0:
                if "}" in line:
                    stack_size -= 1
                elif "{" in line:
                    stack_size += 1
                line = f.readline()
            continue
        temp_flag = 0
        new_line = ""
        if "bit<" not in line:
            for key1 in para_list:
                if key1 in line:
                    for key2 in para_dict[key1]:
                        if key2 in line:
                            if key1+"_0" in line:
                                new_line = line[:line.find(key1+"_0")] + "hdr.version.para_" + key1 + "_" + key2 + line[line.find(key2)+len(key2):]
                            else:
                                new_line = line[:line.find(key1)] + "hdr.version.para_" + key1 + "_" + key2 + line[line.find(key2)+len(key2):]
                            temp_flag = 1
                    break
        if temp_flag == 1:
            result += new_line
        else:
            result += line
        line = f.readline()
    w.write(result)
    w.close()
    f.close()

def main():
    para_dict, register_dict = instrument_ghosts()
    process_parameters(para_dict, register_dict)

if __name__ == "__main__":
    main()
