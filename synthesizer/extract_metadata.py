from collections import defaultdict

'''
extract metadata names and positions and pass to the frontend.
'''
def extract(f):
    metadata_list = defaultdict()
    metadata_real_list = defaultdict()
    version_list = []
    VIOLATION, CHECK, CURR = "", "", ""
    RESOURCE, DIFF, VIOLATION, TRACK_EGRESS = "", "", "", ""
    line = f.readline()
    while line:
        if "struct metadata {" in line:
            line = f.readline()
            tmp_index = 0
            while line[0] != "}":
                if " _meta_" in line:
                    name_start = line.find(" _meta_") + 7
                    name_end = line.find(";")
                    size_start = line.find("bit<") + 4
                    size_end = line.find(">")
                    name = line[name_start:name_end]
                    size = line[size_start:size_end]
                    metadata_list[name] = [size, 0]
                    metadata_real_list[line[name_start-6:name_end]] = 1
                elif "metadata" in line:
                    name_start = line.find("_")
                    name_end = line.find(";")
                    size_start = line.find("bit<") + 4
                    size_end = line.find(">")
                    name = line[name_start:name_end]
                    size = line[size_start:size_end]
                    metadata_real_list[line[name_start:name_end]] = 1
                else:
                    size_start = line.find("bit<") + 4
                    size_end = line.find(">")
                    temp_index = size_end+1
                    for item in line[size_end+1:]:
                        if item != " ":
                            name_start = temp_index
                            break
                        temp_index += 1
                    name_end = line.find(";")
                    name = line[name_start:name_end]
                    size = line[size_start:size_end]
                    metadata_real_list[line[name_start:name_end]] = 1
                line = f.readline()
                tmp_index += 1
            for key in metadata_list:
                if "VIOLATION" in key and "SUBVIOLATION" not in key:
                    VIOLATION = key
                elif "SUBVIOLATION" in key:
                    SUBVIOLATION = key
                elif "CHECK" in key:
                    CHECK = key
                elif "CURR" in key:
                    CURR = key
                elif "RESOURCE" in key:
                    RESOURCE = key
                elif "DIFF" in key:
                    DIFF = key
                elif "REAL" in key:
                    REAL = key
                elif "TRACK_EGRESS" in key:
                    TRACK_EGRESS = key
                elif "version" in key:
                    version_list.append(key)
        line = f.readline()

    return VIOLATION, SUBVIOLATION, CHECK, CURR, RESOURCE, DIFF, \
           REAL, TRACK_EGRESS, metadata_real_list, version_list