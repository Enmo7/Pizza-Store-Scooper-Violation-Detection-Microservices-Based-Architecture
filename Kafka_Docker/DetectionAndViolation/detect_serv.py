import cv2
import pickle
import time
from kafka import KafkaConsumer, KafkaProducer
from ultralytics import YOLO

from hand_violation_tracker import process_frame, violations, ROI_LIST, PIZZA_AREA
from roi import ROI
from violation_database import init_db, save_violation


class Detect:
    def __init__(self, yolo_path):
        self.model = YOLO(yolo_path)

        self.consumer = KafkaConsumer(
            "video_frames",
            bootstrap_servers='kafka:9092',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda x: pickle.loads(x)
        )

        self.producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: pickle.dumps(v)
        )

    def frame_detect(self):
        init_db()

        print("Waiting for first frame to select ROI...")
        for msg in self.consumer:
            frame = msg.value['frame']
            roi_tool = ROI(frame)
            roi_list = roi_tool.pound_inters()
            ROI_LIST.clear()
            ROI_LIST.extend(roi_list)
            print(f"ROI Selected: {ROI_LIST}")
            break

        for msg in self.consumer:
            data = msg.value
            frame = data['frame']

            results = self.model.track(source=frame, persist=True, tracker="bytetrack.yaml")[0]

            tracked_hand = []
            tracked_scooper = []
            tracked_pizza = []

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = results.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                box_coords = (x1, y1, w, h)

                if not hasattr(box, 'id'):
                    continue
                object_id = int(box.id[0])

                if label == "hand":
                    tracked_hand.append((object_id, box_coords))
                elif label == "scooper":
                    tracked_scooper.append((object_id, box_coords))
                elif label == "pizza":
                    tracked_pizza.append((object_id, box_coords))

            PIZZA_AREA.clear()
            for _, pizza_box in tracked_pizza:
                PIZZA_AREA.append(pizza_box)

            violation_count, violation_found = process_frame(
                tracked_hands=tracked_hand,
                tracked_scoopers=tracked_scooper
            )

            for hand_id, hand_box in violation_found:
                save_violation(frame, hand_id, hand_box)

            send_data = {
                'frame': frame,
                'timestamp': time.time(),
                'number_of_violation': violation_count
            }

            self.producer.send("detected_frames", send_data)
