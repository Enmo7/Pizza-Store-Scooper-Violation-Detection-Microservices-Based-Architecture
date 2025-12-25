# Pizza-Store-Scooper-Violation-Detection-Microservices-Based-Architecture

## 📌 Overview

This project implements a Computer Vision–based hygiene monitoring system for a pizza store.
The system detects whether workers use a scooper when handling ingredients from predefined Regions of Interest (ROIs).
If a hand touches the pizza without a scooper, the action is flagged as a violation.

The project was implemented using a microservices architecture and evolved through multiple deployment and messaging strategies:

*   RabbitMQ (with & without Docker)
*   Apache Kafka (with & without Docker)

## 🧠 Core Algorithm (Violation Detection Logic)

### 🔹 High-Level Logic

The system does not rely on single-frame detection.
Instead, it tracks object behavior over time to avoid false positives.

### 🔹 Objects Detected

*   Hand
*   Scooper
*   Pizza

Using YOLOv8 + Object Tracking (ByteTrack / DeepSORT).

### 🔹 ROI-Based Sequential Logic

The user manually selects ROI areas at the beginning of the video.
ROIs represent ingredient containers.
Each ROI is defined as (x, y, width, height).

For each frame:

1.  Detect hands, scoopers, and pizza.
2.  Track each hand with a unique ID.
3.  For each tracked hand:
    *   Check if it entered an ROI.
    *   Check if it later reached the pizza area.
    *   Check if a scooper was close to the hand.

A violation is detected only if:

*   Hand entered ROI
*   Hand moved to pizza
*   No scooper detected nearby

When a violation occurs:

*   Frame snapshot is saved.
*   Violation is logged in SQLite database.
*   Hand bounding box is highlighted in red.

### 🔹 Rectangle Intersection Logic

Two rectangles overlap if:

*   A.x < B.x + B.w
*   A.x + A.w > B.x
*   A.y < B.y + B.h
*   A.y + A.h > B.y

This ensures accurate ROI and pizza-area detection.

## 🗂 Project Structure

```
src/
├── readframes/
│   ├── collect_read_fram.py
│   └── fram_read.py
│
├── DetectionAndViolation/
│   ├── detect_serv.py
│   ├── hand_violation_tracker.py
│   └── roi.py
│
├── Streaming/
│   ├── stream_serv.py
│   └── templates/
│       └── index.html
│
├── models/
├── dataset/
```

## 🧩 Architecture Variants

### 🔴 1. RabbitMQ Architecture (Without Docker)

**Architecture Flow**
Frame Reader
   ↓ (RabbitMQ queue: video_frames)
Detection Service
   ↓ (RabbitMQ queue: detected_frames)
Streaming Service → Browser

**Description**
RabbitMQ installed locally.
`pika` library used for publishing and consuming messages.
Services run in separate terminals.

**How to Run**
```bash
python collect_read_fram.py
python detect_serv.py
python stream_serv.py
```

### 🔴 2. RabbitMQ Architecture (With Docker)

**Architecture Flow**
Frame Reader (Container)
   ↓
RabbitMQ (Container)
   ↓
Detection Service (Container)
   ↓
Streaming Service (Container)

**Key Features**
RabbitMQ + services containerized.
Docker internal networking.
Same logic, same queues.

**Run**
```bash
docker compose up
```

### 🔵 3. Kafka Architecture (Without Docker)

**Architecture Flow**
Frame Reader
   ↓ (Kafka topic: video_frames)
Detection Service
   ↓ (Kafka topic: detected_frames)
Streaming Service → Browser

**Description**
Kafka + Zookeeper installed locally.
`kafka-python` used for Producer & Consumer.
Topics replace RabbitMQ queues.

**Topics**
*   `video_frames`
*   `detected_frames`

**Run Order**
```bash
python collect_read_fram.py
python detect_serv.py
python stream_serv.py
```

### 🔵 4. Kafka Architecture (With Docker) ✅ (Final Version)

**Architecture Flow**
Frame Reader (Container)
   ↓
Kafka Broker (Container)
   ↓
Detection Service (Container)
   ↓
Streaming Service (Container)
   ↓
Browser UI

**Dockerized Services**
*   Zookeeper
*   Kafka
*   Frame Reader
*   Detection Service
*   Streaming Service

**Benefits**
*   High throughput
*   Scalable
*   Environment independent
*   Production-ready

**Run**
```bash
docker compose build
docker compose up
```

**Access:**
`http://localhost:5000`

## 🗃 Violation Logging (SQLite)

Each violation record includes:

*   Frame path
*   Timestamp
*   Hand ID
*   Violation label (`missing_scooper`)
*   Bounding box coordinates

Database auto-initializes on service start.

## 📊 RabbitMQ vs Kafka (Summary)

| Feature | RabbitMQ | Kafka |
| :--- | :--- | :--- |
| Model | Queue | Log / Topic |
| Throughput | Medium | High |
| Replay Messages | ❌ | ✅ |
| Scalability | Limited | High |
| Video Streaming | ⚠️ | ✅ |

## ✅ Conclusion

RabbitMQ was ideal for early prototyping.
Kafka provided better scalability and performance.
Docker enabled reproducible and clean deployments.
Core detection logic remained unchanged across all variants.
