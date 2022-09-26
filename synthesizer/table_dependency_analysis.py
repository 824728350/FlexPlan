from collections import defaultdict
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--src", help="source file")
parser.add_argument("--sn", help="start node")
parser.add_argument("--en", help="end node")
args = parser.parse_args()
src = str(args.src)
sn = int(args.sn)
en = int(args.en)

example_list = []
metadata_list = defaultdict()
VIOLATION = ""
TRANSITION = ""
CHECK = ""
version_list = []


def find_nth(haystack, needle, n):
    if n > 0:
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start
    elif n < 0:
        haystack = haystack[::-1]
        n *= -1
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return len(haystack) - start - 1

def main():
    f = open(src+"-clean.p4", "r")
    #print(src+"-init.p4")
    #print(src+"-synthesis.p4")
    result = ""
    line = f.readline()
    maxval = 0 


    table_actions = defaultdict(set)
    table_keys = defaultdict(set)
    meta_dict = defaultdict()
    metadatas = defaultdict(int)
    variables = defaultdict(set)
    headers = defaultdict(set)
    actions_in = defaultdict(set)
    actions_out = defaultdict(set)
    meta_names = set()
    tables = set()
    # get meta_names, headers(header names within each header type, array header considered.), and variables (variable names within each header type)
    while line:
        if "parser ParserImpl" in line:
            while line[0] != "}":
                if "meta." in line and " = " in line:
                    meta_start = line.find("meta.") + 5
                    meta_end = line.find(" = ")
                    meta_name = line[meta_start:meta_end]
                    meta_dict[meta_name] = 1
                line = f.readline()
        if "struct metadata {" in line:
            while line[0] != "}":
                if "bit<" in line:
                    size_start = line.find("<")+1
                    size_end = line.find(">")
                    size = line[size_start:size_end]
                    name_start = line.find("_")
                    name_end = line.find(";")
                    name = line[name_start:name_end]
                    metadatas[name] = size
                    meta_names.add("meta." + name)
                    #print(name,size)
                line = f.readline()

        if "struct headers {" in line:
            line = f.readline()
            while line[0] != "}":
                if "@name" not in line:
                    temp_flag = 0
                    temp_init = 0
                    #print(line)
                    type_end = -1
                    iterations = 0
                    for index in range(len(line)):
                        if line[index].isalnum() and temp_flag == 0 and temp_init == 0:
                            type_start = index
                            type_end = line[index:].find(" ") + index
                            type_name = line[type_start:type_end]
                            if "[" in line and "]" in line:
                                iterations = int(line[line.find("[")+1:line.find("]")])
                                type_name = type_name[:type_name.find("[")]
                            temp_init = 1
                            
                        if index == type_end:
                            temp_flag = 1
                            temp_init = 0
                        if line[index].isalnum() and temp_flag == 1 and temp_init == 0:
                            header_start = index
                            header_end = line[index:].find(";") + index
                            header_name = line[header_start:header_end]
                            if iterations != 0:
                                while iterations > 0:
                                    iterations -= 1
                                    #print(header_name+"["+str(iterations)+"]")
                                    headers[type_name].add(header_name+"["+str(iterations)+"]")
                            else:
                                headers[type_name].add(header_name)
                            #print(type_name, header_name)
                            break
                line = f.readline()
        if line[:6] == "header":
            header_type = line[7:line.find(" {")]
            line = f.readline()
            while line[0] != "}":
                if "bit<" in line:
                    size_start = line.find("<")+1
                    size_end = line.find(">")
                    size = line[size_start:size_end]
                    for index in range(line.find("> "), len(line)):
                        if line[index].isalnum():
                            name_start = index
                            break
                    name_end = line.find(";")
                    name = line[name_start:name_end]
                    variables[header_type].add(name)
                    #print(name,size)
                line = f.readline()
        line = f.readline()

    f.close()
    f = open(src+"-clean.p4", "r")
    line = f.readline()
    variable_names = set()
    validity_names = defaultdict(set)
    #real_validity_names = set()
    isvalid_names = set()
    # get actual variable names, including setValid/setInvalid statements. 
    for header_type in headers:
        for header_name in headers[header_type]:
            for variable_name in variables[header_type]:
                validity_names["hdr." + header_name + ".setInvalid"].add("hdr." + header_name + "." + variable_name)
                validity_names["hdr." + header_name + ".setValid"].add("hdr." + header_name + "." + variable_name)
                isvalid_names.add("hdr." + header_name + ".isValid()")
                variable_names.add("hdr." + header_name + "." + variable_name)

    meta_names.add("standard_metadata.ingress_port")
    meta_names.add("standard_metadata.egress_spec")
    meta_names.add("standard_metadata.egress_port")
    meta_names.add("standard_metadata.clone_spec")
    meta_names.add("standard_metadata.instance_type")
    meta_names.add("standard_metadata.drop")
    meta_names.add("standard_metadata.recirculate_port")
    meta_names.add("standard_metadata.packet_length")
    meta_names.add("standard_metadata.enq_timestamp")
    meta_names.add("standard_metadata.enq_qdepth")
    meta_names.add("standard_metadata.deq_timedelta")
    meta_names.add("standard_metadata.deq_qdepth")
    meta_names.add("standard_metadata.ingress_global_timestamp")
    meta_names.add("standard_metadata.egress_global_timestamp")
    meta_names.add("standard_metadata.lf_field_list")
    meta_names.add("standard_metadata.mcast_grp")
    meta_names.add("standard_metadata.resubmit_flag")
    meta_names.add("standard_metadata.egress_rid")
    meta_names.add("standard_metadata.recirculate_flag")
    meta_names.add("standard_metadata.checksum_error")
    meta_names.add("standard_metadata.priority")
    meta_names.add("standard_metadata.deflection_flag")
    meta_names.add("standard_metadata.deflect_on_drop")
    meta_names.add("standard_metadata.enq_congest_stat")
    meta_names.add("standard_metadata.deq_congest_stat")
    meta_names.add("standard_metadata.mcast_hash")
    meta_names.add("standard_metadata.ingress_cos")
    meta_names.add("standard_metadata.packet_color")
    meta_names.add("standard_metadata.color")

    #print(variable_names)
    #print(meta_names)
    #print(validity_names)

    # get varile dependency within each action. actions_in are variables which the current action dependes on, while actions_out are variables which depends on the current action.
    # the actions/keys within each table are also recorded so that everything is tracable at this point. So that for each table, we know the dependency of all involved variables.
    while line:
        if "@name" in line and " action " in line:
            action_name = line[line.find(' action ') + 8:find_nth(line, '(', 2)]
            line = f.readline()
            while "}" not in line:
                if " = " in line:
                    op_pos = line.find("=")
                    for name in variable_names:
                        if name in line and line.find(name) < op_pos:
                            actions_out[action_name].add(name)
                        elif name in line and line.find(name) > op_pos:
                            actions_in[action_name].add(name)
                    for name in meta_names:
                        if name in line and line.find(name) < op_pos:
                            actions_out[action_name].add(name)
                        elif name in line and line.find(name) > op_pos:
                            actions_in[action_name].add(name) 
                elif "setValid" in line or "setInvalid" in line:
                    for name in validity_names:
                        if name in line:
                            for ele in validity_names[name]:
                                actions_out[action_name].add(ele)
                            temp_name = name[:name.find(".set")] + ".isValid()"
                            actions_out[action_name].add(temp_name)
                
                line = f.readline()

        stack_depth = 0
        if "@name" in line and " table " in line:
            stack_depth += 1
            table_name_start = line.find("table ") + 6
            table_name_end = line.find(" {")
            table_name = line[table_name_start:table_name_end]
            tables.add(table_name)
            while stack_depth != 0:
                line = f.readline()
                if " actions " in line and "{" in line:
                    action_depth = 1
                    temp_index = 0
                    while action_depth != 0:
                        line = f.readline()
                        if "{" in line:
                            action_depth += 1
                        elif "}" in line:
                            action_depth -= 1
                        else:
                            mark = "normal"
                            if "@defaultonly " in line:
                                action_name_start = line.find("@defaultonly ") + 13
                                mark = "default"
                            else:
                                for i in range(len(line)):
                                    if line[i] != " ":
                                        action_name_start = i
                                        break
                            action_name_end = line.find("(")
                            action_name = line[action_name_start:action_name_end] 
                            table_actions[table_name].add(action_name)
                elif "key " in line and "{" in line:
                    #print(line)
                    key_depth = 1
                    temp_index = 0
                    while key_depth != 0:
                        line = f.readline()
                        if "{" in line:
                            key_depth += 1
                        elif "}" in line:
                            key_depth -= 1
                        else:
                            for i in range(len(line)):
                                if line[i] != " ":
                                    key_name_start = i
                                    break
                            for i in range(key_name_start,len(line)):
                                if line[i] == " ":
                                    key_name_end = i
                                    break
                            key_name = line[key_name_start:key_name_end]
                            #print(table_name, key_name)
                            table_keys[table_name].add(key_name)
                elif "{" in line:
                    stack_depth += 1
                elif "}" in line:
                    stack_depth -= 1
        line = f.readline()
    #print(actions_in)
    '''
    for key in actions_out:
        print(key, actions_out[key])
    print(table_actions)
    '''
    #print(table_keys)

    f.close()
    f = open(src+"-clean.p4", "r")
    line = f.readline()
    # now we could try to build dependency graph based on the relationship
    stack = []
    control_stack = []
    nodes = defaultdict()
    data_nodes = defaultdict()
    control_nodes = defaultdict()
    direct_dependencies = defaultdict(set)
    control_dependencies = defaultdict(set)
    data_dependencies = defaultdict(set)
    reverse_direct_dependencies = defaultdict(set)
    ifs = []
    index = 1

    '''
            elif len(curr) == 1 and len(stack) >= 2:
                for item in stack[:-1][::-1]:
                    if len(item) >= 1:
                        #if abs(item[-1]) in direct_dependencies and abs(curr[-1]) in reverse_direct_dependencies:
                            #break
                        direct_dependencies[abs(item[-1])].add(abs(curr[-1]))
                        reverse_direct_dependencies[abs(curr[-1])].add(abs(item[-1]))
                        break
            '''

    def add_dependency(stack):
        if len(stack) >= 1:
            curr = stack[-1]
            if len(curr) > 2:
                #if curr[-2]) in direct_dependencies and abs(curr[-1]) in reverse_direct_dependencies:
                    #return False
                direct_dependencies[abs(curr[-2])].add(abs(curr[-1]))
                reverse_direct_dependencies[abs(curr[-1])].add(abs(curr[-2]))
                data_dependencies[abs(curr[-2])].add(abs(curr[-1]))
            elif len(curr) == 2:
                direct_dependencies[abs(curr[-2])].add(abs(curr[-1]))
                reverse_direct_dependencies[abs(curr[-1])].add(abs(curr[-2]))
                control_dependencies[abs(curr[-2])].add(abs(curr[-1]))
            else:
                pass
                #print("Warning: unexpected stack behavior!", stack)
        else:
            print("Warning: unexpected stack behavior!", stack)


    while line:
        if "control ingress(" in line:
            while True:
                #print(line)
                if "apply {" in line:
                    stack.append([index])
                    nodes[index] = ("ingress")
                    control_stack.append([index])
                    index += 1
                    line = f.readline()
                    while len(stack) != 0:
                        #print(line)
                        
                        # handling if control logic
                        if "if" in line and "{" in line:
                            #stack.append([])
                            elements = set()
                            exam_dicts = [variable_names, isvalid_names, meta_names]
                            for exam in exam_dicts:
                                for key in exam:
                                    if key in line:
                                        elements.add(key)
                            nodes[index] = elements
                            control_nodes[index] = elements
                            stack.append([index])
                            control_stack.append([index])
                            ifs.append(index)
                            add_dependency(control_stack)
                        elif "else" in line and "{" in line:
                            #stack.append([])
                            temp_index = ifs[-1]
                            ifs = ifs[:-1]
                            stack.append([temp_index])
                            control_stack.append([-1*temp_index])
                        elif ".apply();" in line:
                            for key in tables:
                                if key in line:
                                    stack[-1].append(index)
                                    control_stack[-1].append(index)
                                    nodes[index] = key
                                    data_nodes[index] = key
                                    break
                            add_dependency(control_stack)
                        elif "switch (" in line and "action_run" in line and "{" in line:
                            for key in tables:
                                if key in line:
                                    #print(line)
                                    ifs.append(index)
                                    stack.append([index])
                                    control_stack.append([index])
                                    nodes[index] = key
                                    control_nodes[index] = key
                                    data_nodes[index] = key
                                    break
                            add_dependency(control_stack)
                        elif "{" in line:
                            stack.append([index])
                            control_stack.append([index])
                            ifs.append(0)
                        elif "}" in line:
                            #print(len(stack))
                            stack = stack[:-1]
                            if len(control_stack) == 1:
                                control_stack = control_stack[:-1]
                                continue
                            if control_stack[-1][0] > 0:
                                temp_var = control_stack[-1][0]
                                control_stack = control_stack[:-1]
                                control_stack[-1].append(temp_var)
                            else:
                                control_stack = control_stack[:-1]
                            add_dependency(control_stack)
                            #print(len(stack))
                        index += 1
                        #print(stack, ifs)
                        #print(control_stack)
                        line = f.readline()
                    break
                index += 1
                line = f.readline()
            break
        index += 1
        line = f.readline()

    print(nodes)
    #print(direct_dependencies)
    #print(reverse_direct_dependencies)
    print("control_dependencies", control_dependencies)
    print("data_dependencies", data_dependencies)

    def calculate_subblocks(node, lead):
        nodes = [node]
        if lead == 0:
            lead = 1
            for key in control_dependencies[node]:
                nodes += calculate_subblocks(key, lead)
        else:
            for key in control_dependencies[node]:
                nodes += calculate_subblocks(key, lead)
            for key in data_dependencies[node]:
                nodes += calculate_subblocks(key, lead)
        return nodes

    subblocks = defaultdict()

    for node in nodes:
        subblocks[node] = calculate_subblocks(node, 0)

    print("sub blocks: ", subblocks)
        

    def dfs_search_single_table_move(start, end):
        #print(data_dependencies[start])
        if start == end:
            return []
        related_nodes = []
        flag = 0
        for next_node in data_dependencies[start]:
            flag += 1
            #print(next_node, data_dependencies[start])
            related_nodes.append(next_node)
            related_nodes += dfs_search_single_table_move(next_node, end)
        return related_nodes

    #start_node = 4926
    #end_node = 4952
    #start_node = 4926
    #end_node = 5076
    #start_node = 4885
    #end_node = 4926
    start_node = sn
    end_node = en
    related_nodes = dfs_search_single_table_move(start_node, end_node)
    #relate_nodes.append(4926)
    def get_actual_nodes(related_nodes):
        actual_nodes = []
        for node in related_nodes:
            for key in subblocks[node]:
                actual_nodes.append(key)
        return actual_nodes
    passed_nodes = get_actual_nodes(related_nodes)
    tested_nodes = get_actual_nodes([start_node])

    print(related_nodes)
    print(passed_nodes)
    print(tested_nodes)

    def get_in_dependency(node):
        result = set()
        if node not in nodes:
            return result
        if type(nodes[node]) is set:
            for key in nodes[node]:
                result.add(key)
        else:
            for key in table_keys[nodes[node]]:
                result.add(key)
            for act in table_actions[nodes[node]]:
                for ele in actions_in[act]:
                    result.add(ele)
        return result

    def get_out_dependency(node):
        #print(node)
        result = set()
        if node not in nodes:
            return result
        if type(nodes[node]) is set:
            pass
        else:
            for act in table_actions[nodes[node]]:
                for ele in actions_out[act]:
                    result.add(ele)
        return result

    passed_in_dependency = set()
    for node in passed_nodes:
        for key in get_in_dependency(node):
            passed_in_dependency.add(key)

    tested_out_dependency = set()
    for node in tested_nodes:
        for key in get_out_dependency(node):
            tested_out_dependency.add(key)

    passed_out_dependency = set()
    for node in passed_nodes:
        for key in get_out_dependency(node):
            passed_out_dependency.add(key)

    tested_in_dependency = set()
    for node in tested_nodes:
        for key in get_in_dependency(node):
            tested_in_dependency.add(key)

    print(passed_in_dependency)
    print(tested_out_dependency)
    print(passed_out_dependency)
    print(tested_in_dependency)

    print(passed_in_dependency.intersection(tested_out_dependency))
    print(passed_out_dependency.intersection(tested_in_dependency))
    if len(passed_in_dependency.intersection(tested_out_dependency)) == 0 and len(passed_out_dependency.intersection(tested_in_dependency)) == 0:
        print("No conflict detected, safe to move!")
    else:
        print("Potential conflicts!")
        if len(passed_in_dependency.intersection(tested_out_dependency)) != 0:
            print("Nodes below depend on node to be moved!!!", passed_in_dependency.intersection(tested_out_dependency))
        elif len(passed_out_dependency.intersection(tested_in_dependency)) != 0:
            print("After moving, the moved node will depend on nodes above!!!", passed_out_dependency.intersection(tested_in_dependency))
    
    f.close()
    
if __name__ == "__main__":
    main()
