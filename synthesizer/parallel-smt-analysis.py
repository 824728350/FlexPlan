import argparse
import os
import sys
import subprocess
import argparse
import time
import sys
from subprocess import DEVNULL
import pickle
import multiprocessing

'''
smt solving in parallel, to generate concrete assignments
'''
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    args = parser.parse_args()
    return args

def main():
    queue = multiprocessing.Queue(maxsize=32)

    def check_call(arglist, name): 
        time_start = time.time()
        log = open('output-'+name[:name.find(".smt")], 'w')
        p = subprocess.Popen(arglist, stdout=log,stderr=log)
        p.wait()
        print(name, time.time()-time_start)
        log = open('output-'+name[:name.find(".smt")], 'r')
        line = log.readline()
        while line:
            if "sat" in line and "unsat" not in line:
                queue.put("sat")
                return
            elif "unsat" in line:
                queue.put("unsat")
                return
            line = log.readline()
        queue.put("error")
        return
        
    arglists = []
    args = parse_args()
    count = 0
    for filename in os.listdir("./"):
        if str(args.src) in filename and ".smt" in filename:
            count += 1
            arglists.append([['z3', './'+filename], filename])

    processes = [multiprocessing.Process(target=check_call, args=arglist) for arglist in arglists]
    for process in processes:
        process.start()

    if count > 0:
        while True:
            result = queue.get()
            count -= 1
            if result == "sat" or count==0:
                for process in processes:
                    process.terminate()
                break

if __name__ == "__main__":
    main()
