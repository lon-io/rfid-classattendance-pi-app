from pad4pi import rpi_gpio
import time

KEYPAD = [
        ["1", "2", "3", "A"],
        ["4", "5", "6", "B"],
        ["7", "8", "9", "C"],
        ["*", "0", "#", "D"]
]

COL_PINS = [5,6,13,19] # BCM numbering
ROW_PINS = [1,20,16,21] # BCM numbering

class Keypad:

        is_ok_clicked = False
        is_back_clicked = False
        current_str = ""
        last_char = ""

        factory = rpi_gpio.KeypadFactory()

        # Try factory.create_4_by_3_keypad
        # and factory.create_4_by_4_keypad for reasonable defaults
        keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

        def __init__(self):

                self.keypad.registerKeyPressHandler(self.printKey)


        def printKey(self, key):
                self.last_char = key
                if key == KEYPAD[3]:
                        self.is_ok_clicked = True
                elif key == KEYPAD[7]:
                        self.is_back_clicked = True
                else:
                        self.is_ok_clicked = False
                        self.is_back_clicked = False
                        self.current_str += key


# try:
#         print("Press buttons on your keypad. Ctrl+C to exit.")
#         while True:
#                 time.sleep(1)
# except KeyboardInterrupt:
#         print("Goodbye")
# finally:
#         keypad.cleanup()
