from collections import defaultdict
import argparse
import pickle
import extract_metadata
import spec_interpret

'''
Instrumentation for free variable detection as well as unsat core learning.
The goal of free variable detection is to predetermine which changing components 
are not related to user specification, so that we could cut unnecessary search
on such components. The goal of unsat core learning is to reduce the amount of 
counter examples needed for the main CEGIS loop, so that we could speed it up. 
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    parser.add_argument("--cat", help="category")
    args = parser.parse_args()
    return args

# load information learned from previous passes
def load_files():
    try:
        with open("state.pickle",'rb') as f:
            plan = pickle.load(f)
    except:
        plan = defaultdict()
    try:
        with open("tables.pickle",'rb') as f:
            table_dict = pickle.load(f)
    except:
        table_dict = defaultdict(list)
    try:
        with open("metadata.pickle",'rb') as f:
            meta_dict = pickle.load(f)
    except:
        meta_dict = defaultdict()
    try:
        with open("touchdata.pickle",'rb') as f:
            touch_dict = pickle.load(f)
    except:
        touch_dict = defaultdict()
    try:
        with open("versiondata.pickle",'rb') as f:
            version_dict = pickle.load(f)
    except:
        version_dict = defaultdict()
    try:
        with open("spec_list.pickle",'rb') as f:
            spec_list = pickle.load(f)
    except:
        spec_list = []
    try:
        with open("spec_assert.pickle",'rb') as f:
            spec_assert = pickle.load(f)
    except:
        spec_assert = []
    try:
        with open("ghost_dict.pickle",'rb') as f:
            ghost_dict = pickle.load(f)
    except:
        ghost_dict = defaultdict()

    return plan, table_dict, meta_dict, touch_dict, version_dict, spec_list, spec_assert, ghost_dict

def main():
    args = parse_args()
    _, table_dict, _, _, version_dict, spec_list, spec_assert, ghost_dict = load_files()
    src, cat = str(args.src), str(args.cat)
    #VIOLATION, CHECK = "", ""

    f = open(src+"-integrated-par.p4", "r")
    # *-dis-init.p4 will be the default logic used for unsat core extraction
    # however, #-dis-old-init.p4 and *-dis-new-init.p4 will be used to handle 
    # definition concatenation, e.g. in program consistency, to make sure that 
    # they do not suffer from scalability issues.
    w = open(src+"-dis-init.p4", "w")
    w_old = open(src+"-dis-old-init.p4", "w")
    w_new = open(src+"-dis-new-init.p4", "w")
    
    result, result_old, result_new = "", "", ""
    line = f.readline()
    #CURR, TRACK_EGRESS = "", ""
    hit_lists = []
    # Check struct metadata to grab the name and position of all metadata.
    VIOLATION, _, CHECK, CURR, _, _, _, TRACK_EGRESS, metadata_real_list, _ = \
    extract_metadata.extract(open(src+"-integrated-par.p4", "r"))

    fa = open("all_metadata.txt", "w")
    while line:
        if "bug();" in line:
            line = f.readline()
            continue
        if "__track_egress_spec" in line and "true" in line:
            result += " " * line.find("__track_egress_spec") +"meta._meta_{} = 1w1;\n".format(str(TRACK_EGRESS))
            line = f.readline()
            continue
        # we need multiple copies of the program to represent different versions/inputs.
        # specifically, we need to represent the "old", "new" and "cur" version of p4 logic
        if "ig.apply(hdrs_, metas_, standard_meta);" in line:
            for index in range(1,5):
                result += "    headers hdrs_{} = hdrs_;\n".format(str(index))
                result += "    metadata metas_{} = metas_;\n".format(str(index))
                result += "    standard_metadata_t sm_{} = standard_meta;\n".format(str(index))
            line = f.readline()
            continue
        # deprecated, we no longer need all these auxiliary tables.
        
        result += line
        result_old += line
        result_new += line
        if "resubmit_flag_0 = standard_meta.resubmit_flag;" in line:
            if cat == "free":
                num_init, num_range = 1, 3
            else:
                num_init, num_range = 2, 5
            # Instrumentation for all initiated p4 logic snapshots.
            # for most standard_metadata fields, initiated them to be 0.
            for index in range(num_init,num_range):
                hit_list = []
                result += "\n    cs_1 = qquery_first_clone_pre(clone_session_1);\n"
                result += "    copy_field_list(metas_, metas_{}, standard_meta, sm_{}, (bit<16>)clone_field_list_1);\n".format(str(index), str(index))
                result += "    sm_{}.egress_port = cs_1.port;\n".format(str(index))
                result += "    sm_{}.resubmit_flag = (bit<32>)32w0;\n".format(str(index))
                result += "    sm_{}.clone_spec = (bit<32>)32w0;\n".format(str(index))
                result += "    sm_{}.recirculate_flag = (bit<32>)32w0;\n".format(str(index))
                result += "    sm_{}.egress_spec = (bit<9>)9w0;\n".format(str(index))
                result += "    sm_{}.egress_port = (bit<9>)9w0;\n".format(str(index))
                result += "    sm_{}.instance_type = PKT_INSTANCE_TYPE_INGRESS_CLONE_0;\n".format(str(index))
                result += "    metas_{}._meta_{} = 1w0;\n".format(str(index), CHECK) 
                result += "    hdrs_{}.version.setValid();\n".format(str(index))
                result += "    hdrs_{}.version.REMOVE = 1w1;\n".format(str(index))

                for key in ghost_dict:
                    ghost_name, _, ghost_init = ghost_dict[key]
                    result += "    hdrs_{}.version.{} = {};\n".format(str(index), ghost_name, ghost_init)

                for key in table_dict:
                    if ("transition_table" in key or "curr_table" in key or \
                        "iteration_table" in key or "violation_table" in key or "instrument_table" in key or "check_table" in key or "_version" in key):
                        result += "    " + "hdrs_{}.version.table_".format(str(index)) + key + " = 8w0;" + "\n"
                # initiate version control variables and corresponding touch variables.
                for key in version_dict:
                    result += "    hdrs_{}.version.{} = {};\n".format(str(index), key, "havoc<bit<1>>()")
                    result += "    hdrs_{}.version.{} = {};\n".format(str(index), "touch_" + key[key.find("version_")+8:], "2w2")
                    if index == 2:
                        result += "    if (hdrs_{}.version.{} == 1w1) ".format(str(index), key) + "{" + "metas_{}._meta_{} = metas_{}._meta_{} + 8w1;".format(str(index), CURR, str(index), CURR) + "}\n"
                    hit_list.append("hdrs_{}.version.".format(str(index)) + "TOUCH_" + key[key.find("version_")+8:] + " != 2w2") 
                
                result += "    ig.apply(hdrs_{}, metas_{}, sm_{});\n".format(str(index),str(index),str(index))
            
                for key in version_dict:
                    result += "    if (hdrs_{}.version.{} != 2w2) ".format(str(index), "touch_" + key[key.find("version_")+8:]) + "{" + "hdrs_{}.version.{} = hdrs_{}.version.{};".format(str(index), "TOUCH_" + key[key.find("version_")+8:], str(index), "touch_" + key[key.find("version_")+8:]) + "}\n"
                    result += " else {" +  "hdrs_{}.version.{} = 2w2;".format(str(index), "TOUCH_" + key[key.find("version_")+8:]) + "}\n"
                
                hit_lists.append(hit_list)
                
            violation_cond, violation_cond_old, violation_cond_new = [], [], []
            assume_cond, free_cond = [], []
            concatenator = " || "
            # merge p4 logic with user specifications.
            violation_cond, violation_cond_old, violation_cond_new, concatenator  = spec_interpret.interpret(spec_list, spec_assert, metadata_real_list, violation_cond, 2, 3, 4, "distill")
            
            # Failure preconditions, need to distinguish free test (free variables) and distill test (unsat cores).
            new_cond, new_cond_free = [], []
            if num_range == 3:
                for key in version_dict:
                    new_cond.append("hdrs_{}.version.{} > 1w0".format(str(2),key))
                    if cat == "free":
                        new_cond_free.append("hdrs_{}.version.{} > 1w0".format(str(1),key))
            else:
                for key in version_dict:
                    # once a component is changed, it cannot go back to the old version.
                    new_cond.append("hdrs_{}.version.{} < hdrs_{}.version.{}".format(str(3),key,str(2),key))
                    new_cond.append("hdrs_{}.version.{} < hdrs_{}.version.{}".format(str(2),key,str(4),key))
                    if cat == "free":
                        new_cond_free.append("hdrs_{}.version.{} < hdrs_{}.version.{}".format(str(3),key,str(1),key))
                        new_cond_free.append("hdrs_{}.version.{} < hdrs_{}.version.{}".format(str(1),key,str(4),key))
            
            # instrument sub-violation node, the instrumentation is different for free varaible detectiion v.s. unsat core learning.
            if cat == "free":
                result += "    if (" + concatenator.join(free_cond) + ") {\n"
                result += "        metas_{}._meta_{} = 1w1;\n".format(str(1), VIOLATION)
                result += "    }\n"
            else:
                if len(spec_list) == 2 and "||" in spec_assert:
                    result_old = result
                    result_new = result
                    # again, we need special care for definition concatenation so that it scales.
                    result_old += "    if (" + concatenator.join(violation_cond_old) + ") {\n"
                    result_old += "        metas_{}._meta_{} = 1w1;\n".format(str(2), VIOLATION)
                    result_old += "    }\n"
                    result_new += "    if (" + concatenator.join(violation_cond_new) + ") {\n"
                    result_new += "        metas_{}._meta_{} = 1w1;\n".format(str(2), VIOLATION)
                    result_new += "    }\n"
                else:
                    result += "    if (" + concatenator.join(violation_cond) + ") {\n"
                    result += "        metas_{}._meta_{} = 1w1;\n".format(str(2), VIOLATION)
                    result += "    }\n"
            index = 1
            
            # make sure the global bug node is triggered by at least one violation
            if cat == "free":
                result += "\n    if (hdrs_{}.version.isValid() && metas_{}._meta_{} == 1w1) {}\n".format(str(1),str(1), VIOLATION, "{")
            else:
                result += "\n    if (hdrs_{}.version.isValid() && metas_{}._meta_{} == 1w1 && metas_{}._meta_{} > 8w0) {}\n".format(str(2),str(2),VIOLATION,str(2),CURR, "{")
                result_old += "\n    if (hdrs_{}.version.isValid() && metas_{}._meta_{} == 1w1 && metas_{}._meta_{} > 8w0) {}\n".format(str(2),str(2),VIOLATION,str(2),CURR, "{")
                result_new += "\n    if (hdrs_{}.version.isValid() && metas_{}._meta_{} == 1w1 && metas_{}._meta_{} > 8w0) {}\n".format(str(2),str(2),VIOLATION,str(2),CURR, "{")
            
            if assume_cond != []:
                result += "      if (" + " && ".join(assume_cond) + ") {\n"

            if cat == "free":
                result += "        if (" + " || ".join(new_cond_free) + ") {\n"
            else:
                result += "        if (" + " || ".join(new_cond) + ") {\n"
                result_old += "        if (" + " || ".join(new_cond) + ") {\n"
                result_new += "        if (" + " || ".join(new_cond) + ") {\n"
            result += "            bug();\n"
            result += "        }\n    }\n\n"
            result_old += "            bug();\n"
            result_old += "        }\n    }\n\n"
            result_new += "            bug();\n"
            result_new += "        }\n    }\n\n"
            
            if assume_cond != []:
                result += "    }\n"

        line = f.readline()

    if len(spec_list) == 1 and "||" not in spec_assert:
        w.write(result)
        w.close()
    elif len(spec_list) == 2 and "||" in spec_assert:
        w_old.write(result_old)
        w_old.close()
        w_new.write(result_new)
        w_new.close()
    else:
        print("Spec behavior currently undefined!")
    f.close()
    fa.close()

    # store the metadata names and positions, TODO: switch to json format.
    with open("metadata_real_list.pickle",'wb') as f:
        pickle.dump(metadata_real_list, f)

if __name__ == "__main__":
    main()
