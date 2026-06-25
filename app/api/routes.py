from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi import FastAPI
from app.services.video import VideoStreamService
from app.services.image import video_detection
from app.services.stats import StatsService
from app.services.video_source_manager import video_source_manager
import threading

router = APIRouter()

# Initialize stats service
stats_service = StatsService()
stats_service.start()

@router.get('/health')
def health():
    return {"status": "ok"}

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """
    Serves the comprehensive PPE detection dashboard.
    """
    with open("templates/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@router.get("/api/stats")
def get_stats():
    """
    Returns real-time PPE detection statistics.
    """
    return stats_service.get_stats()

@router.get("/api/stats/reset")
def reset_stats():
    """
    Resets the detection statistics.
    """
    return stats_service.reset_stats()

@router.get("/api/video-sources")
def get_video_sources():
    """
    Get all available video sources.
    """
    return {
        "sources": video_source_manager.get_sources(),
        "current_source": video_source_manager.get_current_source()
    }

@router.post("/api/video-sources/{source_id}")
def set_video_source(source_id: str):
    """
    Set the current video source.
    """
    success = video_source_manager.set_current_source(source_id)
    if success:
        return {
            "message": f"Video source changed to {source_id}",
            "current_source": video_source_manager.get_current_source()
        }
    else:
        raise HTTPException(status_code=404, detail=f"Video source {source_id} not found")

@router.post("/api/video-sources/refresh")
def refresh_video_sources():
    """
    Refresh the list of available video sources.
    """
    video_source_manager.refresh_sources()
    return {
        "message": "Video sources refreshed",
        "sources": video_source_manager.get_sources()
    }

@router.post("/api/video-sources/custom")
def add_custom_source(source_id: str, name: str, path: str, source_type: str = "custom"):
    """
    Add a custom video source.
    """
    success = video_source_manager.add_custom_source(source_id, name, path, source_type)
    if success:
        return {
            "message": f"Custom video source {source_id} added",
            "sources": video_source_manager.get_sources()
        }
    else:
        raise HTTPException(status_code=400, detail=f"Source ID {source_id} already exists")

@router.get("/stream")
def video_stream():
    """
    Streams the live PPE detection directly into your web browser using current video source.
    """
    source_path = video_source_manager.get_current_source_path()
    if not source_path:
        raise HTTPException(status_code=404, detail="No video source available")
    
    # Convert string '0' to integer for camera
    source = 0 if source_path == '0' else source_path
    
    stream_service = VideoStreamService(source=source)
    
    return StreamingResponse(
        stream_service.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get('/ppe-player', response_class=HTMLResponse)
def ppe_player():
    """
    Serves a simple web page that embeds the live video stream.
    """
    html_content = """
    <html>
        <head>
            <title>PPE Detection Live Video</title>
            <style>
                body { background-color: #1a1a1a; color: white; font-family: sans-serif; text-align: center; padding-top: 50px; }
                .video-container { margin: 0 auto; max-width: 800px; border: 4px solid #333; border-radius: 8px; overflow: hidden; }
                img { width: 100%; height: auto; display: block; }
            </style>
        </head>
        <body>
            <h2>PPE Detection Video Feed</h2>
            <div class="video-container">
                <img src="/ppe" />
            </div>
            <p>Playing: <span id="sourceName">Loading...</span></p>
            <script>
                fetch('/api/video-sources')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('sourceName').textContent = 
                            data.current_source ? data.current_source.name : 'Unknown';
                    });
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get('/ppe')
def ppe():
    """
    The actual raw video byte stream using current video source.
    """
    source_path = video_source_manager.get_current_source_path()
    if not source_path:
        raise HTTPException(status_code=404, detail="No video source available")
    
    # Convert string '0' to integer for camera
    source = 0 if source_path == '0' else source_path
    
    return StreamingResponse(
        video_detection(path_x=source, stats_service=stats_service),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )