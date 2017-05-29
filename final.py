#!/usr/bin/env python
# -*- coding: utf8 -*-

# import
import time
import signal
from datetime import datetime
import sys
import openpyxl
import RPi.GPIO as GPIO
import requests
from lcd import Lcd
from MFRC522 import MFRC522
from keypad import Keypad
import json
import urllib2


# Timing constants
DELAY = 0.0005

GPIO.setmode(GPIO.BOARD)

GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
        
        # reset the display
            lcd.lcd_clear()
            
        # prompt the user to swipe again
        lcd.lcd_string('Swipe your card', lcd.LCD_LINE_1)
            
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
            
            # reset the display
            lcd.lcd_clear()
            
            # prompt the user to swipe again
            lcd.lcd_string('Swipe your card', lcd.LCD_LINE_1)
        else:
            lecture = response
            lcd.lcd_string(student['matric_no'], lcd.LCD_LINE_1)
            lcd.lcd_string("Marked", lcd.LCD_LINE_2)
            
            # reset the display
            lcd.lcd_clear()
            
            # prompt the user to swipe again
            lcd.lcd_string('Swipe your card', lcd.LCD_LINE_1)
            
            # open lecture file
            lectureFile = openpyxl.load_workbook(fileName)
            # update lecture file
            lectureFile.active.append(student['matric_no'])
            lectureFile.save(fileName)

        return lecture, student

    else:
        lcd.lcd_string(student['matric_no'] + ' not', lcd.LCD_LINE_1)
        lcd.lcd_string('registered', lcd.LCD_LINE_2)
        
        # reset the display
            lcd.lcd_clear()
            
        # prompt the user to swipe again
        lcd.lcd_string('Swipe your card', lcd.LCD_LINE_1)

        return lecture, student


def readCards(course, lecture):
    keypad.current_str = ""
    last_str = ""
    lcd.lcd_string("You may now ", lcd.LCD_LINE_1)
    lcd.lcd_string("swipe cards...", lcd.LCD_LINE_2)
    time.sleep(1)
    
    # reset the display
    lcd.lcd_clear()
            
    # prompt the user to swipe again
    lcd.lcd_string('Swipe your card', lcd.LCD_LINE_1)
    
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

    if 'error' in response and response['error']:
        lcd.lcd_string('No course:' + ' EEE' + current_str[:-1] , lcd.LCD_LINE_1)
        lcd.lcd_string(current_str[-1:]+'. Try again', lcd.LCD_LINE_2)
        time.sleep(1)
        return False
    else:
        course = response
    return course
    
def main():
    # greet the user
    lcd.lcd_string('Hello!', lcd.LCD_LINE_1)
    
    # make the message stay for a while
    time.sleep(2)
    
    # clear the lcd
    lcd.lcd_clear()
    
    # inform the user that the domain of functionality is EEE courses
    lcd.lcd_string('EEE courses', lcd.LCD_LINE_1)
    lcd.lcd_string('only!', lcd.LCD_LINE_2)
    
    # ensure keypad shows
    keypad.should_show = True
    
    # make the message stay briefly
    time.sleeep(1)
    
    # clear the lcd
    lcd.lcd_clear()
    
    # initialize variable to be used in while loop conditional
    password = ''
    
    while password != '1234':
        # request for password from user
        lcd.lcd_string('Password?', lcd.LCD_LINE_1)
        # hide user's input
        keypad.should_show = False
        # read from keypad
        password = readKeypad()
        # reset the keypad
        keypad.resetKeypad()
        
        # verify if password is valid
        if password == '1234':
            # grant access
            lcd.lcd_string('Access granted!', lcd.LCD_LINE_1)
            
            # make the message stay for a while
            time.sleep(1)
            
            # clear the lcd
            lcd.lcd_clear()
        else:
            # deny access
            lcd.lcd_string('Access denied!', lcd.LCD_LINE_1)
            
            # make the message stay for a while
            time.sleep(1)
            
            # clear the lcd
            lcd.lcd_clear()
            
    # display user's input
    keypad.should_show = True
    
    # initialize variable that'll be used in while loop conditional
    course = ''
    while not course:
        # ask user for course digits
        lcd.lcd_string('Course Digits?', lcd.LCD_LINE_1)
        lcd.lcd_string('EEE 204 -> 204', lcd.LCD_LINE_2)
        # read user's input
        course_digits = readKeypad()
        # reset the keypad
        keypad.resetKeypad()
        
        # verify is course digits will fit into infrastructure
        course = getCourse(course_digits)
        if course:
            # notify user of course_digits' validity
            lcd.lcd_string("Course Selected:", lcd.LCD_LINE_1)
            lcd.lcd_string(course['code'], lcd.LCD_LINE_2)
            
            # give a time delay to make message readable
            time.sleep(1)
            
            # clear the lcd
            lcd.lcd_clear()
    
    # create lecture instance
    lecture = createLecture(course)
    # create a file name for lecture
    global fileName
    fileName = 'EEE_%d_%2d%.2d%4d' % (course_digits, datetime.date.today().day,
                                      datetime.date.today().month,
                                      datetime.date.today().year)
    # create a file for the lecture
    lectureFile = openpyxl.Workbook()
    lectureFile.save(fileName)
    # notify user that a lecture instance has been created
    lcd.lcd_string("Lecture Created:", lcd.LCD_LINE_1)
    lcd.lcd_string(lecture['topic'], lcd.LCD_LINE_2)
    
    # add a little time delay to make message readable
    time.sleep(1)
    #clear the lcd
    lcd.lcd_clear()
    
    # begin attendance session
    readCards(course, lecture)
    
    # inform user that the system is ready to shut down
    lcd.lcd_string('Ready to', lcd.LCD_LINE_1)
    lcd.lcd_string('shut down!', lcd.LCD_LINE_2)
    
if __name__ == '__main__':
-
-    try:
-        timeout = 300
-        uptime = 0
-        delay = 5
-
-        try:
-            code = urllib2.urlopen(BASE_URL + 'test').getcode()
-        except urllib2.URLError, err:
-            code = 0
-
-        while (code != 200):
-            lcd.lcd_string('Initializing', lcd.LCD_LINE_1)
-            lcd.lcd_string('Local Network...', lcd.LCD_LINE_2)
-            time.sleep(delay)  # 3 second delay
-            uptime+=delay
-            try:
-                code = urllib2.urlopen(BASE_URL + 'test').getcode()
-            except urllib2.URLError, err:
-                pass
-            if uptime >= timeout:
-                lcd.lcd_string('Timedout waiting', lcd.LCD_LINE_1)