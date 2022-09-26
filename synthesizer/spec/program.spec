specification {
    // create new ghost variables for the program
    // these are used for verification only
    ghost bit<1> sawOld = 1w0;
    ghost bit<1> sawNew = 1w0;
    // update ghost state when tables are applied
    @old => {sawOld = 1w1;}
    @new => {sawNew = 1w1;}
    // define no path mixes old and new nodes
    // $cur references the current transition state
    define program_all_old = {
        placeholder;
        => 
        !($cur.eg.sawNew == 1w1);
    }
    define program_all_new = {
        placeholder;
        =>
        !($cur.eg.sawOld == 1w1);
    }
    assert program_all_old || program_all_new;
}
