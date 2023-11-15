import json
import numpy as np
import cv2
from matplotlib import path
import socket

TRANSPARENT_SCORE = 0.3
LINE_AREA_COLOR = (94, 73, 52)

def get_ipv4_address():
    hostname = socket.gethostname()
    ipv4_address = socket.gethostbyname(hostname)
    return ipv4_address

def get_computer_name():
    computer_name = socket.gethostname()
    return computer_name

def get_color_dict():
    import os
    with open('system/assets/color_dict.json', 'r') as json_file:
        loaded_color_dict = json.load(json_file)
    return loaded_color_dict


# returns true if the two boxes overlap
def overlap(source, target):
    # unpack points
    """
        tl: top left
        br: bottom right
    """
    tl1, br1 = source
    tl2, br2 = target

    # checks
    if (tl1[0] >= br2[0] or tl2[0] >= br1[0]):
        return False
    if (tl1[1] >= br2[1] or tl2[1] >= br1[1]):
        return False
    return True


# returns all overlapping boxes
def getAllOverlaps(boxes, bounds, index):
    """
        Return list index bbox overlap with bounds
    """
    overlaps = []
    for a in range(len(boxes)):
        if a != index:
            if overlap(bounds, boxes[a]):
                overlaps.append(a)
    return overlaps


def merge_bbox(boxes, merge_margin=5):
    # this is gonna take a long time
    finished = False
    while not finished:
        # set end con
        finished = True
        # check progress

        index = 0
        while index < len(boxes):
            # grab current box
            curr = boxes[index]

            # add margin
            tl = curr[0][:]
            br = curr[1][:]
            tl[0] -= merge_margin
            tl[1] -= merge_margin
            br[0] += merge_margin
            br[1] += merge_margin

            # get matching boxes
            overlaps = getAllOverlaps(boxes, [tl, br], index)

            # check if empty
            if len(overlaps) > 0:
                # combine boxes
                # convert to a contour
                con = []
                overlaps.append(index)
                for ind in overlaps:
                    tl, br = boxes[ind]
                    con.append([tl])
                    con.append([br])
                con = np.array(con)

                # get bounding rect
                x, y, w, h = cv2.boundingRect(con)

                # stop growing
                w -= 1
                h -= 1
                merged = [[x, y], [x + w, y + h]]

                # remove boxes from list
                overlaps.sort(reverse=True)
                for ind in overlaps:
                    del boxes[ind]
                boxes.append(merged)

                # set flag
                finished = False
                break

            # increment
            index += 1
    return boxes

def non_max_suppression(boxes, threshold):
    if len(boxes) == 0:
        return []

    # Sort the bounding boxes by their areas in descending order.
    sorted_indices = sorted(range(len(boxes)), key=lambda i: (boxes[i][2] - boxes[i][0]) * (boxes[i][3] - boxes[i][1]),
                            reverse=True)

    selected_indices = []
    while len(sorted_indices) > 0:
        # Select the bounding box with the largest area.
        best_idx = sorted_indices[0]
        selected_indices.append(best_idx)

        # Compute IoU (Intersection over Union) with the best bounding box.
        best_box = boxes[best_idx]
        other_indices = []
        for idx in sorted_indices[1:]:
            try:
                box = boxes[idx]
                intersection = (
                    max(best_box[0], box[0]),
                    max(best_box[1], box[1]),
                    min(best_box[2], box[2]),
                    min(best_box[3], box[3])
                )
                w = max(0, intersection[2] - intersection[0])
                h = max(0, intersection[3] - intersection[1])
                intersection_area = w * h

                area1 = (best_box[2] - best_box[0]) * (best_box[3] - best_box[1])
                area2 = (box[2] - box[0]) * (box[3] - box[1])
                union_area = area1 + area2 - intersection_area

                iou = intersection_area / union_area

                if iou <= threshold:
                    other_indices.append(idx)
            except:
                continue

        sorted_indices = other_indices

    selected_bboxes = [boxes[i] for i in selected_indices]
    return selected_bboxes


def calculate_distance(box1, box2):
    # Calculate the Euclidean distance between the centers of two bounding boxes.
    center1 = ((box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2)
    center2 = ((box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2)
    return np.sqrt((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2)


def merge_n_nearest_boxes_by_distance(boxes, n, distance_threshold):
    # Calculate distances between the centers of all pairs of boxes.
    distances = np.zeros((len(boxes), len(boxes)))
    for i in range(len(boxes)):
        for j in range(len(boxes)):
            if i != j:
                dist = calculate_distance(boxes[i], boxes[j])
                distances[i][j] = dist

    # Find the n nearest boxes for each box.
    merged_boxes = []
    for i in range(len(boxes)):
        nearest_indices = np.argsort(distances[i])[:n]

        # Merge the n nearest boxes based on the distance threshold.
        merged_box = merge_boxes_by_distance(boxes[i], [boxes[j] for j in nearest_indices], distance_threshold)
        merged_boxes.append(merged_box)

    return merged_boxes


def merge_boxes_by_distance(main_box, other_boxes, distance_threshold):
    # Merge the main box with other boxes if their center distance is below the threshold.
    merged_box = main_box
    for box in other_boxes:
        dist = calculate_distance(merged_box, box)
        if dist <= distance_threshold:
            merged_box = (
                min(merged_box[0], box[0]),
                min(merged_box[1], box[1]),
                max(merged_box[2], box[2]),
                max(merged_box[3], box[3])
            )
    return merged_box


def check_points_in_poly(points, poly):
    bbPath = path.Path(poly)
    points = np.array(points).reshape(1, 2)
    return bbPath.contains_points(points)


def check_bbox_in_poly(bbox, polygon, threshold=0):
    x1, y1, x2, y2 = bbox
    return check_points_in_poly((x1, y1), polygon) or check_points_in_poly((x2, y2), polygon)


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


def plot_detection_result(box, frame, color=(0, 255, 0), label=None, conf=0, txt_color=(255, 255, 255),
                          line_width=None):
    p1, p2 = (int(box[0]), int(box[1])), (int(box[2]), int(box[3]))
    lw = line_width or int(round(0.002 * (frame.shape[0] + frame.shape[1]) / 2)) + 1  # line thickness
    cv2.rectangle(frame, p1, p2, color, thickness=1, lineType=cv2.LINE_AA)
    if label:
        tf = max(lw - 1, 1)  # font thickness
        #  + ' ' + str(round(100 * conf,2)
        w, h = cv2.getTextSize(label, 0, fontScale=lw / 3, thickness=tf)[0]  # text width, height
        outside = p1[1] - h >= 3
        p2 = p1[0] + w, p1[1] - h - 3 if outside else p1[1] + h + 3
        cv2.rectangle(frame, p1, p2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(frame,
                    label, (p1[0], p1[1] - 2 if outside else p1[1] + h + 2),
                    0,
                    lw / 3,
                    txt_color,
                    thickness=1,
                    lineType=cv2.LINE_AA)


def draw_area(area_config, image, color=(60, 76, 231)):
    overlay = image.copy()
    area_config_numpy = np.array(area_config)
    cv2.fillPoly(overlay, pts=[area_config_numpy], color=color)
    overlay = cv2.polylines(overlay, [area_config_numpy.reshape((-1, 1, 2))], True, LINE_AREA_COLOR, 2)
    image = cv2.addWeighted(overlay, TRANSPARENT_SCORE, image, 1 - TRANSPARENT_SCORE, 0)
    return image


def get_polygon_points():
    points_dict = {
        "camera-1": {
            'POINTS_1': [[3, 484], [849, 73], [880, 202], [114, 718], [5, 490]],
            'POINTS_2': [[866, 4], [888, 206], [153, 717], [5, 716], [5, 6], [864, 5]]
        },
        "camera-2": {
            'POINTS_1': [[3, 484], [849, 73], [880, 202], [114, 718], [5, 490]],
            'POINTS_2': [[866, 4], [888, 206], [153, 717], [5, 716], [5, 6], [864, 5]]
        },
        "camera-3": {
            'POINTS_1': [[3, 484], [849, 73], [880, 202], [114, 718], [5, 490]],
            'POINTS_2': [[866, 4], [888, 206], [153, 717], [5, 716], [5, 6], [864, 5]]
        },
        "camera-4": {
            'POINTS_1': [[3, 484], [849, 73], [880, 202], [114, 718], [5, 490]],
            'POINTS_2': [[866, 4], [888, 206], [153, 717], [5, 716], [5, 6], [864, 5]]
        }
    }
    return points_dict
