#!/usr/bin/env python3
import libpme, math, random, sys
import pip._vendor.progress.bar as libbar
img = libpme.PME()
img.height = img.width = 1024
img.color_type = libpme.color_types.GREYSCALE
img.bit_depth = 1

operations = {
        "^": lambda x, y: x ^ y,
        "**": lambda x, y: x ** y,
        "*": lambda x, y: x * y,
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "÷?": lambda x, y: x if y == 0 else x / y, # don't want division by zero errors, and filenames can't have / in them.
        #"log": lambda x, y: math.log(x, y), # giving math domain errors
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
        return lambda x, y: r


# ops = [">>", "*", "-", "^"]
# ops.reverse()
# x = lambda x, y: x
# y = lambda x, y: y
# syms = [x, y, y, x, lambda x, y: 11]
# syms.reverse()
ops = [random.choice([x for x, y in operations.items()]) for k in range(random.randint(2, 6))]
syms = [gensym() for i in range(len(ops) + 1)]
def around(x):
    return abs(round(x))
def builder(k, i = 0):
    if len(k) == 0:
        return lambda x, y: syms[i](x, y)
    return lambda x, y: operations[k[0]](round(builder(k[1:], i + 1)(x, y)), syms[i](x, y))

def sbuilder(k, i = 0, recurse = False):
    if len(k) == 0:
        return str(syms[i]("x", "y"))
    if recurse:
        return "(" + sbuilder(k[1:], i + 1, True) + ") " + k[0] +  " " + str(syms[i]("x", "y"))
    return "(" + sbuilder(k, i, True) + ") & 1"


#print(ops)
#the_function = lambda x, y: (((x^y)-y)*x >> 11) & 1
#print(sbuilder(ops));
the_function = lambda x, y: round(builder(ops)(x, y)) & 1
#print(the_function(2, 2))

# i = int(sys.argv[1])
# badfiles = open("badfiles", "r").read().split("\n")[:-1]
# the_function = eval("lambda x, y: " + badfiles[i].split("/")[-1].replace(" BAD FILENAME.png", ""))

data = b''
bar = libbar.IncrementalBar(max = img.height)
bar.start()

for y in range(1024):
    data += b'\x00'
    for x in range(0, 1024, 8):
        this_pixel = 0;
        for subx in range(8):
            this_x = x + subx
            val = the_function(this_x, y)
            this_pixel += val
            this_pixel <<= 1
        this_pixel >>= 1
        data += bytes([this_pixel])
    bar.index = y
    if y % 13 == 0: bar.update()


img.write_raw_idat_data(img.compress(data))
img.save(sbuilder(ops) + ".png")
