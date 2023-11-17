import traceback
from system.utils import get_computer_name, get_ipv4_address
import requests
from system.event_handler import EventHandlerConfig
from system.frame_reader import FrameReader
from system.plc_controller import PLCControllerConfig
from module_fence.base_model import LogicConfig
from module_fence.logic_handler import LogicHandler
import time
from system.utils import get_polygon_points
import cv2
from system.socket import sokect_server
import threading
import eventlet
def get_camera_ids():
    server_name = get_computer_name()
    root_url = f'http://26.30.0.242:8080/camera/{server_name}'
    res = requests.get(root_url)
    content = res.json()
    return [camera['camera_id'] for camera in content['data']['cameras']]

def main():
    dict_points = get_polygon_points()
    module_id = "motion-detections"
    camera_ids = get_camera_ids()
    server_name = get_computer_name()

    frame_reader = FrameReader(camera_ids)
    logic_handlers = {}

    for camera_id in camera_ids:
        print(f"http://{get_ipv4_address()}:8005/stream-manage/output/{module_id}-{camera_id}")
        event_handler_config = EventHandlerConfig(
            post_frame_url=f"http://{get_ipv4_address()}:8005/stream-manage/output/{module_id}-{camera_id}",
            post_event_url="http://26.30.0.242:8080/event",
            camera_id=camera_id,
            module_id=module_id,
            msgType=2,
            frame_stream_size=None,
            frame_log_size=(1280, 720),
            frame_org_size=(1280, 720)
        )
        plc_controller_config = PLCControllerConfig(
            plc_ip_address="192.168.2.150",
            plc_port=502,
            plc_address=1,
            modbus_address=8196
        )
        logic_config = LogicConfig(
            event_handler_config=event_handler_config,
            # plc_controller_config=plc_controller_config
        )
        logic_handlers[camera_id] = LogicHandler(config=logic_config, points=dict_points[camera_id], camera_id=camera_id)

        
    server_instance = sokect_server.SocketIOServer(logic_handlers)

    def run_server():
        server_instance.run()

    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    eventlet.sleep(1)
    

    frames_dict_1 = frame_reader.get_last_frames()
    frames_dict_2 = frame_reader.get_last_frames()
    start_time = time.time()

    while True:
        try:
            for frame_dict1, frame_dict2 in zip(frames_dict_1.items(), frames_dict_2.items()):

                key1, value1 = frame_dict1
                key2, value2 = frame_dict2

                logic_handlers[key1].update(value1, value2)
                logic_handlers[key1].count_frame()
                logic_handlers[key1].show_state_record()
                logic_handlers[key1].fps()

            frames_dict_2 = frame_reader.get_last_frames()
            end_time = time.time()
            n_time = 1
            if end_time - start_time > n_time:
                start_time = end_time
                frames_dict_1 = frames_dict_2

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        except:
            traceback.print_exc()
            continue

    cv2.destroyAllWindows()