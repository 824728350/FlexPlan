from collections import defaultdict
from subprocess import STDOUT, check_output
import subprocess
import pickle

'''
kill backend processes when necessary
'''
def main():
    try:
        with open("uc_pid.pickle",'rb') as f:
            pid = pickle.load(f)
            solver = "sudo kill " + str(pid)
            print("Kill uc pid: ", str(pid))
            process = subprocess.Popen(solver, shell=True, stdout=subprocess.PIPE)
            process.wait()
    except:
        print("No running uc pid!")

    try:
        with open("frontend_pid.pickle",'rb') as f:
            pid = pickle.load(f)
            solver = "sudo kill " + str(pid)
            print("Kill frontend pid: ", str(pid))
            process = subprocess.Popen(solver, shell=True, stdout=subprocess.PIPE)
            process.wait()
    except:
        print("No running frontend pid!")

if __name__ == "__main__":
    main()