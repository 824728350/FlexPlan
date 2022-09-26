from collections import defaultdict
import argparse
import pickle
import utils

'''
A simple parser for the specification dsl. Should support program/execution/field consistency 
and other safety properties. Currently we do not support nested AND/OR operations, and for the 
concatenation between different "define" declaration, we only support single OR operations which
may need to be extended to cover more advaced user requirements.
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsl", help="dsl file")
    args = parser.parse_args()
    return args

# parse a define declaration, including its assumptions and assertions.
def parse_entity(entity):
    entity_name = ""
    entity_assume = []
    entity_assert = []
    flag = 2
    for line in entity:
        if "{" in line and "define" in line:
            entity_name = line.strip(" ={\n")
            entity_name = entity_name.split(" ")[1]
            flag = 0
        elif flag == 0:
            if "=>" in line:
                flag = 1
            elif ";" not in line:
                continue
            else:
                # for assumption, directly add in the dsl logic.
                string = line.strip(" ;\n")
                if "||" in string and "&&" in string:
                    print("ignore complex expression for now...")
                    raise ValueError
                elif "||" in string:
                    entity_assume.append([string.split(" || "), "or"])
                elif "&&" in string:
                    entity_assume.append([string.split(" && "), "and"])
                else:
                    entity_assume.append([[string], "unary"])
        elif flag == 1:
            # for assertion, we need to reverse the logic so that we could find violations later
            if ";" not in line or "}" in line:
                # to handle nested AND/OR operations: we support assertion in the form of
                # "(a && b) || (c && d)", l2/l3 field consistency contains such an example.
                if "||" in line:
                    entity_assert.append([" && ", "concat"])
                elif "&&" in line:
                    entity_assert.append([" || ", "concat"])
                else:
                    continue
            elif "!(" in line:
                string = line.strip(" !;\n")
                string = string[1:-1]
                if "&&" in string and "||" in string:
                    print("ignore complex expression for now...")
                    raise ValueError
                if "&&" in string:
                    entity_assert.append([string.split(" && "), "and"])
                elif "||" in string:
                    entity_assert.append([string.split(" || "), "or"])
                else:
                    entity_assert.append([[string], "unary"])
            else:
                string = line.strip(" ;\n")
                #print(string)
                if "&&" in string and "||" in string:
                    print("ignore complex expression for now...")
                    raise ValueError
                elif "&&" in string:
                    temp_list = string.split(" && ")
                    reversed_list = utils.reverse_op(temp_list)
                    entity_assert.append([reversed_list, "or"])
                elif "||" in string:
                    temp_list = string.split(" || ")
                    reversed_list = utils.reverse_op(temp_list)
                    entity_assert.append([reversed_list, "and"])
                else:
                    temp_list = [string]
                    reversed_list = utils.reverse_op(temp_list)
                    entity_assert.append([reversed_list, "unary"])
    return entity_name, entity_assume, entity_assert

# TODO: more supports for concatenation between different assertion declarations
def parse_assert(line):
    strip_line = line.strip(" ;\n")
    string = strip_line[strip_line.find("assert ")+7:]
    if "&&" in string:
        print("ignore complex expression for now...")
        raise ValueError
    return string

# parse ghost variable definitions, including name, size and init value.
def parse_definitions(line):
    ghost_var_name_start = line.find("> ") + 2
    ghost_var_name_end = line.find(" = ")
    ghost_var_name = line[ghost_var_name_start: ghost_var_name_end]
    ghost_var_size_start = line.find("bit<") + 4
    ghost_var_size_end = line.find(">")
    ghost_var_size = line[ghost_var_size_start: ghost_var_size_end]
    ghost_var_init_start = line.find("= ") + 2
    ghost_var_init_end = line.find(";")
    ghost_var_init = line[ghost_var_init_start: ghost_var_init_end]
    #print(ghost_var_name, ghost_var_size, ghost_var_init)
    return [ghost_var_name, ghost_var_size, ghost_var_init]

# parse ghost variable assignment, including type, position and operation.
def parse_instrumentation(line): 
    instrument_operation_start = line.find("{") + 1
    instrument_operation_end = line.find(";}") 
    instrument_operation = line[instrument_operation_start: instrument_operation_end]
    if "@old" in line:
        instrument_type = "@old"
        instrument_position = "global"
    elif "@new" in line:
        instrument_type = "@new"
        instrument_position = "global"
    elif "@hit" in line:
        instrument_type = "@hit"
        instrument_position_start = line.find("@hit(") + 5
        instrument_position_end = line.find(")")
        instrument_position = line[instrument_position_start: instrument_position_end]
    elif "@" in line:
        print("ignore complex expression for now...")
        raise ValueError
    #print(instrument_type, instrument_position, instrument_operation)
    return instrument_type, instrument_position, instrument_operation

    
def main():
    args = parse_args()
    f = open(str(args.dsl), "r")
    line = f.readline()
    spec_list, ghost_dict = [], defaultdict()
    instrument_list = []
    # ignore comments and split between assertion definition and concatenation.
    while line:
        if "//" in line:
            pass
        elif "{" in line and "specification " not in line and "define" in line:
            entity = [line]
            while "}" not in line:
                line = f.readline()
                if "//" not in line:
                    entity.append(line)
            spec_list.append(parse_entity(entity))
        elif " assert " in line:
            spec_assert = parse_assert(line)
        elif "ghost" in line:
            ghost_var = parse_definitions(line)
            ghost_dict[ghost_var[0]] = ghost_var
        elif "@new" in line or "@old" in line or "@hit" in line:
            instrumentation = parse_instrumentation(line)
            instrument_list.append(instrumentation)
        line = f.readline()

    with open("spec_list.pickle",'wb') as f:
        pickle.dump(spec_list, f)
        #print(spec_list)
    with open("spec_assert.pickle",'wb') as f:
        pickle.dump(spec_assert, f)
    with open("ghost_dict.pickle",'wb') as f:
        pickle.dump(ghost_dict, f)
    with open("instrument_list.pickle",'wb') as f:
        pickle.dump(instrument_list, f)
            
if __name__ == "__main__":
    main()
