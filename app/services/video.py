import cv2
from app.services.detector import Detector

class VideoStreamService:
    def __init__(self, source=0):
        self.source = source
        self.detector = Detector()

    def generate_frames(self):
        """Generates processed video frames as bytes for a web stream."""
        cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            print(f"Error: Could not open video source {self.source}")
            return

        while True:
            success, frame = cap.read()
            if not success:
                break

            # Process frame with YOLO
            results = self.detector.detect(frame)
            annotated_frame = results[0].plot()

            # Encode the frame as a JPEG image
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()

            # Yield the frame in a format the browser understands (MJPEG)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        cap.release()