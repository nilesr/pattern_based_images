## Generate images from a random pattern

Someone on fractalforums gave me the idea of creating random images based on mathematical operations

This generates a random set of operators and a random set of operands, either x, y or a random number, and composes them into a formula.

It then generates an image using the lowest order bit of the result of that formula for each pixel.

For example, if it generated the formula ((((x ^ y) - y) \* x) >> 11) & 1, then the output would look like this

![](sample/sample.png)

### Dependencies

Depends on [libpme](https://github.com/nilesr/libpme) (`pip3 install libpme`)

### Usage

	python3 generator.py [mode]

`mode` can be one of `high` or `greyscale`. If left blank, it generates an image using the lowest bit of the result of the formula. If set to high, it will use the highest bit of the result. If set to greyscale, it will use the result of the formula as a shade of grey, truncated to one byte for png.
