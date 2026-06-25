from ultralytics import YOLO
import cv2
import math
import time

def video_detection(path_x, stats_service=None):
    cap = cv2.VideoCapture(path_x)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = 1.0 / fps if fps > 0 else 0.03

    model = YOLO("weights/ppe.pt")
    classNames = ['Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 'Safety Cone',
                'Safety Vest', 'machinery', 'vehicle']
                
    frame_count = 0
                
    while True:
        success, img = cap.read()
        if not success or img is None:
            break

        results = model(img, stream=True)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])
                class_name = classNames[cls]
                label = f'{class_name} {conf}'
                
                # Track statistics if service is provided
                if stats_service and frame_count % 10 == 0:  # Update stats every 10 frames to reduce overhead
                    stats_service.add_detection(class_name, conf, (x1, y1, x2, y2))
                
                # Setup label background sizes
                t_size = cv2.getTextSize(label, 0, fontScale=0.6, thickness=1)[0]
                c2 = x1 + t_size[0], y1 - t_size[1] - 5
                
                # 1. Determine color based on class name
                if class_name in ['Mask', 'Hardhat', 'Safety Vest']:
                    color = (0, 255, 0)  # Green
                elif class_name in ['NO-Hardhat', 'NO-Mask', 'NO-Safety Vest']:
                    color = (0, 0, 255)  # Red
                elif class_name in ['machinery', 'vehicle']:
                    color = (0, 149, 255)  # Orange
                else:
                    color = (255, 0, 255)  # Purple/Default

                # 2. Only draw if confidence passes threshold (Using dynamic color!)
                if conf > 0.5:
                    # Draw bounding box
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    # Draw filled text background box
                    cv2.rectangle(img, (x1, y1), c2, color, -1, cv2.LINE_AA)
                    # Write the label text
                    cv2.putText(img, label, (x1, y1 - 3), 0, 0.6, [255, 255, 255], thickness=2, lineType=cv2.LINE_AA)

        # Encode frame to bytes for FastAPI StreamingResponse
        ret, buffer = cv2.imencode('.jpg', img)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(delay)
        frame_count += 1

    cap.release()