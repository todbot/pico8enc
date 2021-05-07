#
# pico8enc_test_dualencodertest.py -- 8 rotary encoders on a Pico, testing DualEncoder PIO library
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

from rp2pio_dualincrementalencoder import DualIncrementalEncoder

encA = rotaryio.IncrementalEncoder( board.GP27, board.GP28 )
encBC = DualIncrementalEncoder(board.GP0, board.GP1, board.GP2, board.GP3)
encDE = DualIncrementalEncoder(board.GP4, board.GP5, board.GP6, board.GP7)
encFG = DualIncrementalEncoder(board.GP8, board.GP9, board.GP10, board.GP11)
encH = rotaryio.IncrementalEncoder( board.GP12, board.GP13 )

old = [0] * 8
old[0] = encA.position
(old[1],old[2]) = encBC.positions
(old[3],old[4]) = encDE.positions
(old[5],old[6]) = encFG.positions
old[7] = encH.position
lasttime = 0
has_changed = False
while True:
    pos = [0] * len(old)
    pos[0] = encA.position
    (pos[1],pos[2]) = encBC.positions
    (pos[3],pos[4]) = encDE.positions
    (pos[5],pos[6]) = encFG.positions
    pos[7] = encH.position
    
    for i in range(len(pos)):
        if old[i] != pos[i]:
            #print(f"enc:{i} {pos[i]}")
            has_changed = True
            old[i] = pos[i]
    
    if time.monotonic() - lasttime > 1 or has_changed:
        lasttime = time.monotonic()
        print(f"{time.monotonic():.2f} encoders:", encA.position,encBC.positions,encDE.positions,encFG.positions,encH.position)
        has_changed = False



