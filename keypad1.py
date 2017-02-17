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


def printKey(key):
        print(key)

factory = rpi_gpio.KeypadFactory()

# Try factory.create_4_by_3_keypad
# and factory.create_4_by_4_keypad for reasonable defaults
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

keypad.registerKeyPressHandler(printKey)

try:
        print("Press buttons on your keypad. Ctrl+C to exit.")
        while True:
                time.sleep(1)
except KeyboardInterrupt:
        print("Goodbye")
finally:
        keypad.cleanup()
