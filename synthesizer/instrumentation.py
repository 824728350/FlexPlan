import sys
import os
from collections import defaultdict
import argparse
import pickle
import utils

'''
Basic instrumentation for input p4 program
'''

def parse_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    args = parser.parse_args()
    return args

# a ghost header "version" need to be added into the p4 logic.
VERSION_HEADER = """

header version_t {
    bit<8>  VERSION;
    bit<8>  LENGTH;
    bit<7>  CONTROL;
    bit<1>  VIOLATION;
    bit<8>  LEFT;
    bit<8>  RIGHT;
    bit<32> MIN;
    bit<32> MAX;
    bit<8>  HITS;
    bit<1>  REMOVE;
}

"""
# a ghost parser state "parse_version" need to be added. 
PARSER_VERSION = """

    @name(".parse_version") state parse_version {
        packet.extract<version_t>(hdr.version);
        transition accept;
    }

"""
def main():
    args = parse_args()
    src = str(args.src)
    f = open(src+"-clean.p4", "r")
    w = open(src+"-clean-init.p4", "w")
    result = ""
    line = f.readline()
    flag_version_header, flag_metadata = 0, 0
    flag_header, flag_parser_version = 0, 0
    curr_num = 0
    while line:
        if line[:6] == "header" and flag_version_header == 0:
            result += VERSION_HEADER
            flag_version_header = 1
        if "struct metadata {" in line and flag_metadata == 0:
            flag_metadata = 1
        elif flag_metadata == 1:
            if "}" not in line:
                temp_num = ""
                for index in range(len(line)-3, 0, -1):
                    if line[index].isnumeric():
                        temp_num = line[index] + temp_num
                    else: break
                curr_num = int(temp_num)
            elif "}" in line:
                print(curr_num)
                # add the following ghost varaibles into metadta struct.
                flag_metadata = 2
                result += "    bit<1>   _meta_VIOLATION{};\n".format(curr_num+1)
                result += "    bit<1>   _meta_SUBVIOLATION{};\n".format(curr_num+2)
                result += "    bit<8>   _meta_TRANSITION{};\n".format(curr_num+3)
                result += "    bit<1>   _meta_CHECK{};\n".format(curr_num+4)
                result += "    bit<8>   _meta_PREV{};\n".format(curr_num+5)
                result += "    bit<8>   _meta_CURR{};\n".format(curr_num+6)
                result += "    bit<32>  _meta_DIFF{};\n".format(curr_num+7)
                result += "    bit<32>  _meta_RESOURCE{};\n".format(curr_num+8)
                result += "    bit<32>  _meta_REAL{};\n".format(curr_num+9)
                result += "    bit<1>   _meta_TRACK_EGRESS{};\n".format(curr_num+10)
                result += "    bit<1>   _meta_TEST_UNSAT_CORE{};\n".format(curr_num+11)
                result += "    bit<8>   _meta_FREE{};\n".format(curr_num+12)
        if "struct headers {" in line and flag_header == 0:
            flag_header = 1
        elif flag_header == 1:
            # add version header into header struct.
            result += "    @name(\".version\")\n"
            result += "    version_t                               version;\n" 
            flag_header = 2
        if line[:6] == "parser" and flag_parser_version == 0:
            flag_parser_version = 1
        elif flag_parser_version == 1:
            flag_parser_version = 2
        elif flag_parser_version == 2:
            if line[0] != "}":
                # make sure all packets go through the parse_version state.
                line = line.replace("accept", "parse_version")
            elif line[0] == "}":
                result += PARSER_VERSION
                flag_parser_version = 3
        result += line
        line = f.readline()
    w.write(result)
    w.close()
    f.close()

if __name__ == "__main__":
    main()
