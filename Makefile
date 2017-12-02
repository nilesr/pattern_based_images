all: CFLAGS += "-Ofast"
all: base
debug: CFLAGS += "-ggdb3"
debug: base
base:
	gcc -o generator generator.c -march=native ${CFLAGS} -Wall -Wextra -Wpedantic -pipe -lm
clean:
	rm dotter
.PHONY: all clean base debug
