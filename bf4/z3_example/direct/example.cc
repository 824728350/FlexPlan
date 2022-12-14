/*++
Copyright (c) 2015 Microsoft Corporation
--*/

#include<vector>
#include <z3++.h>

using namespace z3;

void demorgan() {
    std::cout << "de-Morgan example\n";
    
    context c;

    expr x = c.bool_const("x");
    expr y = c.bool_const("y");
    expr conjecture = (!(x && y)) == (!x || !y);
    
    solver s(c);
    // adding the negation of the conjecture as a constraint.
    s.add(!conjecture);
    std::cout << s << "\n";
    std::cout << s.to_smt2() << "\n";
    switch (s.check()) {
    case unsat:   std::cout << "de-Morgan is valid\n"; break;
    case sat:     std::cout << "de-Morgan is not valid\n"; break;
    case unknown: std::cout << "unknown\n"; break;
    }
}

void readDumpedFormula() {
    z3::context c;
    std::string testing = "(declare-const p0 Bool)(assert(= p0 true))(assert(= p0 false))(check-sat)";
    Z3_ast_vector parsed = Z3_parse_smtlib2_string(c,testing.c_str(),0,0,0,0,0,0);
    Z3_ast_vector_inc_ref(c, parsed);
    unsigned sz = Z3_ast_vector_size(c, parsed);
    Z3_ast* vv = malloc(sz);
    for (unsigned I = 0; I < sz; ++I) vv[I] = Z3_ast_vector_get(c, parsed, I);
    return;
}

int main() {

    try {
        demorgan(); std::cout << "\n";
	readDumpedFormula(); std::cout << "\n";
    }
    catch (z3::exception & ex) {
        std::cout << "unexpected error: " << ex << "\n";
    }
    return 0;
}
