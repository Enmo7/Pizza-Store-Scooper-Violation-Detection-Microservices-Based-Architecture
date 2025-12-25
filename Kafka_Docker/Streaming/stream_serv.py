import cv2
import pickle
import threading
import time
from kafka import KafkaConsumer
from flask import Flask, Response, render_template

app = Flask(__name__)

latest_info = {
    "frame": None,
    "violations": 0,
    "timestamp": ""
}

def kafka_listener():
    consumer = KafkaConsumer(
        "detected_frames",
        bootstrap_servers='kafka:9092',
        auto_offset_reset='latest',
        value_deserializer=lambda x: pickle.loads(x)
    )

    for msg in consumer:
        data = msg.value
        latest_info["frame"] = data['frame']
        latest_info["violations"] = data['number_of_violation']
        latest_info["timestamp"] = time.strftime(
            '%Y-%m-%d %H:%M:%S',
            time.localtime(data['timestamp'])
        )

def generate_stream():
    while True:
        frame = latest_info["frame"]
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                buffer.tobytes() + b'\r\n'
            )

@app.route('/video')
def video_feed():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def dashboard():
    return render_template(
        "index.html",
        violations=latest_info["violations"],
        timestamp=latest_info["timestamp"]
    )

if __name__ == '__main__':
    t = threading.Thread(target=kafka_listener, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
