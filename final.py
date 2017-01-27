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

GPIO.setmode(GPIO.BCM)

GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)

blue_btn = GPIO.input(21)
green_btn = GPIO.input(16)
red_btn = GPIO.input(20)
black_btn = GPIO.input(19)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Create an object of the class Lcd
lcd = Lcd()


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()


def getCourses():
    r = requests.get('http://localhost:3000/api/courses')
    courses = r.json()

    for index, course in enumerate(courses):
        if index % 2 == 0:
            lcd.lcd_string(course['code'], lcd.LCD_LINE_1)
        else:
            lcd.lcd_string(course['code'], lcd.LCD_LINE_2)
        time.sleep(2)

    return courses


def main():
    # Hook the SIGINT
    signal.signal(signal.SIGINT, end_read)

    lcd.lcd_string("Welcome", lcd.LCD_LINE_1)
    time.sleep(3)  # 3 second delay

    lcd.lcd_string("Getting all", lcd.LCD_LINE_1)
    lcd.lcd_string("Courses ...", lcd.LCD_LINE_2)

    courses = getCourses()

    lcd.lcd_string("Please select a ", lcd.LCD_LINE_1)
    lcd.lcd_string("Course", lcd.LCD_LINE_2)

    lcd.lcd_string(courses[0]['code'], lcd.LCD_LINE_1)
    lcd.lcd_string("", lcd.LCD_LINE_2)

    while True:
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
            return
        time.sleep(0.2)
