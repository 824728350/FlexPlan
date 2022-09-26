
import argparse
import subprocess

"""
Run e2e FlexPlan experiment: take in a P4 program and user requirement, 
randomly generate some updates (and their resource usage), then synthesis a runtime update plan.
Example: python3 FlexPlan.py --max_seq_len 4 --headroom INF --p4_file p4_programs/switch/p4src/switch.p4 
         --objective maximize --spec_file spec/execution-ipv4-test.spec --p_mod 8 --p_add 8 --p_del 8
"""

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testing", help="testing or real world input?")
    parser.add_argument("--max_seq_len", help="maximum sequence length to try")
    parser.add_argument("--headroom", help="resource headroom")
    parser.add_argument("--p4_file", help="source p4 file")
    parser.add_argument("--objective", help="optimization objective")
    parser.add_argument("--spec_file", help="user requirement file")
    parser.add_argument("--p_mod", help="percetange to randomly modify")
    parser.add_argument("--p_add", help="percetange to randomly add")
    parser.add_argument("--p_del", help="percetange to randomly delete")
    parser.add_argument("--free_var", help="optimization on free var to reduce possible sequence length")

    args = parser.parse_args()
    return args

def execute_cmd(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if process.poll() is not None:
            break
        if output:
            print(output.strip().decode())
    process.wait()
    if (process.returncode):
        print("get a problem when running FlexPlan script! Exit now.")
        exit(1)

def main():
    args = parse_args()
    max_seq_len = int(args.max_seq_len)
    headroom = str(args.headroom)
    objective = str(args.objective)
    p4_file = str(args.p4_file)
    spec_file = str(args.spec_file)
    p_mod = int(args.p_mod)
    p_add = int(args.p_add)
    p_del = int(args.p_del)
    free_var = str(args.free_var)
    testing = str(args.testing)
    if headroom == "INF":
        headroom = 100000
    else: 
        headroom = int(headroom)
    if p4_file.split("/")[-1][-3:] != ".p4":
        print("invalid input!")
        return
    p4_name = p4_file.split("/")[-1][:-3]
    resource_file = "resource-{}.txt".format(p4_name)
    command = "sh cegis.sh {} {} {} {} {} {} {} {} {} {} {} {}" \
              .format(max_seq_len, headroom, objective, p4_file, p4_name, \
              spec_file, resource_file, p_mod, p_add, p_del, free_var, testing)
    execute_cmd(command)

if __name__ == "__main__":
    main()