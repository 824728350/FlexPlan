CXX	 = g++
CXXFLAGS = -std=c++11 -g -Ofast -march=native -W -Wall
INCLUDES = -I/usr/include/z3 -I.
LIBS     = -lz3
PROG	 = parse

all: $(PROG)

$(PROG): $(PROG).c
	$(CXX) $(CXXFLAGS) $(INCLUDES) $^ $(LIBS) -o $@

clean:
	rm -f *.o $(PROG)

%.o: %.cc
	$(CXX) $(CXXFLAGS) -c -o $@ $<
