
import RPi.GPIO as GPIO
from keypad import Keypad

GPIO.setmode(GPIO.BOARD)

### KEYPAD ###
keypad = Keypad()

def readKeypad():
    last_str = keypad.current_str
    while True:
        if keypad.is_ok_clicked:
            return
        elif last_str != keypad.current_str:
            print keypad.current_str
        last_str = keypad.current_str
        print last_str

def main():
    readKeypad()


if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    GPIO.cleanup()

