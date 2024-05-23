import subprocess
from flask import request, redirect, url_for, render_template, flash
from web_ui import app
from web_ui import inner_status
from web_ui import camera_control

@app.errorhandler(404)
def non_existant_route(error):
   return redirect(url_for('menu'))

@app.route('/menu')
def menu():
    cam_list_dict, cam_list_text = camera_control.get_cam_list()
    if inner_status.current_camera == '' and len(cam_list_text)>0:
        inner_status.current_camera = cam_list_text[0]
    return render_template(
        'menu.html', navi_title="menu", cam_list=cam_list_text, current_camera=inner_status.current_camera)

