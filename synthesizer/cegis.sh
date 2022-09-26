#!/bin/sh
export GC_INITIAL_HEAP_SIZE=50G
ulimit -s 256000

sh clean_repo.sh
echo ""
echo "=====================================instrumentation starts====================================="
echo ""
start=`date +%s.%N`
start_total=`date +%s.%N`

if [ "${12}" = "on" ]
then
    # clean and reformat raw p4 code
    python3 clean_p4.py $4 > warnings 2>&1
    # generate basic p4 logic instrumentations
    python3 instrumentation.py --src $5
    # randomly generate update annotations
    python3 random_annotation.py --src $5 --num_mod $8 --num_add $9 --num_del ${10}
else
    cp $4 $5-clean-anno.p4
fi
# expand annotations into version control branches
python3 annotation_expand.py --src $5
# simple frontend parsing for the user specification
python3 parser.py --dsl $6
# extract key table/action information
python3 nondeterministic_action.py --src $5
# calls bf4 for further frontend processing
python3 integrate_p4.py $4
# make sure we have control over all needed values
python3 replace_action_run.py --src $5 --mode normal

end=`date +%s.%N`
runtime1=$( echo "$end - $start" | bc -l )
echo instrumentation time $runtime1
touch termination

echo ""
echo "=====================================frontend starts====================================="
echo ""
start=`date +%s.%N`

# add user requirement into unsat core learning instrumentation
python3 distill_spec.py --src $5 --cat distill
# post processing on ingress and egress logic
python3 ingres_egress_merge.py --src $5-dis --suffix synthesis
python3 ingres_egress_merge.py --src $5-dis-old --suffix synthesis
python3 ingres_egress_merge.py --src $5-dis-new --suffix synthesis

echo "Generating the first formula, for synthesis"
cp  $5-integrated-par.p4  $5-1-integrated-par.p4
# add user requirement into CEGIS proposal phase instrumentation
python3 synthesizer_spec.py  --src $5-1 --constraint $2 --total 1 --dsl $6 --resource $7 --incremental off --marco off --mode synthesis
python3 ingres_egress_merge.py --src $5-1 --suffix synthesis
echo "Generating the second formula, for verification."
cp  $5-integrated-par.p4  $5-ver-integrated-par.p4
# add user requirement into CEGIS verification phase instrumentation
python3 synthesizer_spec.py  --src $5-ver --constraint $2 --total 1 --dsl $6 --resource $7 --incremental off --marco off --mode verify
python3 ingres_egress_merge.py --src $5-ver --suffix verify

# generate smt formula for all the above instrumented programs in parallel.
python3 -u parallel-p4c-analysis.py --src $5 --num 5 --phase init > output-para 2>output-para
rm -rf $5-*merge.p4

if grep Error output-para
then
    echo "Wrong input. Exit FLexPlan..."
fi

# generate larger formula for longer transition sequences. 
for len in `seq 2 $1`
do
    cp  $5-integrated-par.p4  $5-$len-integrated-par.p4
    python3 synthesizer_spec.py  --src $5-$len --constraint $2 --total $len --dsl $6 --resource $7 --incremental off --marco diagnosis --mode synthesis
    python3 ingres_egress_merge.py --src $5-$len --suffix synthesis
done
# generate larger synthesis formula in the background.
nohup python3 -u parallel-p4c-analysis.py --src $5 --num 1 --phase background >output-back 2>output-back &

end=`date +%s.%N`
runtimef=$( echo "$end - $start" | bc -l )
echo frontend time: $runtimef

echo ""
echo "=====================================preprocessing starts====================================="
echo ""
start=`date +%s.%N`
# generate unsat cores before main CEGIS loop
echo "Generating unsat cores."
python3 distill_uc.py --dsl $6 --p4 $4 --id $5 --mode aggregate --period 300 --timeout 5
# If unsat core learning takes too long, move it to the background
nohup python3 -u distill_uc.py --dsl $6 --p4 $4 --id $5 --mode backgound --period 60000 --timeout 600 >output-slow 2>output-slow &

python3 concat_states.py --output verify-incremental.smt --input direct-$5-ver-merge.smt --iter 1 --cause off --incremental off

touch error
if grep ERROR error
then
	echo "VIOLATION could not be triggered at all?"
	exit 1
fi

end=`date +%s.%N`
runtimef=$( echo "$end - $start" | bc -l )
echo frontend time: $runtimef

echo ""
echo "=====================================CEGIS starts====================================="


for i in `seq 1 $1`
do
    echo ""
    echo "Start finding plan with sequence length $i..."
    echo ""
    until test -f direct-$5-$i-merge.smt
    do
        sleep 1
    done
    python3 extract_prev.py --src direct-$5-$i-merge.smt
    if test -f assignments_prev.pickle
    then
        cp assignments_prev.pickle assignments.pickle
        rm -rf assignments_prev.pickle
    fi
    cp direct-$5-$i-merge.smt direct-$5-merge.smt
    python3 concat_states.py --output synthesis-init.smt --input direct-$5-merge.smt --iter 1 --cause off --incremental off
    #python3 reverse_smt.py > error 2>error

    echo "Entering main CEGIS loop."
    python3 cegis_loop.py --src $5 --length $i --objective $3 --constraint $2 --rounds 100 --dsl $6 --resource $7 --free_var ${11}
    
    end_total=`date +%s.%N`
    runtimef=$( echo "$end_total - $start_total" | bc -l )
    echo runtime time so far: $runtimef

    if grep EXIT termination
    then
        break
    fi
done

echo ""
echo "=====================================Get update plan====================================="
echo ""

python3 final_result.py
nohup python3 kill_uc.py >output-kill 2>&1 &

rm -rf termination
rm -rf *instrumented*.p4
rm -rf *notintegrated*.p4
rm -rf *p4i

end_total=`date +%s.%N`
runtime=$( echo "$end_total - $start_total" | bc -l )
echo ""
echo "total completion time: $runtime"
sh clean_repo.sh

