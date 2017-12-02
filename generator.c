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

/*
 * To generate the patterns, we first make a list of 5 operations to apply to a starting variable
 * So there will be six operations, but the first one will only be used to supply x, y or a constant
 * Each operation holds either x, y, or a constant, and also an applicator. So if the operations
 * generated were <x, +>, <y, *>, <4, ->, <x, |> then the resulting pattern would be
 * ((((x) * y) - 4) | x). Note that the + from the first operation was ignored, the first operation
 * is only used to get an x/y/imm value.
 */
#define OPERS 6

typedef struct operation {
	int type;
	int immediate;
	int applicator;
} operation;

// Turns <x, +> into x, <4, +> into 4, etc..
int sym(operation op, int x, int y) {
	if (op.type == OP_IMMED) return op.immediate;
	return op.type == OP_X ? x : y;
}

// Helper macros for defining functions that will apply a binary operation to the given input (lhs)
// First, rhs is determined from op using sym, so if op was <4, +> then rhs = 4, and if op was <x, +>
// then rhs gets set to x. Then, lhs + rhs is computed (replacing + with whatever operation this
// function is for), and the result is returned
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

// An applicator is just one of the above functions, it takes an intermediate value (lhs), x, y and an
// operation and returns the result
typedef int_t (*applicator)(int_t, int, int, operation);

// Each applicator needs a name so that we can put it in the filename
typedef struct applicator_pair {
	applicator applicator;
	char* name;
} applicator_pair;

// Makes all the operation like <x, +> or <3, *>, randomly
// The caller is expected to free the result
operation* make_operations(int num_applicators) {
	operation* result = calloc(OPERS, sizeof(operation));
	for (int i = 0; i < OPERS; i++) {
		int r1 = rand() % 3, r2 = 0, type = 0;
		if (r1 == 0) {
			type = OP_X;
		} else if (r1 == 1) {
			type = OP_Y;
		} else {
			type = OP_IMMED;
			r2 = (rand() % 15) + 1;
		}
		result[i] = (operation) {.type = type, .immediate = r2, .applicator = rand() % num_applicators};
	}
	return result;
}

// Turns an operation's symbol into a string, so <x, +> becomes "x" and <25, -> becomes "25"
// The caller is expected to free the result
char* symstr(operation op) {
	if (op.type == OP_IMMED) {
		char* result;
		asprintf(&result, "%d", op.immediate);
		return result;
	}
	return strdup(op.type == OP_X ? "x" : "y");
}

// Makes a filename from the given set of operations.
// The caller is expected to free the result
char* make_filename(operation* ops, applicator_pair* applicators) {
	char* result = strdup("");
	// First add all the operations except the first one to result, seperated by closing parenthesis
	for (int i = 1; i < OPERS; i++) {
		char* oldresult = result;
		char* op_symstr = symstr(ops[i]);
		asprintf(&result, "%s %s %s)", result, applicators[ops[i].applicator].name, op_symstr);
		free(oldresult);
		free(op_symstr);
	}
	// Construct a string with all the opening parenthesis
	int opening_parens = OPERS - 1;
	char* openers = calloc(1, opening_parens + 1);
	memset(openers, '(', opening_parens);
	// Add the opening parenthesis, the symbol for the first operation, and the existing result together
	// and return it
	char* oldresult = result;
	char* symstr_0 = symstr(ops[0]);
	asprintf(&result, "%s%s)%s.png", openers, symstr_0, result);
	free(openers);
	free(oldresult);
	free(symstr_0);
	return result;
}

// Computes the pixel value for the given x, y pair with the passed operations and applicators
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

// Helper macro for constructing the list of applicator pairs
#define Add_simple(string, function) (applicator_pair) {.applicator = &apply_##function, .name = #string}

int main() {
	// Seed the random generator
	srand(time(NULL) * clock());
	// Set up our list of applicators using their functions and some descriptive strings
	// that will go in the filename
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

	// Allocate width*height 1-byte pixels
	uint8_t* image = calloc(DIMENSION, DIMENSION);
	// Generate random operations
	operation* ops = make_operations(NUM_APPLICATORS);
	// Compute the filename for the output file
	char* output_filename = make_filename(ops, applicators);

	/* DEBUG STUFF
	for (int i = 0; i < OPERS; i++) {
		printf("%s %s\n", applicators[ops[i].applicator].name, symstr(ops[i]));
	}
	*/

	// Compute each pixel
	for (int x = 0; x < DIMENSION; x++) {
		for (int y = 0; y < DIMENSION; y++) {
			uint8_t pixel = get_pixel(ops, x, y, applicators) % 2;
			//printf("Final pixel value is %d\n", pixel);
			pixel *= 255;
			image[x * DIMENSION + y] = pixel;
		}
	}
	// Save the image
	stbi_write_png(output_filename, DIMENSION, DIMENSION, 1, image, DIMENSION);
	printf("Written to %s\n", output_filename);
	// Clean up
	free(output_filename);
	free(image);
	free(ops);
}
