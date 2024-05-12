import time
import subprocess
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