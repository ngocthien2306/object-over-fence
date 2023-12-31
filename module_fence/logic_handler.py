import time

from module_fence.base_model import LogicConfig
from system.utils import *
from system.event_handler import EventHandler, EventHandlerBase
from system.plc_controller import PLCController, PLCControllerBase
import cv2
from PIL import Image, ImageChops
from ultralytics import YOLO

class LogicHandler:
    def __init__(self, config: LogicConfig, points, camera_id) -> None:
        self._config = config
        if self._config.event_handler_config is not None:
            self._event_handler = EventHandler(self._config.event_handler_config)
        else:
            self._event_handler = EventHandlerBase(self._config.event_handler_config)
        if self._config.plc_controller_config is not None:
            self._plc_controller = PLCController(self._config.plc_controller_config)
        else:
            self._plc_controller = PLCControllerBase(self._config.plc_controller_config)

        self._model = YOLO("models/yolov8m.pt", task='detect')
        
        self._number_true_frame = 7
        self._last_event_timestamp = 0
        self._last_handle_wrong = True
        self.frame_1 = None
        self.frame_2 = None
        self._points = points
        self.colors = get_color_dict()
        self._camera_id = camera_id
        self._start_time = time.time()
        self._end_time = time.time()
        self._count_frame = 0
        self._is_clicked_alarm = False
        self.is_start_record = False
        self._video_frames = {
            'org': [],
            'frame_plot': []
        }
        self._current_fps = 0

    def fps(self, f=1.0, show=False):
        self._end_time = time.time()
        if self._end_time - self._start_time >= f:
            if show:
                print(f"{self._camera_id}: {self._count_frame} fps")
            self._start_time = self._end_time
            self._current_fps = self._count_frame
            self._count_frame = 0
            
    def show_state_record(self):
        self._end_time = time.time()
        if self._end_time - self._start_time >= 1:
            self._start_time = self._end_time
            
        print(f"{self._camera_id}: {self.is_start_record}")

    def _process_frame(self, frame1, frame2):
        inside_yn = False

        frame1 = cv2.resize(frame1, (1280, 720))
        frame2 = cv2.resize(frame2, (1280, 720))
        frame_plot = frame2.copy()

        # frame1 = remove_green(frame1)
        # frame2 = remove_green(frame2)
        
        predicts = self._model(frame_plot, verbose=False, classes=0, conf=0.4)
        
        bboxes = predicts[0].boxes.xyxy.cpu().int().tolist()
        bboxes = [[[box[0], box[1]], [box[2], box[3]]] for box in bboxes]
        
        frame_plot = predicts[0].plot()
        # cv2.imshow("frame_plot", frame_plot)
        
        diff = cv2.absdiff(frame1, frame2)

        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(diff_gray, 21)
        _, thresh = cv2.threshold(blur, 25, 255, cv2.THRESH_BINARY)

        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxs = bboxes
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            if cv2.contourArea(contour) < 1200:
                continue

            bounding_boxs.append([[int(x), int(y)], [int(x + w), int(y + h)]])

        bounding_boxs = merge_bbox(bounding_boxs, merge_margin=20)

        for i, box in enumerate(bounding_boxs):
            p1, p2 = box
            x1, y1 = p1
            x2, y2 = p2

            if check_bbox_in_poly((x1, y1, x2, y2), self._points['POINTS_2']):
                inside_yn = True
                self.is_start_record = True
                # plot_detection_result((x1, y1, x2, y2),
                #     frame_plot, (0, 0, 230),
                #     'undefined object', None)
            
            # else:
            #     plot_detection_result((x1, y1, x2, y2),
            #         frame_plot, self.colors[str(100)],
            #         'undefined object', None)

        if self._camera_id == 'camera-1':
            dilated = cv2.resize(dilated, (720, 508))
            frame1 = cv2.resize(frame1, (720, 508))
            frame2 = cv2.resize(frame2, (720, 508))
            cv2.imshow("dilated", dilated)
            cv2.imshow("frame1", frame1)
            cv2.imshow("frame2", frame2)

        key = cv2.waitKey(1)
        if key == ord('q'):
            print()

        return inside_yn, frame_plot

    def update(self, frame1, frame2):
        is_wrong, frame_plot = self._process_frame(frame1, frame2)
        
        if is_wrong:
            current_timestamp = int(time.time())
            plot_text(frame_plot, (50, 50), "DANGER: OBJECT IN FENCE", (0, 0, 255), line_width=3)
            frame_plot = draw_area(self._points['POINTS_2'], frame_plot)

            if self._last_event_timestamp != current_timestamp and self._last_handle_wrong:
                self._last_event_timestamp = current_timestamp
                self._plc_controller.turn_on()
                
                self._event_handler.update(frame2, frame_plot)
                    
                self._last_handle_wrong = False

            self._number_true_frame = 0

        else:
            self._number_true_frame += 1
            if self._number_true_frame >= 7:
                plot_text(frame_plot, (50, 50), f"SAFE", (0, 255, 0), line_width=3)
                frame_plot = draw_area(self._points['POINTS_2'], frame_plot, (18, 156, 243))
                self._plc_controller.turn_off()
                self._last_handle_wrong = True

            else:
                plot_text(frame_plot, (50, 50), "DANGER: OBJECT IN FENCE", (0, 0, 255), line_width=3)

                frame_plot = draw_area(self._points['POINTS_2'], frame_plot)

         
        videos = []
        if self.is_start_record or self._is_clicked_alarm:
            print(f'{self._camera_id} - frame number ', len(self._video_frames['org']))
            self._event_handler.fps = self._current_fps
            if len(self._video_frames['org']) <= (int(self._current_fps) * 10):
                self._video_frames['org'].append(frame2)
                self._video_frames['frame_plot'].append(frame_plot)
            else:
                videos = self._video_frames
                self._video_frames = {
                    'org': [],
                    'frame_plot': []
                }
                self.is_start_record = False
                 
        if len(videos) > 0 and self._is_clicked_alarm:
            print(f'{self._camera_id}: Done frame')
            self._event_handler.update_video(videos['org'], videos['frame_plot'])
            self._is_clicked_alarm = False
        self._event_handler.post_frame(frame_plot)

        return is_wrong, frame_plot

    def count_frame(self):
        self._count_frame += 1
        
    

    