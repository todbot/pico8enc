#
# pico8enc_test.py -- 8 rotary encoders on a Pico, no extra hardware
#
# 2021 - @todbot / Tod Kurt - todbot.com
#

import time
import board
from digitalio import DigitalInOut, Direction, Pull
import neopixel
import rotaryio

# eight rotary encoders w/ switches
encoder_pins = ( (board.GP12, board.GP13, board.GP16),  # pin A, pin B, pin for switch
                 (board.GP10, board.GP11, board.GP17),
                 (board.GP8, board.GP9, board.GP18),
                 (board.GP6, board.GP7, board.GP19),
                 (board.GP4, board.GP5, board.GP20),
                 (board.GP2, board.GP3, board.GP21),
                 (board.GP0, board.GP1, board.GP22),
                 (board.GP27, board.GP28, board.GP26),
)
encoders = []
encoder_buttons = []
last_encoder_vals = []
for pins in encoder_pins:
    pin_A, pin_B, pin_switch = pins
    encoder = rotaryio.IncrementalEncoder( pin_A, pin_B )
    button = DigitalInOut(pin_switch)
    button.pull = Pull.UP
    encoders.append(encoder)
    encoder_buttons.append(button)
    last_encoder_vals.append( encoder.position ) 

print("pico8enc - 8 rotary encoders test")
while True:
    for i in range(len(encoders)):
        encoder_diff = encoders[i].position - last_encoder_vals[i] # encoder clicks since last read
        last_encoder_vals[i] = encoders[i].position
        butpress = "v" if encoder_buttons[i].value==False else '.'
        print(encoders[i].position, encoder_diff, butpress , end=" - ")
    print()
    time.sleep(0.1)
    
