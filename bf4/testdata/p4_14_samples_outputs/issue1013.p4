#include <core.p4>
#include <v1model.p4>

@name("headers") header headers_0 {
    bit<32> x;
}

struct metadata {
}

struct headers {
    @name(".h") 
    headers_0 h;
}

parser ParserImpl(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name(".start") state start {
        transition accept;
    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name(".mask") action mask() {
        hdr.h.x = hdr.h.x & ~32w0x0 | hdr.h.x & 32w0x0;
    }
    @name(".t") table t {
        actions = {
            mask;
        }
    }
    apply {
        t.apply();
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

