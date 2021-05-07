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
import usb_midi
import adafruit_midi
from adafruit_midi.control_change   import ControlChange

from rp2pio_dualincrementalencoder import DualIncrementalEncoder

midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1])

# config for all the knobs
# note that some of these will be controlled by DualIncrementalEncoder
# and some by rotaryio.IncrementalEncoder
knobs_config  = (
    #  encoder pins (pinA,pinB,switchPin)   #color    # midi CC number # mult
    ( (board.GP12, board.GP13, board.GP16), 0xFF00FF, 28 ),  # right-most knob
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
    def __init__(self, encoder, encoder_slot, button, color, midi_cc_num, midi_cc_val=0):
        self._encoder = encoder
        self._encoder_slot = encoder_slot  # for DualEncoder
        self.button = button
        self.color = color
        self.midi_cc_num = midi_cc_num
        self.change = 0
        self.midi_mult = 4  # amount to multiple 
        self._pos = 0
        self._pos_mm = 0  # goes from 0-255
        self.update() # set up the rest of things

    def update(self):
        self.button.update()
        if self._encoder_slot == 0:     # check if dualencoder position 0
            pos,other = self._encoder.positions
        elif self._encoder_slot == 1:   # check if dualencoder position 1
            other,pos = self._encoder.positions
        else:                           # normal rotaryio encoder
            pos = self._encoder.position
        self.change = self._pos - pos
        self._pos = pos
        if self._pos_mm >= 0 and self._pos_mm <= 127:
            self._pos_mm = min(max(self._pos_mm + self.change,0),127)

    @property
    def position(self):
        return self._pos
    
    @property
    def midi_cc_val(self):
        #self._midi_cc_val = self._pos_mm  #min(max(self._pos_mm,0),255)
        #return self._midi_cc_val
        return self._pos_mm #* self.midi_mult

#--------------------------

# set up the knobs, store them in an array
knobs = [None] * len(knobs_config)
#for i in range(1, len(knobs_config)-6, 2): # step by twos because DualEncoders
for i in range(1, len(knobs_config)-1, 2): # step by twos because DualEncoders
    (pins0, color0, midi_cc_num0) = knobs_config[i+1]
    (pins1, color1, midi_cc_num1) = knobs_config[i+0] # count backwards so DualEncoder works right
    pin0_A, pin0_B, pin0_switch = pins0
    pin1_A, pin1_B, pin1_switch = pins1
    print("DualEncoder:",i+1,i,pin0_A, pin0_B, pin1_A, pin1_B)
    encoderdual = DualIncrementalEncoder(pin0_A, pin0_B, pin1_A, pin1_B)
    button_pin = DigitalInOut(pin0_switch)
    button_pin.pull = Pull.UP
    button0 = Debouncer(button_pin)
    button_pin = DigitalInOut(pin1_switch)
    button_pin.pull = Pull.UP
    button1 = Debouncer(button_pin)
    knobs[i+1] = Knob(encoderdual, 0, button0, color0, midi_cc_num0)
    knobs[i+0] = Knob(encoderdual, 1, button1, color1, midi_cc_num1)

for i in 0,7:  # the two single encoders because of PCB layout silliness
    (pins, color, midi_cc_num) = knobs_config[i]
    print("IncrementalEncoder:",i,pins,color)
    pin_A, pin_B, pin_switch = pins
    encoder = rotaryio.IncrementalEncoder( pin_A, pin_B )
    button_pin = DigitalInOut(pin_switch)
    button_pin.pull = Pull.UP
    button = Debouncer(button_pin)
    knobs[i] = Knob(encoder, None, button, color, midi_cc_num) 
    
leds = neopixel.NeoPixel(led_pin, num_leds, brightness=0.2, auto_write=False)
# testing
leds.fill(0xff6600); leds.show();
time.sleep(0.25)
leds.fill(0); leds[0] = (0,0xff,0); leds[len(leds)-1] = (0,0xff,0); leds.show()
time.sleep(0.25)
leds.fill(0); leds.show()

# convert midi cc value to a led strip info
def val_to_leds(color,val):
    di = 128 // len(leds)  # 128 values in midi CC
    i = len(leds)-1 - (val // di)  
    leds.fill(color)
    leds[i] = 0xffffff
    leds.show()

# def val_to_leds2(color,val):
#     di = 
#     ifl = val / 16
#     i = val // 16
    
    
#     i = len(leds)-1 - (val // 16)  # FIXME magic 16
#     leds.fill(color)
#     leds[i] = 0xffffff
#     leds.show()

# i=0
# while True:
#     val_to_leds(0x00ff00, i)
#     print(f"i:{i}")
#     #leds.fill(0x00ff00)
#     #leds[i] = 0xffffff
#     #leds.show()
#     i = (i + 1) % 127
#     time.sleep(0.1)
    
print("pico8enc - 8 rotary encoders midi controller")
while True:
    #time.sleep(0.1)
    for knob in knobs:
        knob.update()
        diff = knob.change
        if diff or knob.button.fell or knob.button.rose:
            val_to_leds(knob.color, knob.midi_cc_val)
            midi.send(ControlChange(knob.midi_cc_num, knob.midi_cc_val))
            butpress = '-'
            if knob.button.fell:
                butpress = 'v'
            if knob.button.rose:
                butpress = '^'
            print("MIDI CC#:%d = %d knob:%d diff:%d but:%s" % (knob.midi_cc_num, knob.midi_cc_val, knob.position, diff, butpress))


    
