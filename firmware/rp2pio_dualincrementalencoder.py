# SPDX-FileCopyrightText: 2021 Jeff Epler, written for Adafruit Industries
#
# SPDX-License-Identifier: MIT
#
# This example is adapted in part from micropython:
# https://github.com/micropython/micropython/pull/6894/files
#
# Originally from:
# https://github.com/adafruit/Adafruit_CircuitPython_PIOASM/blob/main/examples/rotaryencoder.py
# Modified by @todbot on 6 May 2021
# to support dual rotary encoders

import adafruit_pioasm
import board
import rp2pio
import array
import digitalio

class DualIncrementalEncoder:
    _state_look_up_table = array.array(
        "b",
        [
            # Direction = 1
            0,  # 00 to 00
            -1,  # 00 to 01
            +1,  # 00 to 10
            +2,  # 00 to 11
            +1,  # 01 to 00
            0,  # 01 to 01
            +2,  # 01 to 10
            -1,  # 01 to 11
            -1,  # 10 to 00
            +2,  # 10 to 01
            0,  # 10 to 10
            +1,  # 10 to 11
            +2,  # 11 to 00
            +1,  # 11 to 01
            -1,  # 11 to 10
            0,  # 11 to 11
            
            # Direction = 0
            0,  # 00 to 00
            -1,  # 00 to 01
            +1,  # 00 to 10
            -2,  # 00 to 11
            +1,  # 01 to 00
            0,  # 01 to 01
            -2,  # 01 to 10
            -1,  # 01 to 11
            -1,  # 10 to 00
            -2,  # 10 to 01
            0,  # 10 to 10
            +1,  # 10 to 11
            -2,  # 11 to 00
            +1,  # 11 to 01
            -1,  # 11 to 10
            0,  # 11 to 11
        ],
    )

    # note the '4' here, for 4 inputs
    _sm_code = adafruit_pioasm.assemble(
        """
    again:
        in pins, 4
        mov x, isr
        jmp x!=y, push_data
        mov isr, null
        jmp again
    push_data:
        push
        mov y, x
    """
    )

    _sm_init = adafruit_pioasm.assemble("set y 31")

    def __init__(self, pin_a, pin_b, pin_c, pin_d):
        # pins_are_sequenctial only takes two pins at a time
        if not rp2pio.pins_are_sequential([pin_a, pin_b]):
            raise ValueError("Pins must be sequential")
        if not rp2pio.pins_are_sequential([pin_b, pin_c]):
            raise ValueError("Pins must be sequential")
        if not rp2pio.pins_are_sequential([pin_c, pin_d]):
            raise ValueError("Pins must be sequential")

        self._sm = rp2pio.StateMachine(
            self._sm_code,
            160_000,
            init=self._sm_init,
            first_in_pin=pin_a,
            in_pin_count=4,
            pull_in_pin_up=0b1111,
            in_shift_right=False,
        )

        self._counter0 = 0
        self._counter1 = 0
        self._direction0 = 0
        self._direction1 = 0
        self._lut0_index = 0
        self._lut1_index = 0
        self._buffer = bytearray(1)

    def _update_state_machine(self, state):
        lut0_index = self._lut0_index | (state & 3)
        lut1_index = self._lut1_index | (state>>2 & 3)
        lut0 = self._state_look_up_table[lut0_index]
        lut1 = self._state_look_up_table[lut1_index]
        #print(f"\t state:{state:08b} lut0:{lut0_index}/{lut0} lut1:{lut1_index}/{lut1}")
        self._counter0 += lut0
        self._counter1 += lut1
        if lut0:
            self._direction0 = 1 if (lut0 > 0) else 0
        if lut1:
            self._direction1 = 1 if (lut1 > 0) else 0
        self._lut0_index = ((lut0_index << 2) & 0b1100) | (self._direction0 << 4)
        self._lut1_index = ((lut1_index << 2) & 0b1100) | (self._direction1 << 4)

    def deinit(self):
        self._sm.deinit()
        
    def get_positions(self):
        """ returns a tuple containing both encoder positions """
        while self._sm.in_waiting:
            self._sm.readinto(self._buffer)
            self._update_state_machine(self._buffer[0])
            # turn quarter_counts into position counts
        return (self._counter0 // 4, self._counter1 // 4)

    # note this fails sometimes because loosing quarter counts
    def set_positions(self, vals):
        val0,val1 = vals
        if val0 is not None:
            self._counter0 = val0*4
        if val1 is not None:
            self._counter1 = val1*4

    positions = property(get_positions, set_positions)
        

### Demo

if __name__ == "__main__":
    encoders = DualIncrementalEncoder(board.GP0, board.GP1, board.GP2, board.GP3)

    old_positions = None
    while True:
        positions = encoders.positions
        if old_positions != positions:
            print("Dual Encoders:", positions)
            old_positions = positions
