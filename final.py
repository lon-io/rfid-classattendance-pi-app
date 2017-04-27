#!/usr/bin/env python
# -*- coding: utf8 -*-

# import
import time
import signal
from datetime import datetime
import sys
import RPi.GPIO as GPIO
import requests
from lcd import Lcd
from MFRC522 import MFRC522
from keypad import Keypad
import json
import urllib


# Timing constants
DELAY = 0.0005

GPIO.setmode(GPIO.BOARD)

# GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(38, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(35, GPIO.IN, pull_up_down=GPIO.PUD_UP)

BASE_URL = 'http://127.0.0.1:3000/api/'

continue_reading = True

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()
    sys.exit()

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Create an object of the class Lcd
lcd = Lcd()

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
    keypad.current_str = ""
    last_str = ""
    lcd.lcd_string("You may now ", lcd.LCD_LINE_1)
    lcd.lcd_string("swipe cards...", lcd.LCD_LINE_2)
    time.sleep(1)
    lcd.lcd_clear()
    global continue_reading
    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while continue_reading:
        if keypad.is_ok_clicked:
            keypad.resetKeypad()
            return last_str
        elif keypad.is_delete_clicked:
            keypad.resetKeypad()
            return 'delete'
        elif keypad.is_back_clicked:
            keypad.resetKeypad()
            return 'back'
        students = []
        # Scan for cards
        (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            print "Card detected"
            lcd.lcd_clear()
            lcd.lcd_string("Card detected:", lcd.LCD_LINE_1)

        # Get the UID of the card
        (status,uid) = MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:
            uid_ = str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3])

            # Print UID
            print "Card read UID: " + uid_
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
    keypad.current_str = ""
    last_str = ""
    while True:
        if keypad.is_ok_clicked:
            keypad.resetKeypad()
            return last_str
        elif keypad.is_delete_clicked:
            keypad.resetKeypad()
            return False
        elif last_str != keypad.current_str:
            last_str = keypad.current_str
            if keypad.is_back_clicked:
                keypad.resetKeypad()
            if keypad.should_show:
                # Todo: Should  check that the string contains only integers
                lcd.lcd_clear()
                lcd.lcd_string(last_str, lcd.LCD_LINE_1)

def getCourse(current_str):
    lcd.lcd_clear()

    try:
        r = requests.get(BASE_URL + 'coursecode/' + current_str)
        response = r.json()
    except:
        lcd.lcd_string('Network error', lcd.LCD_LINE_1)
        lcd.lcd_string('Retrying...', lcd.LCD_LINE_2)
        while True:
            try:
                r = requests.get(BASE_URL + 'coursecode/' + current_str)
                response = r.json()
            except:
                pass
            if keypad.is_back_clicked:
                keypad.resetKeypad()
                lcd.lcd_clear()
                lcd.lcd_string('Back', lcd.LCD_LINE_1)
                time.sleep(1)
                lcd.lcd_string('Try again', lcd.LCD_LINE_1)
                return False
            elif keypad.is_delete_clicked:
                lcd.lcd_clear()
                lcd.lcd_string('Cancelled', lcd.LCD_LINE_1)
                time.sleep(1)
                keypad.resetKeypad()
                return 'cancel'

    if 'error' in response and response['error']:
        lcd.lcd_string('No course:' + ' EEE' + current_str[:-1] , lcd.LCD_LINE_1)
        lcd.lcd_string(current_str[-1:]+'. Try again', lcd.LCD_LINE_2)
        time.sleep(1)
        return False
    else:
        course = response
    return course


def main():
    lcd.lcd_string("Welcome", lcd.LCD_LINE_1)
    time.sleep(2)  # 2 second delay

    lcd.lcd_string("Enter a Course", lcd.LCD_LINE_1)
    lcd.lcd_string("code (e.g. 503)", lcd.LCD_LINE_2)

    keypad.should_show = True
    course_code = readKeypad()
    if not course_code:
        lcd.lcd_string("Cancelled", lcd.LCD_LINE_1)
        lcd.lcd_string("", lcd.LCD_LINE_2)
    else:
        course = getCourse(course_code)

        if course == 'cancel':
            return

        while not course:
            course_code = readKeypad()
            if not course_code:
                lcd.lcd_string("Cancelled", lcd.LCD_LINE_1)
                lcd.lcd_string("", lcd.LCD_LINE_2)
                return
            course = getCourse(keypad.current_str)

        lcd.lcd_string("Course Selected:", lcd.LCD_LINE_1)
        lcd.lcd_string(course['code'], lcd.LCD_LINE_2)

        time.sleep(1.0)

        lecture = createLecture(course)

        lcd.lcd_string("Lecture Created:", lcd.LCD_LINE_1)
        lcd.lcd_string(lecture['topic'], lcd.LCD_LINE_2)

        time.sleep(0.5)

        read_cards = readCards(course, lecture)
        if read_cards == 'delete':
            return
        elif read_cards == 'back':
            ###########
            lcd.lcd_string("Enter a Course", lcd.LCD_LINE_1)
            lcd.lcd_string("code (e.g. 503)", lcd.LCD_LINE_2)

            keypad.should_show = True
            course_code = readKeypad()
            if not course_code:
                lcd.lcd_string("Cancelled", lcd.LCD_LINE_1)
                lcd.lcd_string("", lcd.LCD_LINE_2)
            else:
                course = getCourse(course_code)

            if course == 'cancel':
                return

            while not course:
                course_code = readKeypad()
                if not course_code:
                    lcd.lcd_string("Cancelled", lcd.LCD_LINE_1)
                    lcd.lcd_string("", lcd.LCD_LINE_2)
                    return
                course = getCourse(keypad.current_str)

            lcd.lcd_string("Course Selected:", lcd.LCD_LINE_1)
            lcd.lcd_string(course['code'], lcd.LCD_LINE_2)

            time.sleep(1.0)

            lecture = createLecture(course)

            lcd.lcd_string("Lecture Created:", lcd.LCD_LINE_1)
            lcd.lcd_string(lecture['topic'], lcd.LCD_LINE_2)


            time.sleep(0.5)

            read_cards = readCards(course, lecture)
            if read_cards == 'delete':
                return
            elif read_cards == 'back':
                return



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
        timeout = 300
        uptime = 0
        delay = 5
        while (urllib.urlopen(BASE_URL + 'test').getcode() != 200):
            lcd.lcd_string('Initializing', lcd.LCD_LINE_1)
            lcd.lcd_string('Local Network...', lcd.LCD_LINE_2)
            time.sleep(delay)  # 3 second delay
            uptime+=delay
            if (uptime >= timeout):
                lcd.lcd_string('Timedout waiting', lcd.LCD_LINE_1)
                lcd.lcd_string('4 network -> BYE', lcd.LCD_LINE_2)
                time.sleep(3)
                sys.exit()
        lcd.lcd_string('Connected...', lcd.LCD_LINE_1)
        lcd.lcd_string('', lcd.LCD_LINE_2)
        main()
    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(1)
        lcd.lcd_clear()
        GPIO.cleanup()

