#!/usr/bin/env python
# -*- coding: utf8 -*-

#import
import RPi.GPIO as GPIO
import time
import signal
from lcd import Lcd
import MFRC522

# Timing constants
DELAY = 0.0005

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()

def main():
    # Hook the SIGINT
    signal.signal(signal.SIGINT, end_read)

    # Create an object of the class MFRC522
    MIFAREReader = MFRC522.MFRC522()

    # Create an object of the class Lcd
    lcd = Lcd()

    lcd.lcd_string("Welcome", lcd.LCD_LINE_1)

