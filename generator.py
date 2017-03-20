#!/usr/bin/env python3
import libpme, math, random, sys
import pip._vendor.progress.bar as libbar
operations = {
        "^": lambda x, y: x ^ y,
        "**": lambda x, y: x ** y,
        "*": lambda x, y: x * y,
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "÷?": lambda x, y: x if y == 0 else x / y, # don't want division by zero errors, and filenames can't have / in them.
        "log? base": lambda x, y: x if abs(x) <= 1 or abs(y) <= 1 else math.log(abs(x), abs(y)),
        #"~": lambda x, y: ~(getop()(x, y)), # todo
        ">>": lambda x, y: x >> y,
        "<<": lambda x, y: x << y,
        "&": lambda x, y: x & y,
        "|": lambda x, y: x | y
}

def gensym():
    r = random.randint(0, 2)
    if r == 0:
        return lambda x, y: y
    elif r == 1:
        return lambda x, y: x
    else:
        r = random.randint(1, 16)
        # we can't just write "return lambda x, y: random.randint(1, 16)" or it would generate a different random number for each pixel. That bug took forever to find
        # as bryan says, "this is what happens when you arent completely fluent in being multiple closures deep at all times"
        return lambda x, y: r

def builder(syms, k, i = 0):
    if len(k) == 0:
        return lambda x, y: syms[i](x, y)
    return lambda x, y: operations[k[0]](round(builder(syms, k[1:], i + 1)(x, y)), syms[i](x, y))

def sbuilder(syms, bitmask, k, i = 0, recurse = False):
    if len(k) == 0:
        return str(syms[i]("x", "y"))
    if recurse:
        return "(" + sbuilder(syms, bitmask, k[1:], i + 1, True) + ") " + k[0] +  " " + str(syms[i]("x", "y"))
    return "(" + sbuilder(syms, bitmask, k, i, True) + ") & " + str(bitmask)

def mask(val, greyscale, bitmask):
    if greyscale:
        return min(255, max(0, val))
    if bitmask == 1:
        return val & bitmask
    else:
        return 0 if val & bitmask == 0 else 1

def build(the_function, name, greyscale):
    img = libpme.PME()
    img.height = img.width = 1024
    img.color_type = libpme.color_types.GREYSCALE
    img.bit_depth = 1

    data = b''
    bar = libbar.IncrementalBar(max = img.height)
    bar.start()

    if greyscale:
        img.bit_depth = 8

    for y in range(1024):
        data += b'\x00'
        if not greyscale:
            for x in range(0, 1024, 8):
                this_pixel = 0;
                for subx in range(8):
                    this_x = x + subx
                    val = the_function(this_x, y)
                    this_pixel += val
                    this_pixel <<= 1
                this_pixel >>= 1
                data += bytes([this_pixel])
        else:
            for x in range(1024):
                data += bytes([the_function(x, y)])
        bar.index = y
        if y % 13 == 0 or greyscale: bar.update()
    bar.index = 1024
    bar.finish()
    print()

    img.write_raw_idat_data(img.compress(data))
    img.save(name + ".png")

def generate(arg = "default", ops = False, syms = False):
	# ops = [">>", "*", "-", "^"]
	# ops.reverse()
	# x = lambda x, y: x
	# y = lambda x, y: y
	# syms = [x, y, y, x, lambda x, y: 11]
	# syms.reverse()
    if not ops:
        ops = [random.choice([x for x, y in operations.items()]) for k in range(random.randint(2, 6))]
    if not syms:
        syms = [gensym() for i in range(len(ops) + 1)]

    if arg == "all":
        for a in ["default", "high", "greyscale"]:
            generate(a, ops, syms)
        return

    bitmask = 1
    greyscale = False
    if arg == "high":
        bitmask = 128
    elif arg == "greyscale":
        greyscale = True
        bitmask = 255

	#print(ops)
	#the_function = lambda x, y: (((x^y)-y)*x >> 11) & 1
    print(sbuilder(syms, bitmask, ops));
    the_function = lambda x, y: mask(round(builder(syms, ops)(x, y)), greyscale, bitmask)
	#print(the_function(2, 2))

	# i = int(sys.argv[1])
	# badfiles = open("badfiles", "r").read().split("\n")[:-1]
	# the_function = eval("lambda x, y: " + badfiles[i].split("/")[-1].replace(" BAD FILENAME.png", ""))

    build(the_function, sbuilder(syms, bitmask, ops), greyscale)


if len(sys.argv) > 1:
    generate(sys.argv[1].lower())
else:
    generate()
