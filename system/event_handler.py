import os.path
import time
import requests
import threading
from typing import Optional

from pydantic import BaseModel
from system.image_utils import image_resize, image_to_bytes, save_image

class EventHandlerConfig(BaseModel):
    post_frame_url: str
    post_event_url: str
    camera_id: str
    module_id: str
    msgType: int

    frame_stream_size: Optional[tuple] = None
    frame_log_size: Optional[tuple] = None
    frame_org_size: Optional[tuple] = None

class EventImageInfo(BaseModel):
    image_log_filename: str
    image_log_uri: str
    image_log_path: str

    image_org_filename: str
    image_org_uri: str
    image_org_path: str

class EventHandlerBase:
    def __init__(self, config: EventHandlerConfig):
        pass
    
    def update(self, frame_org, frame_log):
        pass

    def post_frame(self, frame):
        pass


class EventHandler(EventHandlerBase):
    def __init__(self, config: EventHandlerConfig):
        self._config = config
        self._queue = []

        self._t = threading.Thread(target=self._run)
        self._t.daemon = True
        self._t.start()

    def _get_event_image_info(self, timestamp) -> EventImageInfo:
        image_log_filename = f"{self._config.module_id}_{self._config.camera_id}_{timestamp}.jpg"
        image_log_uri = f"/public/images/{self._config.module_id}/{self._config.camera_id}/{image_log_filename}"

        image_root_path = f"C:/Users/delai/source/repos/deploy_module/logs/images/{self._config.module_id}/{self._config.camera_id}"
        if not os.path.exists(image_root_path):
            os.makedirs(image_root_path)

        image_log_path = f"{image_root_path}/{image_log_filename}"

        image_org_filename = f"{self._config.module_id}_{self._config.camera_id}_{timestamp}_org.jpg"
        image_org_uri = f"/public/images/{self._config.module_id}/{self._config.camera_id}/{image_org_filename}"
        image_org_root_path = f"C:/Users/delai/source/repos/deploy_module/logs/images/{self._config.module_id}/{self._config.camera_id}"
        if not os.path.exists(image_org_root_path):
            os.makedirs(image_org_root_path)

        image_org_path = f"{image_org_root_path}/{image_org_filename}"

        return EventImageInfo(
            image_log_filename=image_log_filename,
            image_log_uri=image_log_uri,
            image_log_path=image_log_path,
            image_org_filename=image_org_filename,
            image_org_uri=image_org_uri,
            image_org_path=image_org_path
        )
    
    def _post_event(self, timestamp, image_uri):
        event_message = {
            "camera_id": self._config.camera_id,
            "module_id": self._config.module_id,
            "timestamp": int(timestamp),
            "image_uri": image_uri,
            "msgType": self._config.msgType
        }
        requests.post(self._config.post_event_url, json=event_message, timeout=2)

    def post_frame(self, frame):
        if frame is None:
            return
        frame = image_resize(frame, self._config.frame_stream_size)
        frame_bytes = image_to_bytes(frame)
        try:
            response = requests.post(self._config.post_frame_url, data=frame_bytes, timeout=1)
        except Exception as e:
            print("Lỗi khi gửi frame:", str(e))

    def update(self, frame_org, frame_log):
        self._queue.append((frame_org, frame_log))

    def _process(self, frame_org, frame_log):
        timestamp = int(time.time())
        event_image_info = self._get_event_image_info(timestamp)

        frame_log = image_resize(frame_log, self._config.frame_log_size)
        frame_org = image_resize(frame_org, self._config.frame_org_size)

        if not self._config.post_event_url:
            return 

        # self._post_event(timestamp, event_image_info.image_log_uri)
        
        # save_image(event_image_info.image_log_path, frame_log)
        # save_image(event_image_info.image_org_path, frame_org)

    def _run(self):
        while True:
            # print("run -- len queue", len(self._queue))
            if len(self._queue) > 0:
                frame_org, frame_log = self._queue.pop(0)
                print(len(frame_org))

                self._process(frame_org[0], frame_log[0])
            time.sleep(0.02)