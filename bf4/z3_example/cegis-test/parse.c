/*++
Copyright (c) 2015 Microsoft Corporation
--*/

#include<stdio.h>
#include<stdlib.h>
#include<stdarg.h>
#include<memory.h>
#include<setjmp.h>
#include<z3.h>

#define LOG_Z3_CALLS

#ifdef LOG_Z3_CALLS
#define LOG_MSG(msg) Z3_append_log(msg)
#else
#define LOG_MSG(msg) ((void)0)
#endif

/**
   \defgroup capi_ex C API examples
*/
/**@{*/
/**
   @name Auxiliary Functions
*/
/**@{*/

/**
   \brief exit gracefully in case of error.
*/
void exitf(const char* message)
{
  fprintf(stderr,"BUG: %s.\n", message);
  exit(1);
}

/**
   \brief exit if unreachable code was reached.
*/
void unreachable()
{
    exitf("unreachable code was reached");
}

/**
   \brief Simpler error handler.
 */
void error_handler(Z3_context c, Z3_error_code e)
{
    printf("Error code: %d\n", e);
    exitf("incorrect use of Z3");
}

static jmp_buf g_catch_buffer;
/**
   \brief Low tech exceptions.
   In high-level programming languages, an error handler can throw an exception.
*/
void throw_z3_error(Z3_context c, Z3_error_code e)
{
    longjmp(g_catch_buffer, e);
}

/**
   \brief Error handling that depends on checking an error code on the context.
*/

void nothrow_z3_error(Z3_context c, Z3_error_code e) {
    // no-op
}

/**
   \brief Create a logical context.
   Enable model construction. Other configuration parameters can be passed in the cfg variable.
   Also enable tracing to stderr and register custom error handler.
*/
Z3_context mk_context_custom(Z3_config cfg, Z3_error_handler err)
{
    Z3_context ctx;

    Z3_set_param_value(cfg, "model", "true");
    ctx = Z3_mk_context(cfg);
    Z3_set_error_handler(ctx, err);

    return ctx;
}

Z3_solver mk_solver(Z3_context ctx)
{
  Z3_solver s = Z3_mk_solver(ctx);
  Z3_solver_inc_ref(ctx, s);
  return s;
}

void del_solver(Z3_context ctx, Z3_solver s)
{
  Z3_solver_dec_ref(ctx, s);
}

/**
   \brief Create a logical context.
   Enable model construction only.
   Also enable tracing to stderr and register standard error handler.
*/
Z3_context mk_context()
{
    Z3_config  cfg;
    Z3_context ctx;
    cfg = Z3_mk_config();
    ctx = mk_context_custom(cfg, error_handler);
    Z3_del_config(cfg);
    return ctx;
}

/**
   \brief Create a logical context.
   Enable fine-grained proof construction.
   Enable model construction.
   Also enable tracing to stderr and register standard error handler.
*/
Z3_context mk_proof_context() {
    Z3_config cfg = Z3_mk_config();
    Z3_context ctx;
    Z3_set_param_value(cfg, "proof", "true");
    ctx = mk_context_custom(cfg, throw_z3_error);
    Z3_del_config(cfg);
    return ctx;
}

/**
   \brief Create a variable using the given name and type.
*/
Z3_ast mk_var(Z3_context ctx, const char * name, Z3_sort ty)
{
    Z3_symbol   s  = Z3_mk_string_symbol(ctx, name);
    return Z3_mk_const(ctx, s, ty);
}

/**
   \brief Create a boolean variable using the given name.
*/
Z3_ast mk_bool_var(Z3_context ctx, const char * name)
{
    Z3_sort ty = Z3_mk_bool_sort(ctx);
    return mk_var(ctx, name, ty);
}

/**
   \brief Create an integer variable using the given name.
*/
Z3_ast mk_int_var(Z3_context ctx, const char * name)
{
    Z3_sort ty = Z3_mk_int_sort(ctx);
    return mk_var(ctx, name, ty);
}

/**
   \brief Create a Z3 integer node using a C int.
*/
Z3_ast mk_int(Z3_context ctx, int v)
{
    Z3_sort ty = Z3_mk_int_sort(ctx);
    return Z3_mk_int(ctx, v, ty);
}

/**
   \brief Create a real variable using the given name.
*/
Z3_ast mk_real_var(Z3_context ctx, const char * name)
{
    Z3_sort ty = Z3_mk_real_sort(ctx);
    return mk_var(ctx, name, ty);
}

/**
   \brief Create the unary function application: <tt>(f x)</tt>.
*/
Z3_ast mk_unary_app(Z3_context ctx, Z3_func_decl f, Z3_ast x)
{
    Z3_ast args[1] = {x};
    return Z3_mk_app(ctx, f, 1, args);
}

/**
   \brief Create the binary function application: <tt>(f x y)</tt>.
*/
Z3_ast mk_binary_app(Z3_context ctx, Z3_func_decl f, Z3_ast x, Z3_ast y)
{
    Z3_ast args[2] = {x, y};
    return Z3_mk_app(ctx, f, 2, args);
}

/**
   \brief Check whether the logical context is satisfiable, and compare the result with the expected result.
   If the context is satisfiable, then display the model.
*/
void check(Z3_context ctx, Z3_solver s, Z3_lbool expected_result)
{
    Z3_model m      = 0;
    Z3_lbool result = Z3_solver_check(ctx, s);
    switch (result) {
    case Z3_L_FALSE:
        printf("unsat\n");
        break;
    case Z3_L_UNDEF:
        printf("unknown\n");
        m = Z3_solver_get_model(ctx, s);
        if (m) Z3_model_inc_ref(ctx, m);
        printf("potential model:\n%s\n", Z3_model_to_string(ctx, m));
        break;
    case Z3_L_TRUE:
        m = Z3_solver_get_model(ctx, s);
        if (m) Z3_model_inc_ref(ctx, m);
        printf("sat\n%s\n", Z3_model_to_string(ctx, m));
        break;
    }
    if (result != expected_result) {
        exitf("unexpected result");
    }
    if (m) Z3_model_dec_ref(ctx, m);
}

/**
   \brief Prove that the constraints already asserted into the logical
   context implies the given formula.  The result of the proof is
   displayed.
   Z3 is a satisfiability checker. So, one can prove \c f by showing
   that <tt>(not f)</tt> is unsatisfiable.
   The context \c ctx is not modified by this function.
*/
void prove(Z3_context ctx, Z3_solver s, Z3_ast f, bool is_valid)
{
    Z3_model m = 0;
    Z3_ast   not_f;

    /* save the current state of the context */
    Z3_solver_push(ctx, s);

    not_f = Z3_mk_not(ctx, f);
    Z3_solver_assert(ctx, s, not_f);

    switch (Z3_solver_check(ctx, s)) {
    case Z3_L_FALSE:
        /* proved */
        printf("valid\n");
        if (!is_valid) {
            exitf("unexpected result");
        }
        break;
    case Z3_L_UNDEF:
        /* Z3 failed to prove/disprove f. */
        printf("unknown\n");
        m = Z3_solver_get_model(ctx, s);
        if (m != 0) {
            Z3_model_inc_ref(ctx, m);
            /* m should be viewed as a potential counterexample. */
            printf("potential counterexample:\n%s\n", Z3_model_to_string(ctx, m));
        }
        if (is_valid) {
            exitf("unexpected result");
        }
        break;
    case Z3_L_TRUE:
        /* disproved */
        printf("invalid\n");
        m = Z3_solver_get_model(ctx, s);
        if (m) {
            Z3_model_inc_ref(ctx, m);
            /* the model returned by Z3 is a counterexample */
            printf("counterexample:\n%s\n", Z3_model_to_string(ctx, m));
        }
        if (is_valid) {
            exitf("unexpected result");
        }
        break;
    }
    if (m) Z3_model_dec_ref(ctx, m);

    /* restore scope */
    Z3_solver_pop(ctx, s, 1);
}

/**
   \brief Assert the axiom: function f is injective in the i-th argument.
   The following axiom is asserted into the logical context:
   \code
   forall (x_0, ..., x_n) finv(f(x_0, ..., x_i, ..., x_{n-1})) = x_i
   \endcode
   Where, \c finv is a fresh function declaration.
*/
void assert_inj_axiom(Z3_context ctx, Z3_solver s, Z3_func_decl f, unsigned i)
{
    unsigned sz, j;
    Z3_sort finv_domain, finv_range;
    Z3_func_decl finv;
    Z3_sort * types; /* types of the quantified variables */
    Z3_symbol *   names; /* names of the quantified variables */
    Z3_ast * xs;         /* arguments for the application f(x_0, ..., x_i, ..., x_{n-1}) */
    Z3_ast   x_i, fxs, finv_fxs, eq;
    Z3_pattern p;
    Z3_ast   q;
    sz = Z3_get_domain_size(ctx, f);

    if (i >= sz) {
        exitf("failed to create inj axiom");
    }

    /* declare the i-th inverse of f: finv */
    finv_domain = Z3_get_range(ctx, f);
    finv_range  = Z3_get_domain(ctx, f, i);
    finv        = Z3_mk_fresh_func_decl(ctx, "inv", 1, &finv_domain, finv_range);

    /* allocate temporary arrays */
    types       = (Z3_sort *) malloc(sizeof(Z3_sort) * sz);
    names       = (Z3_symbol *) malloc(sizeof(Z3_symbol) * sz);
    xs          = (Z3_ast *) malloc(sizeof(Z3_ast) * sz);

    /* fill types, names and xs */
    for (j = 0; j < sz; j++) { types[j] = Z3_get_domain(ctx, f, j); };
    for (j = 0; j < sz; j++) { names[j] = Z3_mk_int_symbol(ctx, j); };
    for (j = 0; j < sz; j++) { xs[j]    = Z3_mk_bound(ctx, j, types[j]); };

    x_i = xs[i];

    /* create f(x_0, ..., x_i, ..., x_{n-1}) */
    fxs         = Z3_mk_app(ctx, f, sz, xs);

    /* create f_inv(f(x_0, ..., x_i, ..., x_{n-1})) */
    finv_fxs    = mk_unary_app(ctx, finv, fxs);

    /* create finv(f(x_0, ..., x_i, ..., x_{n-1})) = x_i */
    eq          = Z3_mk_eq(ctx, finv_fxs, x_i);

    /* use f(x_0, ..., x_i, ..., x_{n-1}) as the pattern for the quantifier */
    p           = Z3_mk_pattern(ctx, 1, &fxs);
    printf("pattern: %s\n", Z3_pattern_to_string(ctx, p));
    printf("\n");

    /* create & assert quantifier */
    q           = Z3_mk_forall(ctx,
                                 0, /* using default weight */
                                 1, /* number of patterns */
                                 &p, /* address of the "array" of patterns */
                                 sz, /* number of quantified variables */
                                 types,
                                 names,
                                 eq);
    printf("assert axiom:\n%s\n", Z3_ast_to_string(ctx, q));
    Z3_solver_assert(ctx, s, q);

    /* free temporary arrays */
    free(types);
    free(names);
    free(xs);
}

/**
   \brief Assert the axiom: function f is commutative.
   This example uses the SMT-LIB parser to simplify the axiom construction.
*/
void assert_comm_axiom(Z3_context ctx, Z3_solver s, Z3_func_decl f)
{
    Z3_sort t;
    Z3_symbol f_name, t_name;
    Z3_ast_vector q;
    unsigned i;

    t = Z3_get_range(ctx, f);

    if (Z3_get_domain_size(ctx, f) != 2 ||
        Z3_get_domain(ctx, f, 0) != t ||
        Z3_get_domain(ctx, f, 1) != t) {
        exitf("function must be binary, and argument types must be equal to return type");
    }

    /* Inside the parser, function f will be referenced using the symbol 'f'. */
    f_name = Z3_mk_string_symbol(ctx, "f");

    /* Inside the parser, type t will be referenced using the symbol 'T'. */
    t_name = Z3_mk_string_symbol(ctx, "T");

    q = Z3_parse_smtlib2_string(ctx,
                           "(assert (forall ((x T) (y T)) (= (f x y) (f y x))))",
                           1, &t_name, &t,
                           1, &f_name, &f);
    printf("assert axiom:\n%s\n", Z3_ast_vector_to_string(ctx, q));
    for (i = 0; i < Z3_ast_vector_size(ctx, q); ++i) {
        Z3_solver_assert(ctx, s, Z3_ast_vector_get(ctx, q, i));
    }
}

/**
   \brief Z3 does not support explicitly tuple updates. They can be easily implemented
   as macros. The argument \c t must have tuple type.
   A tuple update is a new tuple where field \c i has value \c new_val, and all
   other fields have the value of the respective field of \c t.
   <tt>update(t, i, new_val)</tt> is equivalent to
   <tt>mk_tuple(proj_0(t), ..., new_val, ..., proj_n(t))</tt>
*/
Z3_ast mk_tuple_update(Z3_context c, Z3_ast t, unsigned i, Z3_ast new_val)
{
    Z3_sort         ty;
    Z3_func_decl   mk_tuple_decl;
    unsigned            num_fields, j;
    Z3_ast *            new_fields;
    Z3_ast              result;

    ty = Z3_get_sort(c, t);

    if (Z3_get_sort_kind(c, ty) != Z3_DATATYPE_SORT) {
        exitf("argument must be a tuple");
    }

    num_fields = Z3_get_tuple_sort_num_fields(c, ty);

    if (i >= num_fields) {
        exitf("invalid tuple update, index is too big");
    }

    new_fields = (Z3_ast*) malloc(sizeof(Z3_ast) * num_fields);
    for (j = 0; j < num_fields; j++) {
        if (i == j) {
            /* use new_val at position i */
            new_fields[j] = new_val;
        }
        else {
            /* use field j of t */
            Z3_func_decl proj_decl = Z3_get_tuple_sort_field_decl(c, ty, j);
            new_fields[j] = mk_unary_app(c, proj_decl, t);
        }
    }
    mk_tuple_decl = Z3_get_tuple_sort_mk_decl(c, ty);
    result = Z3_mk_app(c, mk_tuple_decl, num_fields, new_fields);
    free(new_fields);
    return result;
}

/**
   \brief Display a symbol in the given output stream.
*/
void display_symbol(Z3_context c, FILE * out, Z3_symbol s)
{
    switch (Z3_get_symbol_kind(c, s)) {
    case Z3_INT_SYMBOL:
        fprintf(out, "#%d", Z3_get_symbol_int(c, s));
        break;
    case Z3_STRING_SYMBOL:
        fprintf(out, "%s", Z3_get_symbol_string(c, s));
        break;
    default:
        unreachable();
    }
}

/**
   \brief Display the given type.
*/
void display_sort(Z3_context c, FILE * out, Z3_sort ty)
{
    switch (Z3_get_sort_kind(c, ty)) {
    case Z3_UNINTERPRETED_SORT:
        display_symbol(c, out, Z3_get_sort_name(c, ty));
        break;
    case Z3_BOOL_SORT:
        fprintf(out, "bool");
        break;
    case Z3_INT_SORT:
        fprintf(out, "int");
        break;
    case Z3_REAL_SORT:
        fprintf(out, "real");
        break;
    case Z3_BV_SORT:
        fprintf(out, "bv%d", Z3_get_bv_sort_size(c, ty));
        break;
    case Z3_ARRAY_SORT:
        fprintf(out, "[");
        display_sort(c, out, Z3_get_array_sort_domain(c, ty));
        fprintf(out, "->");
        display_sort(c, out, Z3_get_array_sort_range(c, ty));
        fprintf(out, "]");
        break;
    case Z3_DATATYPE_SORT:
        if (Z3_get_datatype_sort_num_constructors(c, ty) != 1)
        {
            fprintf(out, "%s", Z3_sort_to_string(c,ty));
            break;
        }
        {
            unsigned num_fields = Z3_get_tuple_sort_num_fields(c, ty);
            unsigned i;
            fprintf(out, "(");
            for (i = 0; i < num_fields; i++) {
                Z3_func_decl field = Z3_get_tuple_sort_field_decl(c, ty, i);
                if (i > 0) {
                    fprintf(out, ", ");
                }
                display_sort(c, out, Z3_get_range(c, field));
            }
            fprintf(out, ")");
            break;
        }
    default:
        fprintf(out, "unknown[");
        display_symbol(c, out, Z3_get_sort_name(c, ty));
        fprintf(out, "]");
        break;
    }
}

/**
   \brief Custom ast pretty printer.
   This function demonstrates how to use the API to navigate terms.
*/
void display_ast(Z3_context c, FILE * out, Z3_ast v)
{
    switch (Z3_get_ast_kind(c, v)) {
    case Z3_NUMERAL_AST: {
        Z3_sort t;
        fprintf(out, "%s", Z3_get_numeral_string(c, v));
        t = Z3_get_sort(c, v);
        fprintf(out, ":");
        display_sort(c, out, t);
        break;
    }
    case Z3_APP_AST: {
        unsigned i;
        Z3_app app = Z3_to_app(c, v);
        unsigned num_fields = Z3_get_app_num_args(c, app);
        Z3_func_decl d = Z3_get_app_decl(c, app);
        fprintf(out, "%s", Z3_func_decl_to_string(c, d));
        if (num_fields > 0) {
            fprintf(out, "[");
            for (i = 0; i < num_fields; i++) {
                if (i > 0) {
                    fprintf(out, ", ");
                }
                display_ast(c, out, Z3_get_app_arg(c, app, i));
            }
            fprintf(out, "]");
        }
        break;
    }
    case Z3_QUANTIFIER_AST: {
        fprintf(out, "quantifier");
        ;
    }
    default:
        fprintf(out, "#unknown");
    }
}

/**
   \brief Custom function interpretations pretty printer.
*/
void display_function_interpretations(Z3_context c, FILE * out, Z3_model m)
{
    unsigned num_functions, i;

    fprintf(out, "function interpretations:\n");

    num_functions = Z3_model_get_num_funcs(c, m);
    for (i = 0; i < num_functions; i++) {
        Z3_func_decl fdecl;
        Z3_symbol name;
        Z3_ast func_else;
        unsigned num_entries = 0, j;
        Z3_func_interp_opt finterp;

        fdecl = Z3_model_get_func_decl(c, m, i);
        finterp = Z3_model_get_func_interp(c, m, fdecl);
        Z3_func_interp_inc_ref(c, finterp);
        name = Z3_get_decl_name(c, fdecl);
        display_symbol(c, out, name);
        fprintf(out, " = {");
        if (finterp)
          num_entries = Z3_func_interp_get_num_entries(c, finterp);
        for (j = 0; j < num_entries; j++) {
            unsigned num_args, k;
            Z3_func_entry fentry = Z3_func_interp_get_entry(c, finterp, j);
            Z3_func_entry_inc_ref(c, fentry);
            if (j > 0) {
                fprintf(out, ", ");
            }
            num_args = Z3_func_entry_get_num_args(c, fentry);
            fprintf(out, "(");
            for (k = 0; k < num_args; k++) {
                if (k > 0) {
                    fprintf(out, ", ");
                }
                display_ast(c, out, Z3_func_entry_get_arg(c, fentry, k));
            }
            fprintf(out, "|->");
            display_ast(c, out, Z3_func_entry_get_value(c, fentry));
            fprintf(out, ")");
            Z3_func_entry_dec_ref(c, fentry);
        }
        if (num_entries > 0) {
            fprintf(out, ", ");
        }
        fprintf(out, "(else|->");
        func_else = Z3_func_interp_get_else(c, finterp);
        display_ast(c, out, func_else);
        fprintf(out, ")}\n");
        Z3_func_interp_dec_ref(c, finterp);
    }
}

/**
   \brief Custom model pretty printer.
*/
void display_model(Z3_context c, FILE * out, Z3_model m)
{
    unsigned num_constants;
    unsigned i;

    if (!m) return;

    num_constants = Z3_model_get_num_consts(c, m);
    for (i = 0; i < num_constants; i++) {
        Z3_symbol name;
        Z3_func_decl cnst = Z3_model_get_const_decl(c, m, i);
        Z3_ast a, v;
        bool ok;
        name = Z3_get_decl_name(c, cnst);
        display_symbol(c, out, name);
        fprintf(out, " = ");
        a = Z3_mk_app(c, cnst, 0, 0);
        v = a;
        ok = Z3_model_eval(c, m, a, 1, &v);
        (void)ok;
        display_ast(c, out, v);
        fprintf(out, "\n");
    }
    display_function_interpretations(c, out, m);
}

/**
   \brief Similar to #check, but uses #display_model instead of #Z3_model_to_string.
*/
void check2(Z3_context ctx, Z3_solver s, Z3_lbool expected_result)
{
    Z3_model m      = 0;
    Z3_lbool result = Z3_solver_check(ctx, s);
    switch (result) {
    case Z3_L_FALSE:
        printf("unsat\n");
        break;
    case Z3_L_UNDEF:
        printf("unknown\n");
        printf("potential model:\n");
        m = Z3_solver_get_model(ctx, s);
        if (m) Z3_model_inc_ref(ctx, m);
        display_model(ctx, stdout, m);
        break;
    case Z3_L_TRUE:
        printf("sat\n");
        m = Z3_solver_get_model(ctx, s);
        if (m) Z3_model_inc_ref(ctx, m);
        display_model(ctx, stdout, m);
        break;
    }
    if (result != expected_result) {
        exitf("unexpected result");
    }
    if (m) Z3_model_dec_ref(ctx, m);

}

/**
   \brief Display Z3 version in the standard output.
*/
void display_version()
{
    unsigned major, minor, build, revision;
    Z3_get_version(&major, &minor, &build, &revision);
    printf("Z3 %d.%d.%d.%d\n", major, minor, build, revision);
}

void parser_smt()
{
    Z3_context ctx = mk_context();
    Z3_solver s = mk_solver(ctx);
    Z3_ast x, y;
    Z3_symbol         names[2];
    Z3_func_decl decls[2];
    Z3_ast_vector f;
    unsigned i;

    printf("\nparser_smt\n");
    LOG_MSG("parser_smt");


    /* Z3_enable_arithmetic doesn't need to be invoked in this example
       because it will be implicitly invoked by mk_int_var.
    */

    f = Z3_parse_smtlib2_file(ctx, "direct.smt", 0, 0, 0, 0, 0, 0);
    printf("formula: %s\n", Z3_ast_vector_to_string(ctx, f));
    printf("assert axiom:\n%s\n", Z3_ast_vector_to_string(ctx, f));
    for (i = 0; i < Z3_ast_vector_size(ctx, f); ++i) {
        Z3_solver_assert(ctx, s, Z3_ast_vector_get(ctx, f, i));
    }
    check(ctx, s, Z3_L_TRUE);

    del_solver(ctx, s);
    Z3_del_context(ctx);
}

int main() {
#ifdef LOG_Z3_CALLS
    Z3_open_log("z3.log");
#endif
    parser_smt();
    return 0;
}

