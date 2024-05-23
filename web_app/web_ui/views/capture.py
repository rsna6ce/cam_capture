import os
import time
import threading
import cv2
import numpy as np
import urllib
import urllib.parse
from datetime import datetime, timedelta
from flask import request, redirect, url_for, render_template, flash, jsonify, Response, make_response
from web_ui import app
from web_ui import inner_status
from web_ui import camera_control
from web_ui import param
from web_ui import web_ui_path

camera_control_lock = threading.Lock()

@app.route('/capture')
def capture():
    if inner_status.current_camera=="":
        #flash('select camera','success')
        return redirect(url_for('menu'))
    start_enable = 'disabled' if inner_status.capture_running else ''
    stop_enable = '' if inner_status.capture_running else 'disabled'
    exposure_enable = False
    camera_info = inner_status.current_camera.split(' ')
    dev_name = camera_info[0]
    exposure_params = camera_control.get_cam_exposure()
    exposure={}
    for exposure_param in exposure_params:
        param = exposure_param.get(dev_name)
        if param:
            exposure_enable = True
            exposure = param
            break
    return render_template(
        'capture.html', navi_title="capture",
        capture_running=inner_status.capture_running,
        current_camera=inner_status.current_camera,
        start_enable=start_enable, stop_enable=stop_enable,
        exposure_enable=exposure_enable, exposure=exposure)

@app.route('/set_camera')
def set_camera():
    if inner_status.capture_running:
        return jsonify({'result':'ERROR', 'reason':'capture running'})
    cam = request.args.get('cam','')
    inner_status.current_camera = cam
    return jsonify({'result':'OK', 'reason':''})

@app.route('/set_exposure')
def set_exposure():
    if inner_status.capture_running:
        return jsonify({'result':'ERROR', 'reason':'capture running'})
    camera_info = inner_status.current_camera.split(' ')
    dev_name = camera_info[0]
    auto = request.args.get('auto','')
    time = request.args.get('time','')
    with camera_control_lock:
        camera_control.set_cam_exposure(dev_name, auto, time)
    return jsonify({'result':'OK', 'reason':''})

@app.route("/preview_camera")
def preview_camera():
    with camera_control_lock:
        if inner_status.capture_running:
            filename = app.config["web_ui_path"] + "/static/image/now_recording.png"
            with open(filename, 'rb') as f:
                response = make_response(f.read())
                response.headers.set('Content-Type', 'image/jpeg')
                response.headers.set('Accept-Ranges', 'bytes')
                response.headers.set('Cache-Control', 'public, max-age=60')
                return response
        try:
            camera_info = inner_status.current_camera.split(' ')
            path = camera_info[0]
            name = camera_info[1]
            size = camera_info[2]
            format =camera_info[3]
            atmark = camera_info[4]
            fps = int(camera_info[5])
            width = int(size[: size.find('x')])
            height = int(size[size.find('x')+1 :])

            cap = cv2.VideoCapture(path)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')) #MJPEG固定
            cap.set(cv2.CAP_PROP_FPS, fps)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            ret, img = cap.read()
            cap.release()

            ret, jpeg = cv2.imencode('.jpg', img)
            response = make_response(jpeg.tobytes())
            response.headers.set('Content-Type', 'image/jpeg')
            response.headers.set('Accept-Ranges', 'bytes')
            response.headers.set('Cache-Control', 'public, max-age=60')
            return response

        except Exception as e:
            print( "Exception", e.args)
            return ''


@app.route('/capture/trigger', methods=['POST'])
def capture_trigger():
    with camera_control_lock:
        trigger = request.form.get('trigger','')
        capture_running = (trigger == 'start')
        if capture_running:
            dt_now = datetime.now()
            job_name = dt_now.strftime('%Y%m%d_%H%M%S')
            inner_status.capture_job_name = job_name
            camera_control.start()
        else:
            inner_status.capture_job_name = ''
            camera_control.stop()

        inner_status.capture_running = capture_running
        return redirect(url_for('capture'))


