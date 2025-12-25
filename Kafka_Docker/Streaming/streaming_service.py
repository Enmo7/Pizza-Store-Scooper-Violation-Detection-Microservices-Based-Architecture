import cv2
import pickle
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    "detected_frames",
    bootstrap_servers='kafka:9092',
    auto_offset_reset='latest',
    value_deserializer=lambda x: pickle.loads(x)
)

print("Streaming service running...")

for msg in consumer:
    data = msg.value
    frame = data['frame']

    cv2.imshow("Object Detection after", frame)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
