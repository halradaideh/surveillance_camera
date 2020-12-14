# -*- coding: UTF-8 -*-

from flask import Flask, render_template, Response
import cv2, time, pandas
from time import sleep
import sys
from fbchat import Client
from fbchat.models import *
import fbchat
import re
from getpass import getpass
# importing datetime class from datetime library
from datetime import datetime

app = Flask(__name__)

camera = cv2.VideoCapture(0)

fbchat._util.USER_AGENTS    = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"]
fbchat._state.FB_DTSG_REGEX = re.compile(r'"name":"fb_dtsg","value":"(.*?)"')

client = Client("hamdan.radaideh@hotmail.com", getpass())

from requests import get

def send_msg(msg, image):
    time=str(datetime.now())
    ip = get('https://api.ipify.org').text
    receivers_ids=['1435843372'] #, '100036488761702']
    for thread_id in receivers_ids:
        print('Send text',  file=sys.stdout)
        client.send(
            Message(text=msg+" \nat : "+time+"\nGo to http://"+str(format(ip))+"/ \n for live feed !"),
            thread_id=thread_id,
            thread_type=ThreadType.USER
        )



def gen_frames():  # generate frame by frame from camera
    # Assigning our static_back to None
    static_back = None

    # List when any moving object appear
    motion_list = [ None, None ]

    # Time of movement
    time = []

    # Initializing DataFrame, one column is start
    # time and other column is end time
    df = pandas.DataFrame(columns = ["Start", "End"])
    while True:
        sleep(0.1)
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # Initializing motion = 0(no motion)
            motion = 0

            # Converting color image to gray_scale image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Converting gray scale image to GaussianBlur
            # so that change can be find easily
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # In first iteration we assign the value
            # of static_back to our first frame
            if static_back is None:
                static_back = gray
                continue

            # Difference between static background
            # and current frame(which is GaussianBlur)
            diff_frame = cv2.absdiff(static_back, gray)

            # If change in between static background and
            # current frame is greater than 30 it will show white color(255)
            thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
            thresh_frame = cv2.dilate(thresh_frame, None, iterations = 2)

            # Finding contour of moving object
            cnts,_ = cv2.findContours(thresh_frame.copy(),
                               cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in cnts:
                if cv2.contourArea(contour) < 10000:
                    continue
                motion = 1

                (x, y, w, h) = cv2.boundingRect(contour)
                # making green rectangle arround the moving object
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

            # Appending status of motion
            motion_list.append(motion)

            motion_list = motion_list[-2:]

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Appending Start time of motion
            if motion_list[-1] == 1 and motion_list[-2] == 0:
                time.append(datetime.now())
                send_msg("Motion Detected")
                print('Motion started',  file=sys.stdout)

            # Appending End time of motion
            if motion_list[-1] == 0 and motion_list[-2] == 1:
                time.append(datetime.now())
                send_msg("Motion Finished")
                print('Motion finished',  file=sys.stdout)



            key = cv2.waitKey(1)
            # if q entered whole process will stop
            if key == ord('q'):
                # if something is movingthen it append the end time of movement
                if motion == 1:
                    time.append(datetime.now())
                break


            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True,use_reloader=False,host="192.168.1.20")
