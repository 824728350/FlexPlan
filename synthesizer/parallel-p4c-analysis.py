import argparse
import os
import subprocess
import argparse
import sys
from subprocess import DEVNULL
import pickle
import multiprocessing
import utils

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    parser.add_argument("--num", help="process number")
    parser.add_argument("--phase", help="phase")
    args = parser.parse_args()
    return args

def check_call(arglist, name):
    print(name, " start!")  
    isExist = os.path.exists("./test_folder_{}/".format(name[:-3]))
    if not isExist:
        os.makedirs("./test_folder_{}/".format(name[:-3]))
    p = subprocess.Popen(["cp", arglist[1], "./test_folder_{}/".format(name[:-3])]) 
    p.wait()
    p = subprocess.Popen(arglist, cwd="./test_folder_{}/".format(name[:-3]))
    p.wait()
    
    #subprocess.check_call(arglist)
    print(name)
    for root, dirs, files in os.walk("./test_folder_{}/".format(name[:-3])):
        if "direct.smt" in files:
            old_name = os.path.join(root, "direct.smt")
            new_name = os.path.join(root, "direct-{}.smt".format(name[:-3]))
            print(old_name, new_name)
            os.rename(old_name, new_name)
    print(name)
    p = subprocess.Popen(["cp", "./test_folder_{}/direct-{}.smt".format(name[:-3], name[:-3]), "."])
    p.wait()
    p = subprocess.Popen(["rm", "-rf", "./test_folder_{}".format(name[:-3])])
    p.wait()

def main():
    pid = os.getpid()
    with open("frontend_pid.pickle",'wb') as f:
        pickle.dump(pid, f)
    arglists = []
    args = parse_args()
    for filename in os.listdir("./"):
        if str(args.src) in filename and "-merge.p4" in filename:
            print(filename)
            arglists.append([['p4c-analysis', './'+filename], filename])
    if str(args.phase) == "background":
        arglists.sort(key=lambda x:int(x[1][utils.find_nth(x[1], "-", -2)+1:utils.find_nth(x[1], "-", -1)]))
    #processes = [multiprocessing.Process(target=check_call, args=arglist) for arglist in arglists]
    pool = multiprocessing.Pool(processes=int(args.num))
    for arglist in arglists:
        print("What?",arglist)
        pool.apply_async(check_call, args=arglist)
    pool.close()
    pool.join()

if __name__ == "__main__":
    main()

