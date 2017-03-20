#!/usr/bin/env python3
import libpme, math, random, sys
import pip._vendor.progress.bar as libbar # used this in 2bit, love this dirty little hack
# The string will be used in sbuilder to print out the pattern and for the filename
operations = {
        "^": lambda x, y: x ^ y,
        "**": lambda x, y: x ** y,
        "*": lambda x, y: x * y,
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "%?": lambda x, y: x if y == 0 else x % y,
        "÷?": lambda x, y: x if y == 0 else x / y, # don't want division by zero errors, and filenames can't have / in them.
        "log? base": lambda x, y: x if abs(x) <= 1 or abs(y) <= 1 else math.log(abs(x), abs(y)),
        #"~": lambda x, y: ~(getop()(x, y)), # todo
        ">>": lambda x, y: x >> y,
        "<<": lambda x, y: x << y,
        "&": lambda x, y: x & y,
        "|": lambda x, y: x | y
}

# gensym has a 1/3 chance of returning a lambda that returns x, 1/3 for y, and 1/3 for a number generated *when gensym was run*.
def gensym():
    r = random.randint(0, 2)
    if r == 0:
        return lambda x, y: y
    elif r == 1:
        return lambda x, y: x
    else:
        r2 = random.randint(1, 16)
        # we can't just write "return lambda x, y: random.randint(1, 16)" or it would generate a different random number for each pixel. That bug took forever to find
        # as bryan says, "this is what happens when you arent completely fluent in being multiple closures deep at all times"
        return lambda x, y: r2

# iterate through syms and ops, each time returning a left associative expression
# so for ops = ["+", "*"] and syms = [5, x, y]
# it would return something that takes an x and y, and effectively returns ((y + x) * 5)
def builder(syms, ops, i = 0):
    if len(ops) == 0:
        return lambda x, y: syms[i](x, y) # if there are no more operations left, just evaluate the symbol.
    return lambda x, y: operations[ops[0]](round(builder(syms, ops[1:], i + 1)(x, y)), syms[i](x, y)) # if there are operations, pop the first one off and recurse

# used in sbuilder to pretty-print the formula
def get_bitmask_char(bitmask, greyscale):
    if greyscale == "modulo":
        return "%"
    return "&"

# Does the same thing as builder, but makes a string
def sbuilder(syms, bitmask, greyscale, ops, i = 0, recurse = False):
    if len(ops) == 0:
        return str(syms[i]("x", "y"))
    if recurse:
        return "(" + sbuilder(syms, bitmask, greyscale, ops[1:], i + 1, True) + ") " + ops[0] +  " " + str(syms[i]("x", "y"))
    return "(" + sbuilder(syms, bitmask, greyscale, ops, i, True) + ") " + get_bitmask_char(bitmask, greyscale) + " " + str(bitmask) # the first time we're called, just print the real value in parenthesis, with an &/% bitmask at the end.

# do the actual bitmasking
def mask(val, greyscale, bitmask):
    val = round(val)
    if greyscale == "modulo":
        return val % 256 # modulo by the maximum brightness for one pixel (8 bits/channel so 2**8)
    if greyscale:
        return min(255, max(0, val)) # truncate to one byte
    if bitmask == 1: # optimization. We could leave this case out and let it use the default, but it would be slower.
        return val & bitmask
    return 0 if val & bitmask == 0 else 1 # used for bitmask = 128 (arg == "high") only right now

# actually creates an image given a function and a filename.
def build(the_function, name, greyscale):
    img = libpme.PME()
    img.height = img.width = 1024
    img.color_type = libpme.color_types.GREYSCALE
    img.bit_depth = 1
    if greyscale:
        img.bit_depth = 8

    data = b'' # will hold the raw pixel data

    bar = libbar.IncrementalBar(max = img.height)
    bar.start()

    for y in range(img.height):
        data += b'\x00' # to indicate that this scanline contains raw pixel data.
        if not greyscale:
            for x in range(0, img.width, 8): # eight pixels per byte of output, because bit_depth is 1
                this_pixel = 0;
                for subx in range(8):
                    this_x = x + subx
                    val = the_function(this_x, y)
                    this_pixel += val
                    this_pixel <<= 1
                this_pixel >>= 1
                data += bytes([this_pixel])
        else: # for greyscale each pixel is one byte
            for x in range(img.width):
                data += bytes([the_function(x, y)])
        # bar.update run all the time causes screen flickering, so only run it every 13 scanlines. greyscale is so slow that we may as well run it every time anyways.
        if y % 13 == 0 or greyscale: 
            bar.index = y
            bar.update()
    bar.index = img.height # finish up
    bar.finish()
    print()

    # save the image
    img.write_raw_idat_data(img.compress(data))
    img.save(name + ".png")

# calls builder to build the the_function function and passes it the building function, build.
def generate(arg = "default", ops = False, syms = False):
    if not ops:
        ops = [random.choice([x for x, y in operations.items()]) for k in range(random.randint(2, 6))]
    if not syms:
        syms = [gensym() for i in range(len(ops) + 1)]

    literals = [f("x", "y") for f in syms]
    if "y" not in literals or "x" not in literals:
        print("DEBUG! " + sbuilder(syms, 1, False, ops) + " does not contain both x and y. Trying another")
        generate(arg)
        return

    # uncomment to use the sample data. I used this to test the builder function.
	# ops = [">>", "*", "-", "^"]
	# ops.reverse()
	# x = lambda x, y: x
	# y = lambda x, y: y
	# syms = [x, y, y, x, lambda x, y: 11]
	# syms.reverse()

    # if we're running everything, use the now-generated operations and symbols to generate all four functions and exit
    if arg == "all":
        for a in ["default", "high", "greyscale", "modulo"]:
            generate(a, ops, syms)
        return
    # set bitmask and greyscale based on arg
    bitmask = 1
    greyscale = False
    if arg == "high":
        bitmask = 128
    elif arg == "greyscale":
        greyscale = True
        bitmask = 255
    elif arg == "modulo":
        greyscale = arg
        bitmask = 255
    # we could abstract the arguments into a dictionary that maps string argument -> list [bitmask, greyscale], then the if arg == all could just iterate over [x for x, y in args.items()]. Maybe next update

    # debug
	#print(ops)
	#the_function = lambda x, y: (((x^y)-y)*x >> 11) & 1

    # print out the pattern, also generate the function
    print(sbuilder(syms, bitmask, greyscale, ops));
    the_function = lambda x, y: mask(builder(syms, ops)(x, y), greyscale, bitmask)
    # debug
	#print(the_function(2, 2))

	# i = int(sys.argv[1])
	# badfiles = open("badfiles", "r").read().split("\n")[:-1]
	# the_function = eval("lambda x, y: " + badfiles[i].split("/")[-1].replace(" BAD FILENAME.png", ""))

    # pass off control to the thing that actually uses the function to make an image, using the value of sbuilder as the filename.
    build(the_function, sbuilder(syms, bitmask, greyscale, ops), greyscale)


if len(sys.argv) > 1:
    generate(sys.argv[1].lower())
else:
    generate()
