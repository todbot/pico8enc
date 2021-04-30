#
# pico8enc_midi.py -- 8 rotary encoders on a Pico, no extra hardware
#
# 2021 - @todbot / Tod Kurt - todbot.com
#

import time
import board
from digitalio import DigitalInOut, Direction, Pull
import rotaryio
from adafruit_debouncer import Debouncer
import neopixel
import adafruit_midi
from adafruit_midi.control_change   import ControlChange

# config for all the knobs
# OOPS: Looks like CircuitPython can either support EITHER
# - 8 rotary encoders and NO neopixels, OR
# - 7 rotary encoders and neopixels
# DANGIT
knobs_config  = (
    #  encoder pins (pinA,pinB,switchPin)   #color    # midi CC number # mult
#    ( (board.GP12, board.GP13, board.GP16), 0xFF00FF, 28 ),  # right-most knob
    ( (board.GP10, board.GP11, board.GP17), 0x0000FF, 27 ), 
    ( (board.GP8,  board.GP9,  board.GP18), 0x00FF00, 26 ), 
    ( (board.GP6,  board.GP7,  board.GP19), 0xFFFF00, 25 ), 
    ( (board.GP4,  board.GP5,  board.GP20), 0x00FFFF, 24 ), 
    ( (board.GP2,  board.GP3,  board.GP21), 0xFF3300, 23 ),
    ( (board.GP0,  board.GP1,  board.GP22), 0x0033FF, 22 ), 
    ( (board.GP27, board.GP28, board.GP26), 0xFF00FF, 21 ),  # left-most knob
)

num_leds = 8
led_pin = board.GP14

# contains all the info needed about a knob
class Knob:
    def __init__(self, encoder, button, color, midi_cc_num, midi_cc_val=0):
        self.encoder = encoder
        self.button = button
        self.color = color
        self.midi_cc_num = midi_cc_num
        self._midi_cc_val = midi_cc_val
        self.change = 0
        self.encoder.position = 127
        self.mult = 4
        self._last_val = self.encoder.position

    def update(self):
        self.button.update()
        pos = self.encoder.position
        self.encoder.position = min(max(pos,0),127)
        self.change = self._last_val - pos
        self._last_val = pos

    @property
    def position(self):
        return 127 - self.encoder.position
    
    @property
    def midi_cc_val(self):
        self._midi_cc_val = 2 * self.position
        return self._midi_cc_val
    
#--------------------------

# # set up the knobs, store them in an array
knobs = []
for config in knobs_config:
    (pins, color, midi_cc_num) = config
    pin_A, pin_B, pin_switch = pins
    encoder = rotaryio.IncrementalEncoder( pin_A, pin_B )
    button_pin = DigitalInOut(pin_switch)
    button_pin.pull = Pull.UP
    button = Debouncer(button_pin)
    knobs.append( Knob(encoder, button, color, midi_cc_num) )

leds = neopixel.NeoPixel(led_pin, num_leds, brightness=0.2, auto_write=False)

# testing
leds.fill(0xff6600); leds.show();
time.sleep(0.5)
leds.fill(0); leds[0] = (0,0xff,0); leds[len(leds)-1] = (0,0xff,0); leds.show()
time.sleep(0.5)
leds.fill(0); leds.show()

# convert midi cc value to a led strip info
def val_to_leds(color,val):
    leds.fill(color)
    i = len(leds)-1  - (val // len(leds))
    leds[i] = 0xffffff
    leds.show()


print("pico8enc - 8 rotary encoders midi controller")
while True:
    for knob in knobs:
        knob.update()
        diff = knob.change
        if diff or knob.button.fell or knob.button.rose:
            val_to_leds(knob.color, knob.midi_cc_val)
            butpress = '-'
            if knob.button.fell:
                butpress = 'v'
                #midi.send(ControlChange(knob.midi_cc_num, knob.midi_cc_val))
            if knob.button.rose:
                butpress = '^'
            print("MIDI CC#:%d = %d knob:%d diff:%d but:%s" % (knob.midi_cc_num, knob.midi_cc_val, knob.position, diff, butpress))


    
