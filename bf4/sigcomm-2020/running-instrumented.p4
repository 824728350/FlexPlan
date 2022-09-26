extern H havoc<H>();
extern void key_match(in bool condition);
extern void assert(in bool condition);
extern void angelic_assert(in bool condition);
extern void assume(in bool condition);
extern void bug();
extern void oob();
extern void dontCare();
extern void do_drop();

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
    bit<64> tmp_0;
    @name(".parse_cpu_header") state parse_cpu_header {
        packet.extract<cpu_header_t>(hdr.cpu_header);
        {
            if (hdr.cpu_header.isValid())  {
                meta._meta_if_index10 = hdr.cpu_header.if_index;
            } 
            else  {
                bug();
            }
        }
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
        {
            if (hdr.ipv4.isValid())  {
                meta._meta_ipv4_sa1 = hdr.ipv4.srcAddr;
            } 
            else  {
                bug();
            }
        }
        {
            if (hdr.ipv4.isValid())  {
                meta._meta_ipv4_da2 = hdr.ipv4.dstAddr;
            } 
            else  {
                bug();
            }
        }
        {
            if (hdr.ipv4.isValid())  {
                meta._meta_tcpLength9 = hdr.ipv4.totalLen + 16w65516;
            } 
            else  {
                bug();
            }
        }
        transition select(hdr.ipv4.protocol) {
            8w0x6: parse_tcp;
            default: accept;
        }
    }
    @name(".parse_tcp") state parse_tcp {
        packet.extract<tcp_t>(hdr.tcp);
        {
            if (hdr.tcp.isValid())  {
                meta._meta_tcp_sp3 = hdr.tcp.srcPort;
            } 
            else  {
                bug();
            }
        }
        {
            if (hdr.tcp.isValid())  {
                meta._meta_tcp_dp4 = hdr.tcp.dstPort;
            } 
            else  {
                bug();
            }
        }
        transition accept;
    }
    @name(".start") state start {
        meta._meta_if_index10 = (bit<8>)standard_metadata.ingress_port;
        tmp_0 = packet.lookahead<bit<64>>();
        tmp = tmp_0;
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
    bool __track_egress_spec;
    @name(".NoAction") action NoAction_0() {
    }
    @name(".nop") action nop() {
    }
    @name(".do_nat") action do_nat(bit<32> newdst) {
        {
            if (hdr.ipv4.isValid())  {
                hdr.ipv4.srcAddr = newdst;
            } 
            else  {
                bug();
            }
        }
    }
    @name(".nat") @instrument_keys() table nat {
        key = {
            hdr.ipv4.isValid(): exact @name("ipv4.$valid$") ;
            hdr.ipv4.srcAddr  : ternary @name("ipv4.srcAddr") ;
        }
        actions = {
            do_nat();
            nop();
        }
        default_action = nop();
    }
    @name("ingress.do_forward") action do_forward_1(bit<9> nhop) {
        {
            if (hdr.ipv4.isValid() && hdr.ipv4.isValid())  {
                hdr.ipv4.ttl = hdr.ipv4.ttl + 8w255;
            } 
            else  {
                bug();
            }
        }
        {
            standard_metadata.egress_spec = nhop;
            __track_egress_spec = true;
        }
    }
    @name("ingress.do_drop") action do_drop() {
        {
            standard_metadata.egress_spec = 9w511;
            __track_egress_spec = true;
        }
    }
    @name(".ipv4_lpm") @instrument_keys() table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm @name("ipv4.dstAddr") ;
        }
        actions = {
            do_drop();
            do_forward_1();
            @defaultonly NoAction_0();
        }
        default_action = NoAction_0();
    }
    apply {
        __track_egress_spec = false;
        {
            standard_metadata.egress_spec = 9w511;
            __track_egress_spec = true;
        }
        ipv4_lpm.apply();
        nat.apply();
        if (!__track_egress_spec)  {
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
