#!/usr/bin/env python
# -*- coding: utf8 -*-

# import
import time
import signal

import RPi.GPIO as GPIO
import requests
from lcd import Lcd
import MFRC522

# Timing constants
DELAY = 0.0005

GPIO.setmode(GPIO.BOARD)

GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(38, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(35, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()


# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Create an object of the class Lcd
lcd = Lcd()

def getCourses():
    r = requests.get('http://192.168.43.200:3000/api/courses')
    courses = r.json()

    for index, course in enumerate(courses):
        if index % 2 == 0:
            lcd.lcd_string(course['code'], lcd.LCD_LINE_1)
        else:
            lcd.lcd_string(course['code'], lcd.LCD_LINE_2)
        time.sleep(2)

    return courses

def readCards():
    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while True:

        blue_btn = GPIO.input(40)
        green_btn = GPIO.input(36)
        red_btn = GPIO.input(38)
        black_btn = GPIO.input(35)


        # Scan for cards
        (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            print "Card detected"

        # Get the UID of the card
        (status,uid) = MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:

            # Print UID
            lcd.lcd_string(str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]), lcd.LCD_LINE_1)
            lcd.lcd_string("", lcd.LCD_LINE_2)


def main():
    lcd.lcd_string("Welcome", lcd.LCD_LINE_1)
    time.sleep(2)  # 3 second delay

    lcd.lcd_string("Getting all", lcd.LCD_LINE_1)
    lcd.lcd_string("Courses ...", lcd.LCD_LINE_2)

    time.sleep(1)

    courses = getCourses()

    lcd.lcd_string("Please select a ", lcd.LCD_LINE_1)
    lcd.lcd_string("Course", lcd.LCD_LINE_2)

    lcd.lcd_string(courses[0]['code'], lcd.LCD_LINE_1)
    lcd.lcd_string("", lcd.LCD_LINE_2)

    while True:
        blue_btn = GPIO.input(40)
        green_btn = GPIO.input(36)
        red_btn = GPIO.input(38)
        black_btn = GPIO.input(35)

        current = 1

        if not blue_btn:
            lcd.lcd_string(courses[current]['code'], lcd.LCD_LINE_1)
            if current < len(courses) - 1:
                current += 1
        elif not green_btn:
            lcd.lcd_string(courses[current]['code'], lcd.LCD_LINE_1)
            if current > 0:
                current -= 1
        elif not red_btn:
            return
        elif not black_btn:
            lcd.lcd_string(courses[current]['code'], lcd.LCD_LINE_1)
            lcd.lcd_string("Selected", lcd.LCD_LINE_2)
            readCards()
            return
        time.sleep(0.2)


if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    lcd.lcd_byte(0x01, False)
    lcd.lcd_string("Goodbye!", lcd.LCD_LINE_1)
    GPIO.cleanup()

