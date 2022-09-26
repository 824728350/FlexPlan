#include <core.p4>
#include <v1model.p4>

struct data_t {
    bit<32> f1;
    bit<32> f2;
}

struct metadata {
    @name(".m") 
    data_t m;
}

struct headers {
}

parser ParserImpl(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name(".start") state start {
        transition accept;
    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name("._nop") action _nop() {
    }
    @name(".t1") table t1 {
        actions = {
            _nop;
        }
    }
    @name(".t2") table t2 {
        actions = {
            _nop;
        }
    }
    apply {
        if (meta.m.f1 == 32w0) {
            if (meta.m.f2 == 32w0) {
                t1.apply();
            }
        }
        else {
            t2.apply();
        }
    }
}

control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {
    }
}

control DeparserImpl(packet_out packet, in headers hdr) {
    apply {
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

V1Switch(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;

