import cv2
import time
import pickle
from kafka import KafkaProducer

class read_frames:
    def __init__(self, path_video):
        self.path_video = path_video

        self.producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: pickle.dumps(v)
        )

    def read(self):
        cap = cv2.VideoCapture(self.path_video)
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            message = {
                'frame': frame,
                'frame_number': frame_count,
                'timestamp': time.time()
            }

            self.producer.send("video_frames", message)
            print(f"Sent frame {frame_count}")

            frame_count += 1

        cap.release()
        self.producer.flush()
        print("Frame reader finished sending all frames")