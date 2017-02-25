#!/usr/bin/env python
# -*- coding: utf8 -*-

# import
import time
import signal
from datetime import datetime

import RPi.GPIO as GPIO
import requests
from lcd import Lcd
from MFRC522 import MFRC522
from keypad import Keypad
import json

from pad4pi import rpi_gpio

# Timing constants
DELAY = 0.0005

GPIO.setmode(GPIO.BOARD)

# GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(38, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(35, GPIO.IN, pull_up_down=GPIO.PUD_UP)

BASE_URL = 'http://192.168.43.200:3000/api/'

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

showKeyPad = False

### KEYPAD ###
keypad = Keypad()

def getCourses():
    lcd.lcd_clear()
    r = requests.get(BASE_URL + 'courses')
    courses = r.json()

    lcd.lcd_string("", lcd.LCD_LINE_2)

    for index, course in enumerate(courses):
        if index == 0:
            lcd.lcd_string(course['code'], lcd.LCD_LINE_1)
        elif index == 1:
            lcd.lcd_string(course['code'], lcd.LCD_LINE_2)
        else:
            lcd.lcd_string(courses[index-1]['code'], lcd.LCD_LINE_1)
            lcd.lcd_string(course['code'], lcd.LCD_LINE_2)
        time.sleep(1)

    return courses


def getStudent(uid):
    r = requests.get(BASE_URL + 'student_by_uid/' + uid)
    student = r.json()
    return student


def markAttendance(course, lecture, uid):

    response = getStudent(uid)

    if 'error' in response and response['error']:
        lcd.lcd_string('No user with ID:', lcd.LCD_LINE_1)
        lcd.lcd_string(uid, lcd.LCD_LINE_2)
        return lecture, False
    else:
        student = response

    registered = False

    for index, course_ in enumerate(student['courses']):
        if course['_id'] == course_['_id']:
            registered = True
            break

    if registered:
        attendance_ = lecture['attendance']
        lecture['attendance'].append(student['_id'])
        r = requests.put(BASE_URL + 'lecture/attendance/' + lecture['_id'] + '/' + student['_id'],
                         json=lecture)
        response = r.json()

        if 'error' in response and response['error']:
            lecture['attendance'] = attendance_
            lcd.lcd_string(student['matric_no'], lcd.LCD_LINE_1)
            lcd.lcd_string("Already Marked", lcd.LCD_LINE_2)
        else:
            lecture = response
            lcd.lcd_string(student['matric_no'], lcd.LCD_LINE_1)
            lcd.lcd_string("Marked", lcd.LCD_LINE_2)

        return lecture, student

    else:
        lcd.lcd_string(student['matric_no'] + ' not', lcd.LCD_LINE_1)
        lcd.lcd_string('registered', lcd.LCD_LINE_2)

        return lecture, student


def readCards(course, lecture):
    lcd.lcd_string("You may now ", lcd.LCD_LINE_1)
    lcd.lcd_string("swipe cards...", lcd.LCD_LINE_2)

    time.sleep(1)

    lcd.lcd_clear()

    current = 0

    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while True:

        students = []

        # blue_btn = GPIO.input(40)
        # green_btn = GPIO.input(36)
        # red_btn = GPIO.input(38)
        # black_btn = GPIO.input(35)

        # if not blue_btn:
        #     if current < len(students) -1:
        #         current += 1
        #         #lcd.lcd_string(students[current], lcd.LCD_LINE_1)
        # elif not green_btn:
        #     if current > 0:
        #         current -= 1
        #         #lcd.lcd_string(students[current], lcd.LCD_LINE_1)
        # elif not red_btn:
        #     return
        # elif not black_btn:
        #     return students[current]

        # Scan for cards
        (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            lcd.lcd_clear()
            lcd.lcd_string("Card detected:", lcd.LCD_LINE_1)

        # Get the UID of the card
        (status,uid) = MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:

            uid_ = str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3])

            # Print UID
            lcd.lcd_string(uid_, lcd.LCD_LINE_2)

            (lecture, student) = markAttendance(course, lecture, uid_)

            if student != False:
                students.append(student['matric_no'])



def selectCourse(courses):
    current = 0

    lcd.lcd_string(courses[current]['code'], lcd.LCD_LINE_1)
    lcd.lcd_string("", lcd.LCD_LINE_2)

    while True:
        # blue_btn = GPIO.input(40)
        # green_btn = GPIO.input(36)
        # red_btn = GPIO.input(38)
        # black_btn = GPIO.input(35)
        #
        # if not blue_btn:
        #     print("Next")
        #     if current < len(courses) -1:
        #         current += 1
        #         lcd.lcd_string(courses[current]['code'], lcd.LCD_LINE_1)
        # elif not green_btn:
        #     print("Previous")
        #     if current > 0:
        #         current -= 1
        #         lcd.lcd_string(courses[current]['code'], lcd.LCD_LINE_1)
        # elif not red_btn:
        #     print("Back")
        #     return
        # elif not black_btn:
        #     print("Selected")
        #     return courses[current]
        time.sleep(0.2)


def createLecture(course):
    r = requests.post(BASE_URL + 'lecture', data = {
        'course': course['_id'],
        'topic': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'about': {
            'page': {
                'raw': '',
                'html': ''
            },
            'bio': ''
        },
        'attendance': [],
        'schedule': [],
    })
    lecture = r.json()
    return lecture


def readKeypad():
    last_str = keypad.current_str
    while True:
        if keypad.is_ok_clicked:
            return
        elif last_str != keypad.current_str:
            print keypad.current_str
        last_str = keypad.current_str

        if showKeyPad:
            lcd.lcd_string(last_str, lcd.LCD_LINE_1)


def main():
    lcd.lcd_string("Welcome", lcd.LCD_LINE_1)
    time.sleep(1)  # 3 second delay

    lcd.lcd_string("Enter a Course", lcd.LCD_LINE_1)
    lcd.lcd_string("code (e.g. 503)", lcd.LCD_LINE_2)

    time.sleep(1)


    readKeypad()

    # courses = getCourses()
    #
    # lcd.lcd_string("Please select a ", lcd.LCD_LINE_1)
    # lcd.lcd_string("Course", lcd.LCD_LINE_2)
    #
    # time.sleep(1)
    #
    # course = selectCourse(courses)
    #
    # lcd.lcd_string("Course Selected:", lcd.LCD_LINE_1)
    # lcd.lcd_string(course['code'], lcd.LCD_LINE_2)
    #
    # time.sleep(0.5)
    #
    # lecture = createLecture(course)
    #
    # lcd.lcd_string("Lecture Created:", lcd.LCD_LINE_1)
    # lcd.lcd_string(lecture['topic'], lcd.LCD_LINE_2)
    #
    # time.sleep(0.5)
    #
    # readCards(course, lecture)


if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    lcd.lcd_byte(0x01, False)
    lcd.lcd_string("Goodbye!", lcd.LCD_LINE_1)
    GPIO.cleanup()

