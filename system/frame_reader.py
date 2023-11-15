import time
import requests
import threading
import cv2
import numpy as np
from system.utils import get_ipv4_address

CAMERA_API = f"http://{get_ipv4_address()}:8005/stream-manage/lastframe"
def url_last_frame(camera_id):
    return f"{CAMERA_API}/{camera_id}"

class Camera:
    def __init__(self, camera_id, fps=25, rotate=False, size=None):
        self._camera_id = camera_id
        self._last_frame = None
        self._fps = fps
        self._rotate = rotate
        self._size = size

    def last_frame(self):
        return self._last_frame

    def update_last_frame(self):
        self._last_frame = self.get_frame_from_http_api()

    def get_frame_from_http_api(self):
        try:
            resp = requests.get(url_last_frame(self._camera_id), stream=True, timeout=2).raw
        except:
            return None
        start_time = time.time()
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        if self._rotate:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if self._size is not None:
            image = cv2.resize(image, self._size)
        return image

    def update_job(self):
        while True:
            start_time = time.time()
            self.update_last_frame()
            end_time = time.time()
            sleep_time = max(0, 1/self._fps - (end_time - start_time))
            time.sleep(sleep_time)

    def start(self):
        self._thread = threading.Thread(target=self.update_job)
        self._thread.daemon = True
        self._thread.start()

class FrameReader:
    def __init__(self, camera_ids: list, camera_params: dict = {}):
        self._cameara_ids = camera_ids
        self._cameara_params = camera_params
        self._init_camera()

    def _init_camera(self):
        self._cameras = {}
        for camera_id in self._cameara_ids:
            camera_param = self._cameara_params.get(camera_id, {})
            self._cameras[camera_id] = Camera(camera_id, **camera_param)
            self._cameras[camera_id].start()

    def get_last_frames(self):
        frames = {}
        for camera_id, camera in self._cameras.items():
            last_frame = camera.last_frame()
            if last_frame is None:
                continue
            frames[camera_id] = last_frame
        return frames

if __name__ == "__main__":
    time.sleep(2)
    camera = Camera("camera-1")
    camera.start()
    img = camera.last_frame()
    cv2.imwrite("camera-1.jpg", img)