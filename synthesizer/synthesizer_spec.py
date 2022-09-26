from collections import defaultdict
import argparse
import pickle
import extract_metadata
import spec_interpret

'''
Instrumentation for the main synthesis and verification formula. Here is a few assumptions:
1. a resource usage file with per-change resource consumption is provided by the user.
2. if one do not know the available resource headroom, simply set it to a very large number. 
   This works because the tool will always search for a plan with minimum resource spike.
3. when in diagnosis mode, a few optimization will be applied to limit the length of transition sequence.
4. when in incremental mode, the tool will greedily search for the next state rather than an entire plan.
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="source file")
    parser.add_argument("--constraint", help="constraint, available resource headroom")
    parser.add_argument("--total", help="total number of intermediate states")
    parser.add_argument("--dsl", help="dsl, user specification")
    parser.add_argument("--resource", help="resource file")
    parser.add_argument("--incremental", help="incremental mode, on or off?")
    parser.add_argument("--marco", help="marco, diagnosis or not?")
    parser.add_argument("--mode", help="mode, synthesis or verify?")
    args = parser.parse_args()
    return args

def get_files(args):
    # read the resource usage of each changing components into reaource_dict
    resource = str(args.resource)
    fr = open(resource, "r")
    line = fr.readline()
    resource_dict = defaultdict(list)
    while line:
        item = line[:-1].split(" ")
        resource_dict[item[0]] = [item[1], item[2]]
        line = fr.readline()
    fr.close()
    with open("resource_dict.pickle",'wb') as f:
        pickle.dump(resource_dict, f)

    # special treatment for free variables, especially free add and free delete
    free_add_set = set()
    free_del_set = set()
    try:
        with open("constrained_variables.pickle",'rb') as f:
            constrained_variables = pickle.load(f)
            constrained_set = set()
            for key in constrained_variables:
                constrained_set.add("version_" + key[:-2])
            for key in resource_dict:
                if key not in constrained_set and resource_dict[key][0] == "0":
                    free_add_set.add(key)
                elif key not in constrained_set and resource_dict[key][1] == "0":
                    free_del_set.add(key)
    except:
        constrained_set = []

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
        with open("touchdata.pickle",'rb') as f:
            touch_dict = pickle.load(f)
    except:
        touch_dict = defaultdict()

    total_changes = 0
    try:
        with open("versiondata.pickle",'rb') as f:
            version_dict = pickle.load(f)
            for key in version_dict:
                total_changes += 1
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
    
    # whether there is definition concatenation, if yes, mark a special identifier.
    if len(spec_list) == 2 and " || " in spec_assert:
        with open("output-or",'w') as fo:
            fo.write("OR")
    else:
        with open("output-or",'w') as fo:
            fo.write("NOP")

    return resource_dict, constrained_set, free_add_set, free_del_set, plan, table_dict, touch_dict, version_dict, total_changes, spec_list, spec_assert, ghost_dict

def main():
    args = parse_args()
    resource_dict, _, free_add_set, free_del_set, plan, table_dict, \
    _, version_dict, total_changes, spec_list, spec_assert, ghost_dict = get_files(args)
    src = str(args.src)
    constraint = int(args.constraint)
    total = int(args.total)
    incremental = str(args.incremental)
    marco = str(args.marco)
    parse_mode = str(args.mode)
    f = open(src+"-integrated-par.p4", "r")
    w = open(src+"-init.p4", "w")
    result = ""
    line = f.readline()

    # Check struct metadata to grab the name and position of all metadata.
    VIOLATION, SUBVIOLATION, CHECK, CURR, RESOURCE, DIFF, REAL, \
    TRACK_EGRESS, metadata_real_list, version_list = \
    extract_metadata.extract(open(src+"-integrated-par.p4", "r"))

    while line:
        if "bug();" in line:
            line = f.readline()
            continue
        if "__track_egress_spec" in line and "true" in line:
            result += " " * line.find("__track_egress_spec") +"meta._meta_{} = 1w1;\n".format(str(TRACK_EGRESS))
            line = f.readline()
            continue
        if "ig.apply(hdrs_, metas_, standard_meta);" in line:
            for index in range(1,total+3):
                result += "    headers hdrs_{} = hdrs_;\n".format(str(index))
                result += "    metadata metas_{} = metas_;\n".format(str(index))
                result += "    standard_metadata_t sm_{} = standard_meta;\n".format(str(index))
            line = f.readline()
            continue
        
        result += line
        if "resubmit_flag_0 = standard_meta.resubmit_flag;" in line:
            # the initial and the final p4 program (i.e. "old" and "new" version) instrumentation.
            for index in range(total+1, total+3):
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
                result += "    metas_{}._meta_{} = 32w{};\n".format(str(index), REAL, str(constraint))
                result += "    hdrs_{}.version.setValid();\n".format(str(index))
                result += "    hdrs_{}.version.REMOVE = 1w1;\n".format(str(index))
    
                for key in ghost_dict:
                    ghost_name, _, ghost_init = ghost_dict[key]
                    result += "    hdrs_{}.version.{} = {};\n".format(str(index), ghost_name, ghost_init)
                
                for key in table_dict:
                    if ("transition_table" in key or "curr_table" in key or \
                        "iteration_table" in key or "violation_table" in key or "instrument_table" in key or "check_table" in key or "_version" in key):
                        result += "    " + "hdrs_{}.version.table_".format(str(index)) + key + " = 8w0;" + "\n"
                
                for key in version_dict:
                    result += "    hdrs_{}.version.{} = {};\n".format(str(index), key, "havoc<bit<1>>()")
                result += "    ig.apply(hdrs_{}, metas_{}, sm_{});\n".format(str(index),str(index),str(index))
                if parse_mode == "synthesis":
                    for key in resource_dict:
                        for item in version_list:
                            if key in item:
                                result += "    if (hdrs_{}.version.{} == 1w1) ".format(str(index), key) + \
                                          "{" + "metas_{}._meta_{} = metas_{}._meta_{} + 32w{}".format(str(index), RESOURCE, str(index), RESOURCE, resource_dict[key][1]) + \
                                          ";  " + "metas_{}._meta_{} = metas_{}._meta_{} + 8w1; ".format(str(index), CURR, str(index), CURR) + \
                                          "metas_{}._meta_{} = metas_{}._meta_{} + 32w{} - 32w{}; ".format(str(index), REAL, str(index), REAL, resource_dict[key][0], resource_dict[key][1]) + "}\n"
                                break
            # the intermediate states instrumentation.
            for index in range(1,total+1):
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
                result += "    metas_{}._meta_{} = 32w{};\n".format(str(index), REAL, str(constraint))
                result += "    hdrs_{}.version.setValid();\n".format(str(index))
                result += "    hdrs_{}.version.REMOVE = 1w1;\n".format(str(index))

                for key in ghost_dict:
                    ghost_name, _, ghost_init = ghost_dict[key]
                    result += "    hdrs_{}.version.{} = {};\n".format(str(index), ghost_name, ghost_init)

                for key in table_dict:
                    if ("transition_table" in key or "curr_table" in key or \
                        "iteration_table" in key or "violation_table" in key or "instrument_table" in key or "check_table" in key or "_version" in key):
                        result += "    " + "hdrs_{}.version.table_".format(str(index)) + key + " = 8w0;" + "\n"
                for key in plan:
                    if "version.version" in key:
                        name = key
                        value = plan[key][0]
                        size = plan[key][1]
                        if value == 1:
                            result += "    hdrs_{}.{} = {}w{};\n".format(str(index), name, str(size), str(value))
                for key in version_dict:
                    result += "    hdrs_{}.version.{} = {};\n".format(str(index), key, "havoc<bit<1>>()")
                result += "    ig.apply(hdrs_{}, metas_{}, sm_{});\n".format(str(index),str(index),str(index))
                if parse_mode == "synthesis": 
                    for key in resource_dict:
                        for item in version_list:
                            if key in item:
                                result += "    if (hdrs_{}.version.{} == 1w1) ".format(str(index), key) + \
                                          "{" + "metas_{}._meta_{} = metas_{}._meta_{} + 32w{}".format(str(index), RESOURCE, str(index), RESOURCE, resource_dict[key][1]) + \
                                          ";  " + "metas_{}._meta_{} = metas_{}._meta_{} + 8w1;".format(str(index), CURR, str(index), CURR) + \
                                         "metas_{}._meta_{} = metas_{}._meta_{} + 32w{} - 32w{}; ".format(str(index), REAL, str(index), REAL, resource_dict[key][0], resource_dict[key][1]) + "}\n"
                                break

            # diagnosis optimization, get rid of redundant transition states.
            if parse_mode == "synthesis":
                result += "    metas_{}._meta_{} = 32w{};\n".format(str(1), DIFF, str(1000000))
                for index in range(1, total+1):
                    if index == 1:
                        if incremental == "off":
                            result += "    if (metas_{}._meta_{} > metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{}) {}metas_{}._meta_{} = metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{};{}\n" \
                                      .format(str(1), DIFF, str(total+1), REAL, str(index), RESOURCE, str(total + 1), RESOURCE, "{", str(1), DIFF, str(total+1), REAL, str(index), RESOURCE, str(total + 1), RESOURCE, "}")
                    else:
                        result += "    if (metas_{}._meta_{} > metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{}) {}metas_{}._meta_{} = metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{};{}\n" \
                                  .format(str(1), DIFF, str(index-1), REAL, str(index), RESOURCE, str(index-1), RESOURCE, "{", str(1), DIFF, str(index-1), REAL, str(index), RESOURCE, str(index-1), RESOURCE, "}")
                if incremental == "off":
                    result += "    if (metas_{}._meta_{} > metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{}) {}metas_{}._meta_{} = metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{};{}\n" \
                              .format(str(1), DIFF, str(total), REAL, str(total+2), RESOURCE, str(total), RESOURCE, "{", str(1), DIFF, str(total), REAL, str(total+2), RESOURCE, str(total), RESOURCE, "}")

            violation_cond = []
            assume_cond = []
            
            # merge p4 logic with user specifications.
            for index in range(1,total+1):
                violation_cond, _, _, concatenator = spec_interpret.interpret(spec_list, spec_assert, metadata_real_list, violation_cond, index, total+1, total+2, "synthesis")
                result += "\n    if (" + concatenator.join(violation_cond) + ") {\n"
                result += "        metas_{}._meta_{} = 1w1;\n".format(str(index), SUBVIOLATION)
                result += "    }\n"
                violation_cond = []
            violations = ["metas_{}._meta_{} == 1w1".format(str(index), SUBVIOLATION) for index in range(1,total+1)]
            
            curr_cond1, curr_cond2 = [], []
            for index in range(1,total+1):
                if marco == "diagnosis":
                    if index == 2:
                        curr_cond1.append("(metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{} <= metas_{}._meta_{} || metas_{}._meta_{} == 8w{})" \
                                  .format(str(total+1), REAL, str(index), RESOURCE, str(total+1), RESOURCE, str(1), DIFF, str(index), CURR, str(total_changes)))
                    elif index > 2:
                        curr_cond1.append("(metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{} <= metas_{}._meta_{} || metas_{}._meta_{} == 8w{})" \
                                  .format(str(index-2), REAL, str(index), RESOURCE, str(index-2), RESOURCE, str(1), DIFF, str(index), CURR, str(total_changes)))
                
                if index == 1:
                    if incremental == "off":
                        curr_cond1.append("(metas_{}._meta_{} - metas_{}._meta_{} <= metas_{}._meta_{})".format(str(index), RESOURCE,  str(total+1), RESOURCE, str(total+1), REAL))
                        curr_cond2.append("(metas_{}._meta_{} - metas_{}._meta_{} >= 8w{} || metas_{}._meta_{} == 8w{})".format(str(index), CURR, str(total+1), CURR, str(1), str(index), CURR, str(total_changes)))
                    temp_str = []
                    
                    if marco == "diagnosis" or marco == "evaluate":
                        # all free deletions are considered happening in the first transition.
                        for key in free_del_set:
                            curr_cond1.append("hdrs_1.version.{} == 1w1".format(key))
                        temp_cond2 = []
                        # all free additios are considered happening in the last transition.
                        for temp_i in range(1,total+2):
                            temp_cond1 = []
                            for key in free_add_set:
                                if temp_i == 1:
                                    temp_cond1.append("hdrs_{}.version.{} == 1w0".format(str(total+1),key))
                                else:
                                    temp_cond1.append("hdrs_{}.version.{} == 1w0".format(str(temp_i-1),key))
                            if temp_i < total+1:
                                temp_cond1.append("metas_{}._meta_{} == 8w{}".format(str(temp_i), CURR, str(total_changes)))
                            else:
                                temp_cond1.append("metas_{}._meta_{} == 8w{}".format(str(total+2), CURR, str(total_changes)))
                            temp_cond2.append("(" + " && ".join(temp_cond1) + ")")
                        curr_cond1.append("(" + " || ".join(temp_cond2) + ")")
                    # for synthesis formula, make sure there is some progress from one state to the next
                    if parse_mode == "synthesis":
                        temp_str = []
                        for key in version_dict:
                            temp_str.append("(hdrs_{}.version.{} < hdrs_{}.version.{})".format(str(index), key, str(total+1), key))
                        result += "\n    if (" + " || ".join(temp_str) + ") {\n"
                        result += "        metas_{}._meta_{} = 1w1;\n".format(str(1), SUBVIOLATION)
                        result += "    }\n"
                else: 
                    curr_cond1.append("(metas_{}._meta_{} - metas_{}._meta_{} <= metas_{}._meta_{})".format(str(index), RESOURCE,  str(index-1), RESOURCE, str(index-1), REAL))
                    curr_cond2.append("(metas_{}._meta_{} - metas_{}._meta_{} >= 8w{} || metas_{}._meta_{} == 8w{})" \
                              .format(str(index), CURR, str(index-1), CURR, str(1), str(index), CURR, str(total_changes)))
                    # for synthesis formula, make sure there is some progress from one state to the next
                    if parse_mode == "synthesis":
                        temp_str = []
                        for key in version_dict:
                            temp_str.append("(hdrs_{}.version.{} < hdrs_{}.version.{})".format(str(index), key, str(index-1), key))
                        result += "\n    if (" + " || ".join(temp_str) + ") {\n"
                        result += "        metas_{}._meta_{} = 1w1;\n".format(str(1), SUBVIOLATION)
                        result += "    }\n"

            # if incremental mode is on, ignore the resource constraint between current state and final state.
            if incremental == "off":
                curr_cond1.append("(metas_{}._meta_{} - metas_{}._meta_{} <= metas_{}._meta_{})".format(str(total+2), RESOURCE,  str(total), RESOURCE, str(total), REAL))
                curr_cond1.append("(metas_{}._meta_{} >= 32w0)".format(str(total+2), REAL))
                if marco == "diagnosis":
                    curr_cond1.append("(metas_{}._meta_{} - metas_{}._meta_{} + metas_{}._meta_{} <= metas_{}._meta_{} || metas_{}._meta_{} == 8w{})" \
                              .format(str(total-1), REAL, str(total+2), RESOURCE, str(total-1), RESOURCE, str(1), DIFF, str(total+2), CURR, str(total_changes)))
                curr_cond2.append("(metas_{}._meta_{} - metas_{}._meta_{} >= 8w{} || metas_{}._meta_{} == 8w{})" \
                          .format(str(total+2), CURR, str(total), CURR, str(1), str(total+2), CURR, str(total_changes)))
            
            if parse_mode == "synthesis":
                curr_cond1.append("(metas_{}._meta_{} > 32w0)".format(str(1), DIFF))
                temp_str = []
                for key in version_dict:
                    temp_str.append("(hdrs_{}.version.{} < hdrs_{}.version.{})".format(str(total+2), key, str(total), key))
                result += "\n    if (" + " || ".join(temp_str) + ") {\n"
                result += "        metas_{}._meta_{} = 1w1;\n".format(str(1), SUBVIOLATION)
                result += "    }\n"
            
            #result += "\n    if (" + " || ".join(violations) + " || metas_{}._meta_{} > 8w16".format(str(1), FREE) + ") {\n"
            result += "\n    if (" + " || ".join(violations) + ") {\n"
            result += "        metas_{}._meta_{} = 1w1;\n".format(str(1), VIOLATION)
            result += "    }\n"
             
            if assume_cond != []:
                result += "  if (" + " && ".join(assume_cond) + ") {\n"
            
            # distinguish synthesis formula from verification formula.
            if parse_mode == "synthesis":
                result += "\n    if (hdrs_{}.version.isValid() && metas_{}._meta_{} == 1w0) {}\n".format(str(1),str(1),VIOLATION, "{")
                result += "        if (" + " && ".join(curr_cond1) + ") {\n"
                result += "        if (" + " && ".join(curr_cond2) + ") {\n"
                result += "                bug();\n"
                result += "        }\n        }\n    }\n\n"
            elif parse_mode == "verify":
                result += "\n    if (hdrs_{}.version.isValid() && metas_{}._meta_{} == 1w1) {}\n".format(str(1),str(1),VIOLATION, "{")
                result += "                bug();\n"
                result += "    }\n\n"

            if assume_cond != []:
                result += "  }\n"
        line = f.readline()

    w.write(result)
    w.close()
    f.close()

if __name__ == "__main__":
    main()

