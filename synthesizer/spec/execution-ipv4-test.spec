specification {
    // create new ghost variables for the program
    // these are used for verification only
    ghost bit<1> sawOld = 1w0;
    ghost bit<1> sawNew = 1w0;
    ghost bit<8> hit__ip_acl = 8w0;
    ghost bit<8> hit__fabric_ingress_dst_lkp_0 = 8w0;
    // update ghost state when tables are applied
    @old => {sawOld = 1w1;}
    @new => {sawNew = 1w1;}
    @hit(_ip_acl) => {hit__ip_acl = 8w1;}
    @hit(_fabric_ingress_dst_lkp_0) => {hit__fabric_ingress_dst_lkp_0 = 8w1;}
    // define no path mixes old and new nodes
    // $cur references the current transition state
    define execution_consistency_ipv4 = {
        $cur.in.ipv4.isValid() && $cur.in.ethernet.isValid() && $cur.eg.meta.tunnel_metadata.ingress_tunnel_type == 5w0 && $cur.eg.meta.tunnel_metadata.egress_tunnel_type == 5w0 && $cur.eg.meta.l3_metadata.lkp_ip_type == 2w1;
        => 
        !($cur.eg.sawOld == 1w1 && $cur.eg.sawNew == 1w1);
    }
    assert execution_consistency_ipv4;
}
