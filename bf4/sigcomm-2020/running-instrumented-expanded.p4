enum flow_def_ipv4_lpm_0__action_type_t {
    do_drop,
    do_forward_1,
    NoAction_0
}

struct flow_def_ipv4_lpm_0 {
    bool                               hit;
    bool                               reach;
    flow_def_ipv4_lpm_0__action_type_t action_run;
    bit<9>                             do_forward_1__nhop;
    @matchKind("lpm") 
    bit<32>                            key_ipv4_lpm_0_ipv4_dstAddr__val;
    @matchKind("lpm") 
    bit<32>                            key_ipv4_lpm_0_ipv4_dstAddr__prefix;
}

@controlled() extern flow_def_ipv4_lpm_0 query_ipv4_lpm_0(@matchKind("lpm") in bit<32> ipv4_lpm_0_ipv4_dstAddr);
extern void end_ipv4_lpm_0();
enum flow_def_nat_0__action_type_t {
    do_nat,
    nop
}

struct flow_def_nat_0 {
    bool                          hit;
    bool                          reach;
    flow_def_nat_0__action_type_t action_run;
    bit<32>                       do_nat__newdst;
    @matchKind("exact") 
    bool                          key_nat_0_ipv4__valid_;
    @matchKind("ternary") 
    bit<32>                       key_nat_0_ipv4_srcAddr__val;
    @matchKind("ternary") 
    bit<32>                       key_nat_0_ipv4_srcAddr__mask;
}

@controlled() extern flow_def_nat_0 query_nat_0(@matchKind("exact") in bool nat_0_ipv4__valid_, @matchKind("ternary") in bit<32> nat_0_ipv4_srcAddr);
extern void end_nat_0();
extern void key_match(in bool condition);
extern void angelic_assert(in bool condition);
extern void bug();

#include <core.p4>

#include <v1model.p4>

struct intrinsic_metadata_t {
    bit<4>  mcast_grp;
    bit<4>  egress_rid;
    bit<32> lf_field_list;
}

struct meta_t {
    bit<1>  do_forward;
    bit<32> ipv4_sa;
    bit<32> ipv4_da;
    bit<16> tcp_sp;
    bit<16> tcp_dp;
    bit<32> nhop_ipv4;
    bit<32> if_ipv4_addr;
    bit<48> if_mac_addr;
    bit<1>  is_ext_if;
    bit<16> tcpLength;
    bit<8>  if_index;
}

header cpu_header_t {
    bit<64> preamble;
    bit<8>  device;
    bit<8>  reason;
    bit<8>  if_index;
}

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<8>  flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

struct metadata {
    bit<1>  _meta_do_forward0;
    bit<32> _meta_ipv4_sa1;
    bit<32> _meta_ipv4_da2;
    bit<16> _meta_tcp_sp3;
    bit<16> _meta_tcp_dp4;
    bit<32> _meta_nhop_ipv45;
    bit<32> _meta_if_ipv4_addr6;
    bit<48> _meta_if_mac_addr7;
    bit<1>  _meta_is_ext_if8;
    bit<16> _meta_tcpLength9;
    bit<8>  _meta_if_index10;
}

struct headers {
    @name(".cpu_header") 
    cpu_header_t cpu_header;
    @name(".ethernet") 
    ethernet_t   ethernet;
    @name(".ipv4") 
    ipv4_t       ipv4;
    @name(".tcp") 
    tcp_t        tcp;
}

parser ParserImpl(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    bit<64> tmp;
    bit<64> tmp_1;
    bit<64> tmp_2;
    @name(".parse_cpu_header") state parse_cpu_header {
        packet.extract<cpu_header_t>(hdr.cpu_header);
        transition select(hdr.cpu_header.isValid()) {
            true: parse_cpu_header_true;
            false: parse_cpu_header_false;
        }
    }
    state parse_cpu_header_true {
        meta._meta_if_index10 = hdr.cpu_header.if_index;
        transition parse_cpu_header_join;
    }
    state parse_cpu_header_false {
        bug();
        transition parse_cpu_header_join;
    }
    state parse_cpu_header_join {
        transition parse_ethernet;
    }
    @name(".parse_ethernet") state parse_ethernet {
        packet.extract<ethernet_t>(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            16w0x800: parse_ipv4;
            default: accept;
        }
    }
    @name(".parse_ipv4") state parse_ipv4 {
        packet.extract<ipv4_t>(hdr.ipv4);
        transition select(hdr.ipv4.isValid()) {
            true: parse_ipv4_true;
            false: parse_ipv4_false;
        }
    }
    state parse_ipv4_true {
        meta._meta_ipv4_sa1 = hdr.ipv4.srcAddr;
        transition parse_ipv4_join;
    }
    state parse_ipv4_false {
        bug();
        transition parse_ipv4_join;
    }
    state parse_ipv4_join {
        transition select(hdr.ipv4.isValid()) {
            true: parse_ipv4_true_0;
            false: parse_ipv4_false_0;
        }
    }
    state parse_ipv4_true_0 {
        meta._meta_ipv4_da2 = hdr.ipv4.dstAddr;
        transition parse_ipv4_join_0;
    }
    state parse_ipv4_false_0 {
        bug();
        transition parse_ipv4_join_0;
    }
    state parse_ipv4_join_0 {
        transition select(hdr.ipv4.isValid()) {
            true: parse_ipv4_true_1;
            false: parse_ipv4_false_1;
        }
    }
    state parse_ipv4_true_1 {
        meta._meta_tcpLength9 = hdr.ipv4.totalLen + 16w65516;
        transition parse_ipv4_join_1;
    }
    state parse_ipv4_false_1 {
        bug();
        transition parse_ipv4_join_1;
    }
    state parse_ipv4_join_1 {
        transition select(hdr.ipv4.protocol) {
            8w0x6: parse_tcp;
            default: accept;
        }
    }
    @name(".parse_tcp") state parse_tcp {
        packet.extract<tcp_t>(hdr.tcp);
        transition select(hdr.tcp.isValid()) {
            true: parse_tcp_true;
            false: parse_tcp_false;
        }
    }
    state parse_tcp_true {
        meta._meta_tcp_sp3 = hdr.tcp.srcPort;
        transition parse_tcp_join;
    }
    state parse_tcp_false {
        bug();
        transition parse_tcp_join;
    }
    state parse_tcp_join {
        transition select(hdr.tcp.isValid()) {
            true: parse_tcp_true_0;
            false: parse_tcp_false_0;
        }
    }
    state parse_tcp_true_0 {
        meta._meta_tcp_dp4 = hdr.tcp.dstPort;
        transition parse_tcp_join_0;
    }
    state parse_tcp_false_0 {
        bug();
        transition parse_tcp_join_0;
    }
    state parse_tcp_join_0 {
        transition accept;
    }
    @name(".start") state start {
        meta._meta_if_index10 = (bit<8>)standard_metadata.ingress_port;
        tmp_2 = packet.lookahead<bit<64>>();
        tmp_1 = tmp_2;
        tmp = tmp_1;
        transition select(tmp[63:0]) {
            64w0: parse_cpu_header;
            default: parse_ethernet;
        }
    }
}

control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {
    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    bool __track_egress_spec_0;
    apply {
        standard_metadata.egress_spec = 9w511;
        __track_egress_spec_0 = true;
        {
            flow_def_ipv4_lpm_0 ipv4_lpm;
            ipv4_lpm = query_ipv4_lpm_0(hdr.ipv4.dstAddr);
            if (ipv4_lpm.hit) {
                key_match(hdr.ipv4.dstAddr & (32w1 << ipv4_lpm.key_ipv4_lpm_0_ipv4_dstAddr__prefix) - 32w1 == ipv4_lpm.key_ipv4_lpm_0_ipv4_dstAddr__val & (32w1 << ipv4_lpm.key_ipv4_lpm_0_ipv4_dstAddr__prefix) - 32w1);
                if (!(hdr.ipv4.isValid() || (32w1 << ipv4_lpm.key_ipv4_lpm_0_ipv4_dstAddr__prefix) - 32w1 == 32w0))  {
                    bug();
                } 
            }
            if (ipv4_lpm.action_run == flow_def_ipv4_lpm_0__action_type_t.NoAction_0) {
            }
            else  {
                if (ipv4_lpm.action_run == flow_def_ipv4_lpm_0__action_type_t.do_forward_1) {
                    angelic_assert(true);
                    {
                        if (hdr.ipv4.isValid() && hdr.ipv4.isValid())  {
                            hdr.ipv4.ttl = hdr.ipv4.ttl + 8w255;
                        } 
                        else  {
                            bug();
                        }
                        standard_metadata.egress_spec = ipv4_lpm.do_forward_1__nhop;
                        __track_egress_spec_0 = true;
                    }
                }
                else  {
                    if (ipv4_lpm.action_run == flow_def_ipv4_lpm_0__action_type_t.do_drop) {
                        angelic_assert(true);
                        {
                            standard_metadata.egress_spec = 9w511;
                            __track_egress_spec_0 = true;
                        }
                    }
                    else  {
                        ;
                    }
                }
            }
            end_ipv4_lpm_0();
        }
        {
            flow_def_nat_0 nat;
            nat = query_nat_0(hdr.ipv4.isValid(), hdr.ipv4.srcAddr);
            if (nat.hit) {
                key_match(hdr.ipv4.isValid() == nat.key_nat_0_ipv4__valid_ && hdr.ipv4.srcAddr & nat.key_nat_0_ipv4_srcAddr__mask == nat.key_nat_0_ipv4_srcAddr__val & nat.key_nat_0_ipv4_srcAddr__mask);
                if (!(hdr.ipv4.isValid() || nat.key_nat_0_ipv4_srcAddr__mask == 32w0))  {
                    bug();
                } 
            }
            if (nat.action_run == flow_def_nat_0__action_type_t.nop) {
                angelic_assert(true);
                {
                }
            }
            else  {
                if (nat.action_run == flow_def_nat_0__action_type_t.do_nat) {
                    angelic_assert(true);
                    {
                        if (hdr.ipv4.isValid())  {
                            hdr.ipv4.srcAddr = nat.do_nat__newdst;
                        } 
                        else  {
                            bug();
                        }
                    }
                }
                else  {
                    ;
                }
            }
            end_nat_0();
        }
        if (!__track_egress_spec_0)  {
            bug();
        } 
    }
}

control DeparserImpl(packet_out packet, in headers hdr) {
    apply {
        packet.emit<cpu_header_t>(hdr.cpu_header);
        packet.emit<ethernet_t>(hdr.ethernet);
        packet.emit<ipv4_t>(hdr.ipv4);
        packet.emit<tcp_t>(hdr.tcp);
    }
}

control verifyChecksum(inout headers hdr, inout metadata meta) {
    apply {
    }
}

control computeChecksum(inout headers hdr, inout metadata meta) {
    apply {
    }
}

V1Switch<headers, metadata>(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;

void copy_field_list(in metadata from, inout metadata to, in standard_metadata_t smfrom, inout standard_metadata_t smto, in bit<16> discriminator) {
}
