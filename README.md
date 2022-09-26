# FlexPlan

FlexPlan is a tool that generate update plans for runtime programmable switches.
Its goal is to roll out runtime updates in a way that is both feasible (i.e., stays with available resource headroom), and correct (i.e. does not violate user defined safety/consistency requirements). FlexPlan solves this problem using CEGIS (Counter Example Guided Inductive Synthesis). At a high level, it contains four components:

1. Instrumentation, where the annotated P4 program and user spec are expanded and concatenated together.
2. Frontend translation, where the above logic is converted into z3 SMT formula.
3. Preprocessing, where pre-CEGIS optimizations (e.g. unsat core learning) is applied to reduce the overall search space.
4. Main CEGIS loop, where candidate update plans and counter examples are raised iteratively until a update plan is found or we know there is no possible plans.

## Installation

FlexPlan is currently tested on Ubuntu 16.04 environments with at least 64GB memory. One can reproduce our setup using the provided `VagrantFile`. With this environment, simply clone FlexPlan repo and run `sh do_install.sh` to install all required dependencies.

## Instructions

For end-to-end testing, simply go to the synthesizer folder and run:
```
python3 FlexPlan.py --testing on --max_seq_len 4 --headroom INF --p4_file p4_programs/switch/p4src/switch.p4 --objective maximize --spec_file spec/execution-ipv4-test.spec --p_mod 8 --p_add 8 --p_del 8 --free_var off
```
This test will take in a unmodified P4 program (e.g. switch.p4) and user defined requirements (`spec/#.spec`), then randomly generate some synthetic runtime changes, and find a corresponding update plan. One could simply tune its parameters to change the behavior of FlexPlan:

`--testing [on|off]` controls whether the update is randomly generated for testing or provided by the user.

`--max_seq_len <integer>` controls the longest update sequence FlexPlan will try.

`--headroom [INF|<integer>]` represents the available resource headroom. Using `INF` provides the benefit of early stopping introspection, without sacrificing peak resoure usage if optimization objective is set correctly.

`--p4_file *.p4` is the source (raw/annotated) P4 program.

`--objective [maximize|minimize|off]` is the optimization objective. Maximize will search for the plan with maximum length and lowest resource spike. Use with `--headroom INF` for early stopping introspection.

`--p4_file *.spec` is the user requirements, e.g., execution consistency for ipv4.

`--p_mod/p_add/p_del <integer>` is the percentage of randomly generated modification/addtion/deletion annotations. If `--testing off`, they will be ignored.

`--free_var [on|off]` Extra optimization for early stopping based on the concept of free variables. Not described in the paper.


