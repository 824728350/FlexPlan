specification {
   ghost bit<8> hit__port_vlan_mapping = 8w0;
   @hit(_port_vlan_mapping) => {hit__port_vlan_mapping = 8w1;}
   define table_access_vlan = {
       placeholder;
       =>
       $cur.eg.version.hit__port_vlan_mapping == 8w1;
   }
   assert table_access_vlan;
}
