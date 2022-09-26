import os
import sys
import pickle
from collections import defaultdict
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--cond", help="condition")
args = parser.parse_args()
cond = str(args.cond)

finished_states = 0
total_states = 0
try:
    with open("state.pickle",'rb') as f:
        assignments = pickle.load(f)
except:
    print("Warning: no transition plan for verification?")
    assignments = defaultdict(list)

temp_list = []
for key in assignments:
    if "#b1" in assignments[key]:
        finished_states += 1
    total_states += 1
#print(total_states, finished_states)

if cond == "fail":
    ft = open("termination", "w")
    ft.write("DEAD!")
    ft.close()
elif cond == "complete":
    ft = open("termination", "w")
    ft.write("ENDED!")
    ft.close()
elif cond == "evaluate" and finished_states == total_states:
    ft = open("termination", "w")
    ft.write("ENDED!")
    ft.close()
else:
    ft = open("termination", "w")
    ft.write("CONTINUE!")
    ft.close()
