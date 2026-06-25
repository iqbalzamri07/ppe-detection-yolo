from ultralytics import YOLO
from app.core.config import MODEL_PATH
import cv2

class Detector:

    def __init__(self):
        self.model = YOLO(str(MODEL_PATH))

    def detect(self, frame):
        return self.model(frame, classes=[0], conf=0.6)