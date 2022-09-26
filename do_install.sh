#!/bin/bash

set -e

SRC_DIR="$(pwd)"

sudo apt-get update
sudo apt-get install -y cmake g++ git automake libtool libgc-dev bison flex libfl-dev libgmp-dev libboost-dev libboost-iostreams-dev libboost-graph-dev llvm pkg-config python python-scapy python-ipaddr python-ply tcpdump bc python-dev python3-dev

cd ${SRC_DIR}
wget https://github.com/protocolbuffers/protobuf/archive/refs/tags/v3.2.0.tar.gz
tar -zxvf v3.2.0.tar.gz
cd protobuf-3.2.0/
sudo apt-get install -y autoconf automake libtool curl make g++ unzip
./autogen.sh
./configure
make -j4
make check
sudo make install
sudo ldconfig

cd ${SRC_DIR}
wget https://github.com/Z3Prover/z3/archive/refs/tags/z3-4.8.7.tar.gz
tar -zxvf z3-4.8.7.tar.gz
cd z3-z3-4.8.7/
python scripts/mk_make.py
cd build
make -j4
sudo make install

cd /usr/local/include/
sudo wget https://github.com/pantor/inja/releases/download/v2.2.0/inja.hpp

cd ${SRC_DIR}
wget https://github.com/nlohmann/json/archive/refs/tags/v3.7.3.tar.gz
tar -zxvf v3.7.3.tar.gz
cd json-3.7.3
mkdir build
cd build
cmake ..
make -j4
sudo make install

cd ${SRC_DIR}
wget https://github.com/apache/thrift/archive/refs/tags/0.11.0.tar.gz
tar -zxvf 0.11.0.tar.gz
cd thrift-0.11.0/
sudo apt-get install -y libssl-dev
./bootstrap.sh
./configure
make -j4
sudo make install
sudo ldconfig

cd ${SRC_DIR}/bf4
mkdir build
cd build
cmake -DENABLE_UNIFIED_COMPILATION=OFF ..
make
sudo make install
make cptemplate
