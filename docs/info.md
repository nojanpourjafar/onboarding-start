<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project uses SPI to control PWM outputs. You send it some data with SPI and it
changes some registers. The registers control which outputs turn on and if they do
PWM or not. There is also a register for the duty cycle, which changes how long the
signal is on.

## How to test

Send it data with SPI and check if the outputs change.

## External hardware

None