specification {
   // preserve processing outcome of egress_spec
   define field_consistency_espec = {
   $cur.in.packet == $old.in.packet;
   $cur.in.packet == $new.in.packet; 
   => 
   $cur.eg.sm.egress_spec == $new.eg.sm.egress_spec || $cur.eg.sm.egress_spec == $old.eg.sm.egress_spec;
   }
   assert field_consistency_espec;
}
