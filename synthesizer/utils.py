import sys
import os
from collections import defaultdict
import argparse
import pickle

def find_nth(haystack, needle, n):
    if n > 0:
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start
    elif n < 0:
        haystack = haystack[::-1]
        n *= -1
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return len(haystack) - start - 1

def reverse_op(temp_list):
    for index in range(len(temp_list)):
        if temp_list[index][0] == "!":
            temp_list[index] = temp_list[index][1:]
        elif "!=" in temp_list[index]:
            position = temp_list[index].find("!=")
            temp_list[index] = temp_list[index][0:position] + "==" + temp_list[index][position+2:]
        elif "==" in temp_list[index]:
            position = temp_list[index].find("==")
            temp_list[index] = temp_list[index][0:position] + "!=" + temp_list[index][position+2:]
        else:
            temp_list[index] = "!" + temp_list[index]
    return temp_list

def grab_hash(line):
    hash_name_flag = 0
    hash_name = ""
    curr_index = 0
    for item in line:
        if item.isnumeric():
            if hash_name_flag == 0:
                start = curr_index
            hash_name_flag = 1
            hash_name += item
        else:
            if hash_name_flag == 1:
                end = curr_index
                break
        curr_index += 1
    return hash_name, start, end

def find_none(haystack, needle):
    for i in range(len(haystack)):
        if haystack[i] != needle:
            return i