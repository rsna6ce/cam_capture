import time
import subprocess
import re
from web_ui import param
from web_ui import app
from web_ui import inner_status

class CameraControl():
    def __init__(self):
        self._subprocess = None

    def start(self):
        if inner_status.current_camera=='':
            return False

        camera_info = inner_status.current_camera.split(' ')
        path = camera_info[0]
        name = camera_info[1]
        size = camera_info[2]
        format ='mjpeg' #camera_info[3].lower()
        atmark = camera_info[4]
        fps = int(camera_info[5])
        video_dir = app.config["web_ui_path"] + '/../captured/videos/'
        filename = '{}-{}-{}-{}-{}fps.mkv'.format(inner_status.capture_job_name, name, format, size, fps)
        cmd = 'ffmpeg -f v4l2 -input_format {} -video_size {} -framerate {} -i {} -c:v copy -y {}'.format(
            format, size, fps, path, video_dir+filename)
        print(cmd)
        print('CameraControl.start()')
        self._subprocess = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
        return True

    def stop(self):
        if self._subprocess==None:
            return False
        print('CameraControl.stop()')
        self._subprocess.communicate(input=b'q')
        while self._subprocess.poll() is None:
            print("waiting......")
            time.sleep(1)
        self._subprocess.terminate()
        self._subprocess = None

    def get_cam_list(self):
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

    def set_cam_exposure(self, dev_name, auto, time):
        command = 'v4l2-ctl -c exposure_time_absolute={} -d {}'.format(time, dev_name)
        ret = subprocess.run(command, shell=True, capture_output=True, text=True)
        command = 'v4l2-ctl -c auto_exposure={} -d {}'.format(auto, dev_name)
        ret = subprocess.run(command, shell=True, capture_output=True, text=True)

    def get_cam_exposure(self):
        command = 'v4l2-ctl --list-devices'
        ret = subprocess.run(command, shell=True, capture_output=True, text=True)
        lines = ret.stdout.splitlines()

        cam_list = []
        cam_name = ""
        dev_name = ""
        for line in lines:
            if line.startswith('\t') and '/dev/video' in line:
                found = line.find('/')
                dev_name = line[found:]
                cam_list.append({'dev':dev_name, 'cam':cam_name})
            elif ':' in line:
                found = line.find(':')
                cam_name = line[:found]

        re_value = re.compile(r'value=[0-9]*')
        re_default = re.compile(r'default=[0-9]*')
        re_min = re.compile(r'min=[0-9]*')
        re_max = re.compile(r'max=[0-9]*')

        exposure_list = []
        for cam in cam_list:
            dev_name = cam.get('dev')
            command = 'v4l2-ctl -L -d ' + dev_name
            ret = subprocess.run(command, shell=True, capture_output=True, text=True)
            lines = ret.stdout.splitlines()
            current_setting={dev_name:{}}
            found_auto = False
            found_time = False
            for line in lines:
                if ('auto_exposure' in line and
                    'value=' in line and
                    'default=' in line):
                    found_auto = True
                    value = re_value.findall(line)[0].replace('value=','')
                    default = re_default.findall(line)[0].replace('default=','')
                    current_setting[dev_name]['auto_exposure']={'value':value, 'default':default}
                if ('exposure_time_absolute' in line and
                    'value=' in line and 'default=' in line and
                    'min=' in line and 'max=' in line):
                    found_time = True
                    value = re_value.findall(line)[0].replace('value=','')
                    default = re_default.findall(line)[0].replace('default=','')
                    min = re_min.findall(line)[0].replace('min=','')
                    max = re_max.findall(line)[0].replace('max=','')
                    current_setting[dev_name]['exposure_time_absolute']={'value':value, 'default':default, 'min':min, 'max':max}
                if found_auto and found_time:
                    exposure_list.append(current_setting)
                    break
        return exposure_list