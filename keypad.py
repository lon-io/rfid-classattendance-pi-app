
import RPi.GPIO as GPIO

KEYPAD = [
        ["1","2","3","A"],
        ["4","5","6","B"],
        ["7","8","9","C"],
        ["*","0","#","D"]
]

COL_PINS = [0,5,6,13] # BCM numbering
ROW_PINS = [19,20,16,21] # BCM numbering

for j in range(4):
        GPIO.setup(COL_PINS[j], GPIO.OUT)
        GPIO.output(COL_PINS[j], 1)

for i in range(1):
        GPIO.setup(ROW_PINS[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

try:
        while(True):
            ### code ###

except KeyboardInterrupt:
        GPIO.cleanup();