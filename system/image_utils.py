import cv2
import numpy as np
from matplotlib import path

AREA_COLOR = (0, 0, 100)
TRANSPARENT_SCORE = 0.5
LINE_AREA_COLOR = (58, 58, 58)

def read_image(path):
    return cv2.imread(path)

def image_resize(frame, output_size=None):
    if output_size is not None:
        return cv2.resize(frame, output_size)
    return frame

def save_image(path, frame):
    cv2.imwrite(path, frame)
    
def save_video(path, frames, fps=30, size=(1920, 1080)):
    """
    Save a video from a list of frames.

    Parameters:
    - path: The path to save the video file.
    - frames: A list of frames (each frame is a NumPy array).
    - fps: Frames per second for the video (default is 30).
    - size: The size of the frames (default is 1920x1080).
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, size)
    for frame in frames:
        out.write(frame)

    out.release()
    
def image_to_bytes(frame):
    _, frame = cv2.imencode(
        ".jpg",
        frame,
        params=(cv2.IMWRITE_JPEG_QUALITY, 70),
    )
    return frame.tobytes()

def draw_area(area_config, image):
    overlay = image.copy()
    area_config_numpy = np.array(area_config)
    cv2.fillPoly(overlay, pts=[area_config_numpy], color=AREA_COLOR)
    overlay = cv2.polylines(overlay, [area_config_numpy.reshape((-1, 1, 2))], True, LINE_AREA_COLOR, 2)
    image = cv2.addWeighted(overlay, TRANSPARENT_SCORE, image, 1 - TRANSPARENT_SCORE, 0)
    return image

def plot_detection_result(box, frame, color=(0, 255, 0), label=None, txt_color=(255, 255, 255), line_width=None):
    p1, p2 = (int(box[0]), int(box[1])), (int(box[2]), int(box[3]))
    lw = line_width or int(round(0.002 * (frame.shape[0] + frame.shape[1]) / 2)) + 1  # line thickness
    cv2.rectangle(frame, p1, p2, color, thickness=lw, lineType=cv2.LINE_AA)
    if label:
        tf = max(lw - 1, 1)  # font thickness
        w, h = cv2.getTextSize(label, 0, fontScale=lw / 3, thickness=tf)[0]  # text width, height
        outside = p1[1] - h >= 3
        p2 = p1[0] + w, p1[1] - h - 3 if outside else p1[1] + h + 3
        cv2.rectangle(frame, p1, p2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(frame,
                    label, (p1[0], p1[1] - 2 if outside else p1[1] + h + 2),
                    0,
                    lw / 3,
                    txt_color,
                    thickness=tf,
                    lineType=cv2.LINE_AA)

def plot_text(frame, point, label, txt_color, line_width=None):
    lw = line_width or int(round(0.002 * (frame.shape[0] + frame.shape[1]) / 2)) + 1  # line thickness
    tf = max(lw - 1, 1)  # font thickness
    cv2.putText(frame,
                label, point,
                0,
                lw / 3,
                txt_color,
                thickness=tf,
                lineType=cv2.LINE_AA)

def check_points_in_poly(points, poly):
    # points = np.array(points)
    poly = np.array(poly)
    bbPath = path.Path(poly)
    return bbPath.contains_points(points)

def check_bbox_in_poly(bbox, poly, overlap_threshold=0.4):
    result = check_points_in_poly(bbox, poly)
    return (result.sum() / len(result)) > overlap_threshold