from collections import defaultdict
import argparse

'''
Expand annotations into version control logic in the p4 program.
We want to control each changing components with a dedicated control variable.
This control variables serve as the basis for CEGIS "sketching holes"
'''
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    args = parser.parse_args()
    return args

def expand_annotations(args):
    src = str(args.src)
    f = open(src+"-clean-anno.p4", "r")
    w = open(src+"-clean-var.p4", "w")
    result = ""
    line = f.readline()
    table_version_dict = defaultdict()

    while line:    
        table_name_start = line.find("@")
        # expand annotations into branches controlled by version header fields (i.e. version variables).
        if "@add" in line: 
            version_variable = line[line.find("@add(") +5 : line.find(")")]
            block_name = line[line.find("{"):]
            # expanding add, this component is executed only when version variable is new.
            result += " "*table_name_start + "if (hdr.version.version_{} == 1w1) ".format(version_variable) + block_name
            table_version_dict[version_variable] = "add"
        elif "@del" in line:
            version_variable = line[line.find("@del(") +5 : line.find(")")]
            block_name = line[line.find("{"):]
            # expanding del, this component is executed only when version variable is old.
            result += " "*table_name_start + "if (hdr.version.version_{} == 1w0) ".format(version_variable) + block_name
            table_version_dict[version_variable] = "delete"
        elif "@mod" in line and "old)" in line:
            version_variable = line[line.find("@mod(") +5 : line.find(", old")]
            block_name = line[line.find("{"):]
            # expanding mod,, this component is executed only when version variable is old.
            result += " "*table_name_start + "if (hdr.version.version_{} == 1w0) ".format(version_variable) + block_name
            table_version_dict[version_variable] = "change"
        elif "@mod" in line and "new)" in line:
            version_variable = line[line.find("@mod(") +5 : line.find(", new")]
            block_name = line[line.find("{"):]
            # expanding mod, this component is executed only when version variable is new.
            result += " "*table_name_start + "if (hdr.version.version_{} == 1w1) ".format(version_variable) + block_name
            table_version_dict[version_variable] = "change"
        else:
            result += line
        line = f.readline()
    w.write(result)
    w.close()
    f.close()
    return table_version_dict

def enforce_changes(args, table_version_dict):
    src = str(args.src)
    f = open(src+"-clean-var.p4", "r")
    w = open(src+"-clean-chg.p4", "w")
    result = ""
    line = f.readline()
    while line:
        # add version variable representation into related header structs
        if "header version_t {" in line:
            result += line
            for item in table_version_dict:
                result += "    bit<1> version_{};\n".format(item)
        elif "struct meta_t" in line:
            result += line
            for item in table_version_dict:
                result += "    bit<32> version_{};\n".format(item)
        elif "struct metadata {" in line:
            temp_index = -1
            while line[0] != "}":
                result += line
                line = f.readline()
                temp_index += 1
            for item in table_version_dict:
                result += "    bit<32>   _meta_version_{}{};\n".format(item, str(temp_index))
                temp_index += 1
            result += line
        else:
            result += line
        line = f.readline()
    w.write(result)
    w.close()
    f.close()

def main():
    args = parse_args()
    table_version_dict = expand_annotations(args)
    enforce_changes(args, table_version_dict)

if __name__ == "__main__":
    main()
