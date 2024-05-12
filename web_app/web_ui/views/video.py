import os
import threading
import time
import queue
import cv2
import subprocess
import shutil
from flask import request, redirect, url_for, render_template, flash, make_response, jsonify
from web_ui import app
from web_ui import inner_status
from web_ui import param
from web_ui import web_ui_path

@app.route('/video')
def video():
    video_basedir=web_ui_path + '/../captured/videos'
    file_and_dirs = os.listdir(video_basedir)
    videos_files = [f for f in file_and_dirs if os.path.isfile(os.path.join(video_basedir, f)) and f!='.git_keep']
    videos_files.sort()
    for i in range(len(videos_files)):
        file_size = round(os.path.getsize(video_basedir+'/'+videos_files[i]) / 1024/1024, 2)
        videos_files[i] += ' ({}MB)'.format(file_size)
    selected_file = ''
    if len(videos_files)>0:
        selected_file = videos_files[-1]

    return render_template(
        'video.html', navi_title="video",
        videos_files = videos_files,
        selected_file = selected_file)

@app.route('/video/trigger', methods=['POST'])
def video_trigger():
    videos_file = request.form.get('videos_file','')
    trigger = request.form.get('trigger', '')
    if videos_file=='':
        return redirect(url_for('video'))
    if trigger == 'remove':
        print('remove', videos_file)
        video_basedir=web_ui_path + '/../captured/videos'
        os.remove(video_basedir+'/'+videos_file)
    return redirect(url_for('video'))

@app.route('/video/preview', methods=['GET'])
def preview_video():
    video_basedir = web_ui_path + '/../captured/videos/'
    filename = request.args.get('filename','')
    filepath = video_basedir + filename
    if not os.path.exists(filepath):
        return ''
    # decode first frame
    cap = cv2.VideoCapture(filepath)
    ret, img = cap.read()
    cap.release()

    ret, jpeg = cv2.imencode('.jpg', img)
    response = make_response(jpeg.tobytes())
    response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set('Accept-Ranges', 'bytes')
    response.headers.set('Cache-Control', 'public, max-age=60')
    return response

@app.route('/video/download', methods=['GET'])
def video_download():
    filename = request.args.get('filename','')
    if filename=='':
        return redirect(url_for('video'))
    video_basedir=web_ui_path + '/../captured/videos'
    response = make_response()
    response.data = open(video_basedir+'/'+filename, "rb").read()
    response.headers['Content-Disposition'] = 'attachment; filename=' + filename
    response.mimetype = 'video/x-matroska'
    return response

