## Generate images from a random pattern

Taken from someone elses' idea on fractialforums and expanded

This generates a random set of operators and a random set of operands, either x, y or a random number, and composes them into a formula.

It then generates an image using the lowest order bit of the result of that formula for each pixel.

For example, if it generated the formula (((x ^ y) - y) \* x) >> 11, then the output would look like this

![](sample/sample.png)
