specification {
   define decrement_ipv4_ttl = {
       placeholder;
       =>
       $cur.eg.ipv4.ttl == $cur.in.ipv4.ttl - 1;
   }
   assert decrement_ipv4_ttl;
}
