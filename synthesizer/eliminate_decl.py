import sys
import os
from collections import defaultdict
import argparse
import pickle

"""
Delete subviolation for program consistency and other properties that requrie global OR operations
"""
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    src = str(args.src)
    fo = open(src, "r")
    line = fo.readline()
    result = ""
    temp_list = []
    while line:
        if "(assert" in line:
            temp = line
            temp_list = [line]
            VERSION = 0
            LENGTH = 0
            SUBVIOLATION = 0
            line = fo.readline()
            while line and "(assert" not in line:
                temp_list.append(line)
                temp += line
                if "VERSION" in line:
                    VERSION += 1
                if "LENGTH" in line:
                    LENGTH += 1
                if "SUBVIOLATION" in line:
                    SUBVIOLATION += 1
                line = fo.readline()
            if not (VERSION >= 1 and LENGTH >= 1 and SUBVIOLATION >= 1):
                result += temp
            else:
                if "old" in src:
                    count = 0
                    for index in range(len(temp_list)-1):
                        if "VERSION" in temp_list[index] and "LENGTH" in temp_list[index+1]:
                            for item in temp_list[index]:
                                if item == "(":
                                    count += 1
                            for item in temp_list[index+1]:
                                if item == ")":
                                    count -= 1
                            temp_list[index] = ""
                            temp_list[index+1] = ""
                            if count > 0:
                                temp_list[index] = "(" * count + "\n"
                            elif count < 0:
                                temp_list[index] = ")" * (-1 * count) + "\n"
                elif "new" in src:
                    count = 0
                    for index in range(len(temp_list)-1):
                        if "VERSION" in temp_list[index] and "#x00" in temp_list[index+1]:
                            for item in temp_list[index]:
                                if item == "(":
                                    count += 1
                            for item in temp_list[index+1]:
                                if item == ")":
                                    count -= 1
                            temp_list[index] = ""
                            temp_list[index+1] = ""
                            if count > 0:
                                temp_list[index] = "(" * count + "\n"
                            elif count < 0:
                                temp_list[index] = ")" * (-1 * count) + "\n"
                result += "".join(temp_list)

            continue
        else:
            result += line
            line = fo.readline()
    fn = open(src[:-4]+"-clean.smt", "w")
    fn.write(result)
    fo.close()
    fn.close()

if __name__ == "__main__":
    main()
