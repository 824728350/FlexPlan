import sys
import os
import time
import argparse
import subprocess

'''
Main CEGIS loop. the proposal phase generate candidate update plans,
while the verification phase test against all possible packets and generate
counter examples when violation is detected. The iteration ends when no
candidate plan could be found, or no more violation exists. 
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    parser.add_argument("--length", help="sequence length")
    parser.add_argument("--objective", help="optimization objective")
    parser.add_argument("--constraint", help="resource constraint")
    parser.add_argument("--rounds", help="maximum rounds")
    parser.add_argument("--dsl", help="dsl filename")
    parser.add_argument("--resource", help="resource filename")
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
        #print(process.stderr.readline())
        print("get a problem when executing main CEGIS loop! Exit now.")
        exit(1)

def execute_cmd_tolerate_err(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if process.poll() is not None:
            break
        if output:
            print(output.strip().decode())
    process.wait()

def find_in_file(file, needle):
    f = open(file, "r")
    line = f.readline()
    while line:
        if needle in line:
            return True
        line = f.readline()
    return False

def main():
    args = parse_args()
    src = str(args.src)
    length = int(args.length)
    rounds = int(args.rounds)
    objective = str(args.objective)
    constraint = int(args.constraint)
    dsl = str(args.dsl)
    resource = str(args.resource)
    free_var = str(args.free_var)

    # "round" marks the maximum number of accepted counter examples.
    for index in range(1, rounds+1):
        execute_cmd("rm -rf output")
        print("Concatenate counterexamples...")
        start = time.time()
        # choose optimization objectives, by default we use "maximize", which maximizes 
        # used states (for introspection) and minimizes resource usage (for optmality).
        if objective == "maximize":
            print("maximize intermediate states enabled") 
            execute_cmd("python3 concat_smt.py --orig solve.smt --new synthesis-init.smt --state synthesis \
                        --iter {} --constraint {} --maxsat off --minimize reverse --cause off --incremental off".format(index,constraint))
        elif objective == "minimize":
            print("minimize resource usage enabled!")
            execute_cmd("python3 concat_smt.py --orig solve.smt --new synthesis-init.smt --state synthesis \
                        --iter {} --constraint {} --maxsat off --minimize on --cause off --incremental off".format(index,constraint))
        elif objective == "nomin":
            print("maximize everything enabled!")
            execute_cmd("python3 concat_smt.py --orig solve.smt --new synthesis-init.smt --state synthesis \
                        --iter {} --constraint {} --maxsat off --minimize nomin --cause off --incremental off".format(index,constraint))
        else:
            print("no objectives!")
            execute_cmd("python3 concat_smt.py --orig solve.smt --new synthesis-init.smt --state synthesis \
                        --iter {} --constraint {} --maxsat off --minimize off --cause off --incremental off".format(index,constraint))
        
        # smt solving to generate candidate update plan.
        execute_cmd_tolerate_err("z3 -smt2 solve.smt >output-syn 2>output-syn")
        end=time.time()
        print("synthesis time: {}".format(end-start))
        execute_cmd("cp solve.smt {}-synthesis.smt".format(src))
        
        # if no candidate plan can be found, exit CEGIS loop.
        if find_in_file("output-syn", "unsat"):
            print("Bad run! Could not find a update plan of this size, End CEGIS for this round")
            execute_cmd("python3 termination.py --cond fail")
            break
        
        # extract candidate plan from the smt solving results.
        print("Generating candidate update plan...")
        execute_cmd("python3 extract_plan.py --incremental off --constraint {}".format(constraint))

        # instrumtent candidate plan into verification smt formula, 
        # split the objective into to per-state for incremental verification.
        print("Instrument candidate update plan, get ready for incremental verification...")
        execute_cmd("rm -rf verify-simple*.smt")
        execute_cmd("rm -rf verify-old*.smt")
        execute_cmd("rm -rf verify-new*.smt")
        execute_cmd("python3 incremental_verify.py --src verify-incremental")
        execute_cmd("rm -rf result")
        execute_cmd("rm -rf output-verify-simple*")
        execute_cmd("touch output-fin")

        if find_in_file("output-fin", "FIN"):
            # if we already iterated through all unsat cores, then no need for verification.
            print("No need for verification...")
            execute_cmd("touch output-ready")
            if find_in_file("output-ready", "READY") or free_var == "off":
                execute_cmd("python3 extract_simple.py --type correct")
            else:
                # extract free variables when possible for the seek of introspection.
                execute_cmd("python3 free_extract.py")
                print("Recalculate to count in free variables for faster failure introspection.")
                for len in range(2, length+1):
                    execute_cmd("cp  {}-integrated-par.p4  {}-{}-integrated-par.p4".format(src, src, len))
                    execute_cmd("python3 synthesizer_spec.py  --src {}-{} --constraint {} --total {} --dsl {} --resource {} \
                                --incremental off --marco diagnosis --mode synthesis".format(src,len,constraint,len,dsl,resource))
                    execute_cmd("python3 ingres_egress_merge.py --src {}-{} --suffix synthesis".format(src,len))
                execute_cmd("python3 extract_simple.py --type correct")
                execute_cmd("echo READY > output-ready")
        else:
            # if haven't iterated all unsat cores, invoke verification to generate counter examples
            if find_in_file("output-or", "NOP"):
                execute_cmd("python3 parallel-smt-analysis.py --src verify-simple")
            elif find_in_file("output-or", "OR"):
                # some extra care for spec with definition concatenation.
                k = 0
                while True:
                    k += 1
                    if os.path.exists("verify-simple{}.smt".format(k)):
                        execute_cmd("python3 eliminate_decl.py --src verify-old{}.smt".format(k))
                        execute_cmd("python3 eliminate_decl.py --src verify-new{}.smt".format(k))
                        execute_cmd("rm -rf verify-old{}.smt; rm -rf verify-new{}.smt".format(k))
                    else:
                        break
                execute_cmd("python3 parallel-smt-analysis.py --src verify-old")
                execute_cmd("python3 parallel-smt-analysis.py --src verify-new")
            
            k = 0
            while True:
                k += 1
                execute_cmd("rm -rf output1; rm -rf output2; rm -rf output3; rm -rf output4; rm -rf output")
                execute_cmd("touch output1; touch output2; touch output3; touch output4; touch output")
                if os.path.exists("verify-simple{}.smt".format(k)):
                    print("Verifying next state...")
                else:
                    break

                if find_in_file("output-or", "NOP"):
                    execute_cmd("cp output-verify-simple{} output1".format(k))
                    # examine verifcation result and determine what to do.
                    if find_in_file("output1", "unsat"):
                        print("Verified {}th transition state...".format(k))
                        execute_cmd("python3 extract_simple.py --type correct")
                    elif find_in_file("output1", "sat"):
                        print("Violation found, generating counter example...")
                        execute_cmd("python3 extract_packet.py")
                        execute_cmd("python3 extract_simple.py --type normal")
                        break
                    else:
                        print("End of verification...") 
                        break
                elif find_in_file("output-or", "OR"):
                    # some extra care for spec with definition concatenation.
                    execute_cmd("cp output-verify-old{}-clean output1".format(k))
                    execute_cmd("cp output-verify-new{}-clean output2".format(k))
                    if find_in_file("output1", "unsat") or find_in_file("output2", "unsat"):
                        print("Verified {}th transition state...".format(k))
                        execute_cmd("python3 extract_simple.py --type correct")
                    elif find_in_file("output1", "sat") and find_in_file("output2", "sat"):
                        print("Generating counter example...")
                        execute_cmd("python3 extract_packet.py")
                        execute_cmd("python3 extract_simple.py --type program_consistency")
                        break
                    else:
                        print("End of verification...") 
                        break
               
        execute_cmd("touch result")
        # return the verified update plan, or continue the CEGIS loop.
        if find_in_file("result", "UNSAT"):
            print("No more counterexamples! a valid transition plan has been found")
            execute_cmd("cp plan.pickle state.pickle")
            execute_cmd("python3 termination.py --cond complete")
            execute_cmd("python3 interpret.py --constraint {}".format(constraint))
            break
        elif find_in_file("result", "SAT"):
            print("Counter examples have been found!...")
        else:
            print("Nothing to be verified, there is no plausible transition plan with intermediate states")
            execute_cmd("cp plan.pickle state.pickle")
            execute_cmd("python3 termination.py --cond complete")
            execute_cmd("python3 interpret.py --constraint {}".format(constraint))
            break
    
    # end the CEGIS loop, either a plan is found or no plan exists.
    if find_in_file("termination", "ENDED"):
        print("End of CEGIS! A transition plan has been found!!!")
    if find_in_file("termination", "DEAD"):
        print("End of CEGIS! A transition plan cannot be found!!!")
    if find_in_file("termination", "EXIT"):
        print("End of CEGIS! A transition plan has been found and no need to try longer sequence!")

    
    execute_cmd("cp solve.smt solve_prev.smt")
    execute_cmd("rm -rf plan.pickle")
    execute_cmd("rm -rf state.pickle")
    execute_cmd("rm -rf mapping.pickle")

if __name__ == "__main__":
    main()