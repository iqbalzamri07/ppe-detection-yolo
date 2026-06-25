from pathlib import Path
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = BASE_DIR / "weights" / "yolo11n.pt"

load_dotenv()
CONFIDENCE = float(
    os.getenv("CONFIDENCE", 0.5)
)
