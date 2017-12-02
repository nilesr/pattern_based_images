#define STB_IMAGE_WRITE_IMPLEMENTATION
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define _GNU_SOURCE
#include "stb/stb_image_write.h"
#include "stb/stb_image.h"
#include <inttypes.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

#define DIMENSION 1024

typedef __int128 int_t;

#define OP_IMMED 0
#define OP_X 1
#define OP_Y 2

#define OPERS 6

typedef struct operation {
	int type;
	int immediate;
	int applicator;
} operation;

int sym(operation op, int x, int y) {
	if (op.type == OP_IMMED) return op.immediate;
	return op.type == OP_X ? x : y;
}

#define Make_complex(name, ...) int_t apply_##name(int_t lhs, int x, int y, operation op) { int_t rhs = sym(op, x, y); __VA_ARGS__; }
#define Make_simple(name, ...) Make_complex(name, return __VA_ARGS__)

Make_simple(xor, lhs ^ rhs)
Make_simple(pow, pow(lhs, rhs))
Make_simple(times, lhs * rhs)
Make_simple(plus, lhs + rhs)
Make_simple(minus, lhs - rhs)
Make_simple(mod, lhs % (rhs == 0 ? 1 : rhs))
Make_simple(div, lhs / (rhs == 0 ? 1 : rhs))
Make_simple(left_shift, lhs << rhs)
Make_simple(right_shift, lhs >> rhs)
Make_simple(and, lhs & rhs)
Make_simple(or, lhs | rhs)
Make_complex(log_base, long double log_rhs = log(rhs); return log(lhs) / (log_rhs == 0 ? 1 : log_rhs))

typedef int_t (*applicator)(int_t, int, int, operation);

typedef struct applicator_pair {
	applicator applicator;
	char* name;
} applicator_pair;

#define Add_simple(string, function) (applicator_pair) {.applicator = &apply_##function, .name = #string}

operation* make_operations(int num_applicators) {
	operation* result = calloc(OPERS, sizeof(operation));
	for (int i = 0; i < OPERS; i++) {
		int r1 = rand() % 3, r2 = 0, type = 0;
		switch (r1) {
			case 0:
				type = OP_X;
				break;
			case 1:
				type = OP_Y;
				break;
			case 2:
				type = OP_IMMED;
				r2 = (rand() % 15) + 1;
				break;
		}
		result[i] = (operation) {.type = type, .immediate = r2, .applicator = rand() % num_applicators};
	}
	return result;
}

char* symstr(operation op) {
	if (op.type == OP_IMMED) {
		char* result;
		asprintf(&result, "%d", op.immediate);
		return result;
	}
	return strdup(op.type == OP_X ? "x" : "y");
}

char* make_filename(operation* ops, applicator_pair* applicators) {
	char* result = NULL;
	int opening_parens = OPERS - 1;
	for (int i = 1; i < OPERS; i++) {
		char* oldresult = result;
		char* op_symstr = symstr(ops[i]);
		asprintf(&result, "%s %s %s)", result ? result : "", applicators[ops[i].applicator].name, op_symstr);
		free(oldresult);
		free(op_symstr);
	}
	char* openers = calloc(1, opening_parens + 1);
	memset(openers, '(', opening_parens);
	char* oldresult = result;
	char* symstr_0 = symstr(ops[0]);
	asprintf(&result, "%s%s)%s.png", openers, symstr_0, result);
	free(openers);
	free(oldresult);
	free(symstr_0);
	return result;
}

int get_pixel(operation* ops, int x, int y, applicator_pair* applicators) {
	int_t intermediate = sym(ops[0], x, y);
	//printf("Starting with %s\n", symstr(ops[0]));
	for (int i = 1; i < OPERS; i++) {
		//printf("Now applying %s %s\n", applicators[ops[i].applicator].name, symstr(ops[i]));
		intermediate = applicators[ops[i].applicator].applicator(intermediate, x, y, ops[i]);
		//printf("Now %"PRIdMAX"\n", intermediate);
	}
	//printf("\n\n");
	return intermediate;
}

int main() {
	srand(time(NULL) * clock());
	applicator_pair* applicators = (applicator_pair[]) {
		Add_simple(^, xor),
		Add_simple(*, times),
		Add_simple(+, plus),
		Add_simple(-, minus),
		Add_simple(%\077, mod),
		Add_simple(÷\077, div),
		Add_simple(log\077 base, log_base),
		Add_simple(<<, left_shift),
		Add_simple(>>, right_shift),
		Add_simple(&, and),
		Add_simple(|, or),
	};
	#define NUM_APPLICATORS 11

	uint8_t* scanlines = calloc(DIMENSION, DIMENSION);
	operation* ops = make_operations(NUM_APPLICATORS);
	/* DEBUG STUFF
	for (int i = 0; i < OPERS; i++) {
		printf("%s %s\n", applicators[ops[i].applicator].name, symstr(ops[i]));
	}
	*/
	char* output_filename = make_filename(ops, applicators);
	for (int x = 0; x < DIMENSION; x++) {
		for (int y = 0; y < DIMENSION; y++) {
			uint8_t pixel = get_pixel(ops, x, y, applicators) % 2;
			//printf("Final pixel value is %d\n", pixel);
			pixel *= 255;
			scanlines[x * DIMENSION + y] = pixel;
		}
	}
	stbi_write_png(output_filename, DIMENSION, DIMENSION, 1, scanlines, DIMENSION);
	printf("Written to %s\n", output_filename);
	free(output_filename);
	free(scanlines);
	free(ops);
}
