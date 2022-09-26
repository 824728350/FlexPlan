import sys
'''
interpret user specifications and translate into concrete assumptions and assertions.
'''
def interpret(spec_list, spec_assert, metadata_real_list, violation_cond, index_cur, index_old, index_new, mode):
    count_temp = 0
    concatenator = " || "
    violation_cond_old, violation_cond_new = [], []
    for _, entity_assume, entity_assert in spec_list:
        assume_string = ""
        # instrument sepc assumptions into program logic.
        for temp_assume in entity_assume:
            temp_list = temp_assume[0]
            temp_cond = []
            for temp_index in range(len(temp_list)):
                action = temp_list[temp_index]
                # ignore packet level (in)equivalence assumptions.
                if action == "placeholder" or "packet" in action:
                    continue
                # interpret table hit assumption as instrumented logic.
                if "hit__" in action:
                    if "!" in action:
                        action = action[1:] + " == 8w0"
                    else:
                        action += " == 8w1"
                if "sm." in action:
                    action = action.replace("$cur.eg.sm", "sm_{}".format(index_cur))
                    action = action.replace("$old.eg.sm", "sm_{}".format(index_old))
                    action = action.replace("$new.eg.sm", "sm_{}".format(index_new))
                elif ".meta." in action:
                    # special care need to be taken for general metadata
                    if ".eg." in action:
                        var_name_start = action.find(".eg.meta.") + 9
                    elif ".ig." in action:
                        var_name_start = action.find(".ig.meta.") + 9
                    else:
                        continue
                    var_name_end = action.find(" ")
                    var_name = action[var_name_start:var_name_end]
                    name_split = var_name.split(".")
                    target = "_".join(name_split)
                    # iterates metadata_real_list to find the real name of metadata fields.
                    for elem in metadata_real_list:
                        if target in elem:
                            action = action.replace(var_name, elem)
                    action = action.replace("$cur.eg.meta", "metas_{}".format(index_cur))
                    action = action.replace("$old.eg.meta", "metas_{}".format(index_old))
                    action = action.replace("$new.eg.meta", "metas_{}".format(index_new))
                    action = action.replace("$cur.eg.meta", "metas_")
                    action = action.replace("$old.eg.meta", "metas_")
                    action = action.replace("$new.eg.meta", "metas_")
                else:
                    action = action.replace("$cur.eg", "hdrs_{}".format(index_cur))
                    action = action.replace("$old.eg", "hdrs_{}".format(index_old))
                    action = action.replace("$new.eg", "hdrs_{}".format(index_new))
                    action = action.replace("$cur.in", "hdrs_")
                    action = action.replace("$old.in", "hdrs_")
                    action = action.replace("$new.in", "hdrs_")
                temp_cond.append(action)
            if temp_cond == []:
                pass
            elif temp_assume[1] == "and":
                assume_string = "(" + " && ". join(temp_cond) + ") && "
            elif temp_assume[1] == "or":
                assume_string = "(" + " || ". join(temp_cond) + ") && "
            else:
                assume_string = "(" + " ". join(temp_cond) + ") && "
        
        # instrument sepc assertions into program logic.
        for temp_assert in entity_assert:
            temp_list = temp_assert[0]
            temp_cond = []
            if temp_assert[1] == "concat":
                concatenator = temp_assert[0]
                continue
            for temp_index in range(len(temp_list)):
                action = temp_list[temp_index]
                # sawOld and sawNew logic is hard coded. TODO: remove the hard coded logic.
                if "sawNew" in action:
                    action = action.replace("$cur.eg.sawNew", "hdrs_{}.version.sawNew".format(index_cur))
                    #temp_cond.append("hdrs_{}.version.VERSION != 8w0".format(index_cur))
                    #action = action.replace("$cur.eg.sawNew", "hdrs_{}.version.VERSION != 8w0".format(index_cur))
                    #action = "hdrs_{}.version.VERSION != 8w0".format(index_cur)
                    
                elif "sawOld" in action:
                    action = action.replace("$cur.eg.sawOld", "hdrs_{}.version.sawOld".format(index_cur))
                    #temp_cond.append("hdrs_{}.version.VERSION != hdrs_{}.version.LENGTH".format(index_cur, index_cur))
                    #action = action.replace("$cur.eg.sawOld", "hdrs_{}.version.VERSION != hdrs_{}.version.LENGTH".format(index_cur, index_cur))
                    #action = "hdrs_{}.version.VERSION != hdrs_{}.version.LENGTH".format(index_cur, index_cur)
                elif "sm." in action:
                    action = action.replace("$cur.eg.sm", "sm_{}".format(index_cur))
                    action = action.replace("$old.eg.sm", "sm_{}".format(index_old))
                    action = action.replace("$new.eg.sm", "sm_{}".format(index_new))
                elif ".meta." in action:
                    if ".eg." in action:
                        var_name_start = action.find(".eg.meta.") + 9
                    elif ".ig." in action:
                        var_name_start = action.find(".ig.meta.") + 9
                    else:
                        continue
                    var_name_end = action.find(" ")
                    var_name = action[var_name_start:var_name_end]
                    name_split = var_name.split(".")
                    target = "_".join(name_split)
                    for elem in metadata_real_list:
                        if target in elem:
                            action = action.replace(var_name, elem)
                    action = action.replace("$cur.eg.meta", "metas_{}".format(index_cur))
                    action = action.replace("$old.eg.meta", "metas_{}".format(index_old))
                    action = action.replace("$new.eg.meta", "metas_{}".format(index_new))
                else:
                    action = action.replace("$cur.eg", "hdrs_{}".format(index_cur))
                    action = action.replace("$old.eg", "hdrs_{}".format(index_old))
                    action = action.replace("$new.eg", "hdrs_{}".format(index_new))
                    action = action.replace("$cur.in", "hdrs_")
                    action = action.replace("$old.in", "hdrs_")
                    action = action.replace("$new.in", "hdrs_")
                temp_cond.append(action)
            if temp_assert[1] == "and":
                violation_cond.append("(" + assume_string + " && ". join(temp_cond) + ")")
            elif temp_assert[1] == "or":
                violation_cond.append("(" + assume_string + " || ". join(temp_cond) + ")")
            else:
                violation_cond.append("(" + assume_string + " ". join(temp_cond) + ")")
        #determing the way to concatenate assertion definitions.
        if mode == "distill":
            if len(spec_list) == 2 and "||" in spec_assert:
                if count_temp == 0:
                    violation_cond_old = violation_cond
                    violation_cond = []
                elif count_temp == 1:
                    violation_cond_new = violation_cond
                    violation_cond = []
            count_temp += 1
    return violation_cond, violation_cond_old, violation_cond_new, concatenator