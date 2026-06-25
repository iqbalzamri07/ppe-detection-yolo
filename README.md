# PPE Detection System

A comprehensive Personal Protective Equipment (PPE) detection and monitoring system using FastAPI, YOLO, and real-time video analytics.

## Features

- 🎥 **Real-time Video Monitoring**: Live PPE detection on video feeds
- 📊 **Comprehensive Dashboard**: Interactive monitoring interface with real-time statistics
- 🔍 **Multi-Source Support**: Switch between different video sources (files, cameras)
- ⚠️ **Violation Alerts**: Real-time alerts for PPE non-compliance
- 📈 **Analytics**: Detailed detection statistics and compliance tracking
- 🎯 **10 PPE Classes**: Detects various PPE items and violations

## PPE Detection Classes

### Compliance Items (Green)
- Hardhat
- Mask  
- Safety Vest

### Violation Items (Red)
- NO-Hardhat
- NO-Mask
- NO-Safety Vest

### Other Items (Orange/Purple)
- Person
- Safety Cone
- Machinery
- Vehicle

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```
   CONFIDENCE=0.5
   ```

3. **Ensure video files are available:**
   Place video files in the `videos/` directory. The system will auto-discover them.

4. **Start the server:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Usage

### Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8000/dashboard
```

### API Endpoints

#### Monitoring
- `GET /dashboard` - Main monitoring dashboard
- `GET /ppe` - PPE detection video stream (current source)
- `GET /stream` - Alternative video stream
- `GET /ppe-player` - Simple video player page

#### Statistics
- `GET /api/stats` - Get real-time detection statistics
- `GET /api/stats/reset` - Reset detection statistics

#### Video Source Management
- `GET /api/video-sources` - List all available video sources
- `POST /api/video-sources/{source_id}` - Set current video source
- `POST /api/video-sources/refresh` - Refresh available sources
- `POST /api/video-sources/custom` - Add custom video source

#### System
- `GET /health` - System health check

## Dashboard Features

### Live Monitoring
- Real-time video feed with PPE detection overlays
- Video source selection dropdown
- Stream controls (restart, stop, fullscreen)
- Connection status indicator

### Statistics Panel
- **Detection Summary**: Total detections, compliance count, violations
- **Compliance Rate**: Overall PPE compliance percentage
- **Detection Trends**: Hourly detection chart
- **Recent Detections**: List of latest detections with details

### Alert System
- Real-time violation alerts
- System notifications
- Connection status updates
- Alert history

### Video Source Management
- Auto-discovery of video files in `videos/` directory
- Camera support (default camera 0)
- Custom source addition
- Source switching without server restart

## Configuration

### Model Configuration
Edit `app/core/config.py` to configure:
- `MODEL_PATH`: Path to YOLO model weights
- `CONFIDENCE`: Detection confidence threshold

### Video Sources
The system automatically discovers:
1. Camera 0 (default webcam)
2. Video files in the `videos/` directory (.mp4, .avi, .mov, etc.)

Custom sources can be added via the dashboard or API.

## Project Structure

```
ppe-detection/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   └── config.py          # Configuration management
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── services/
│   │   ├── detector.py        # YOLO detection wrapper
│   │   ├── video.py           # Video streaming service
│   │   ├── image.py           # Image processing with PPE detection
│   │   ├── stats.py           # Statistics tracking service
│   │   └── video_source_manager.py  # Video source management
│   ├── models/
│   │   └── schemas.py         # Pydantic schemas
│   └── utils/
│       └── image.py           # Image utilities
├── templates/
│   └── dashboard.html         # Main dashboard interface
├── videos/                    # Video files directory
├── weights/                   # Model weights directory
├── outputs/                   # Statistics exports
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Technical Details

### Detection Pipeline
1. Video frame capture from selected source
2. YOLO model inference on each frame
3. Class filtering and confidence thresholding
4. Bounding box annotation with color coding
5. Real-time statistics tracking
6. MJPEG stream generation for web display

### Color Coding
- **Green**: PPE compliance items
- **Red**: PPE violations
- **Orange**: Machinery and vehicles
- **Purple**: Other detected objects

### Statistics Tracking
- Total detection count
- Compliance vs violation breakdown
- Hourly detection trends
- Per-class detection counts
- Recent detection history
- Real-time compliance rate calculation

## Development

### Running in Development Mode
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Features
- Extend `app/services/` for new business logic
- Add routes in `app/api/routes.py`
- Update dashboard in `templates/dashboard.html`
- Modify configuration in `app/core/config.py`

## Performance Considerations

- Stats are updated every 10 frames to reduce overhead
- Old detections are automatically cleaned up (24 hours)
- Alerts are kept for 1 hour
- Maximum 1000 detections stored in memory
- Connection pooling for API requests

## Troubleshooting

### Video stream not loading
- Check video file exists in `videos/` directory
- Verify camera is connected and accessible
- Check browser console for errors
- Ensure model weights exist in `weights/` directory

### Statistics not updating
- Check backend console for errors
- Verify `/api/stats` endpoint is accessible
- Refresh the dashboard page
- Check network connectivity

### Detection issues
- Adjust confidence threshold in `.env` file
- Ensure correct model is being used
- Verify video quality and lighting conditions
- Check model compatibility with video format

## License

This project uses YOLO (Ultralytics) for object detection. Please refer to the respective licenses for the models and libraries used.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review API endpoint documentation
3. Verify all dependencies are installed correctly
4. Check console logs for error messages