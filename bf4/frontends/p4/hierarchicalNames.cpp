/*
Copyright 2017 VMware, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include "hierarchicalNames.h"

#include <boost/algorithm/string.hpp>

namespace P4 {

cstring HierarchicalNames::getName(const IR::IDeclaration* decl) {
    return decl->getName();
}

const IR::Node* HierarchicalNames::postorder(IR::Annotation* annotation) {
    if (annotation->name != IR::Annotation::nameAnnotation)
        return annotation;

    cstring name = IR::Annotation::getName(annotation);
    if (name.startsWith("."))
        return annotation;

    std::vector<std::string> split;
    std::string tosplit(name);
    boost::split(split, tosplit, boost::is_any_of("."));
    // avoid doubling hierarchical name
    // if current name already contains component, don't add it
    if (stack.size() == 1 &&
        std::any_of(split.begin(), split.end(),
                    [this](const cstring& x) { return x == stack.back(); })) {
      return annotation;
    }

    cstring newName = "";
    for (cstring s : stack) {
        newName += s + ".";
    }

    newName += name;
    LOG2("Changing " << name << " to " << newName);
    annotation = new IR::Annotation(annotation->name, { new IR::StringLiteral(newName) });
    return annotation;
}

}  // namespace P4
