import subprocess
from flask import request, redirect, url_for, render_template, flash
from web_ui import app
from web_ui import inner_status

@app.errorhandler(404)
def non_existant_route(error):
   return redirect(url_for('menu'))

@app.route('/menu')
def menu():
    cam_list_dict, cam_list_text = get_cam_list()
    if inner_status.current_camera == '' and len(cam_list_text)>0:
        inner_status.current_camera = cam_list_text[0]
    return render_template(
        'menu.html', navi_title="menu", cam_list=cam_list_text, current_camera=inner_status.current_camera)

def get_cam_list():
    command = 'v4l2-ctl --list-devices'
    ret = subprocess.run(command, shell=True, capture_output=True, text=True)
    lines = ret.stdout.splitlines()

    cam_list_temp = []
    cam_name = ""
    dev_name = ""
    for line in lines:
        if line.startswith('\t') and '/dev/video' in line:
            found = line.find('/')
            dev_name = line[found:]
            cam_list_temp.append({'dev':dev_name, 'cam':cam_name})
        elif ':' in line:
            found = line.find(':')
            cam_name = line[:found]

    cam_list_dict = []
    cam_list_text = []
    for cam in cam_list_temp:
        command = 'v4l2-ctl --list-formats-ext -d ' + cam['dev']
        ret = subprocess.run(command, shell=True, capture_output=True, text=True)
        lines = ret.stdout.splitlines()

        keywords_format = ['[', ']:', '(', ')']
        supported_format = 'MJPG' #MJPEG only
        format_name = ''
        for line in lines:
            if all(w in line for w in keywords_format):
                if supported_format in line:
                    format_name = supported_format
                else:
                    format_name = ''
            elif 'Size:' in line and format_name!='':
                line_strip = line.strip()
                found = line_strip.rfind(' ')
                size = line_strip[found+1:]
            elif 'Interval:' in line and format_name!='':
                line_strip = line.strip()
                found1 = line_strip.find('(')
                found2 = line_strip.find(' fps')
                fps = int(float(line_strip[found1+1:found2]))
                cam_list_dict.append({'dev':cam['dev'], 'cam':cam['cam'], 'size':size, 'format':format_name, 'fps':fps})
                cam_list_text.append('{} {} {} {} @ {} fps'.format(cam['dev'], cam['cam'].replace(' ','_'), size, format_name, fps))
    return cam_list_dict, cam_list_text