from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi import FastAPI
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import os

from app.services.video import VideoStreamService
from app.services.image import video_detection
from app.services.stats import StatsService
from app.services.video_source_manager import video_source_manager
from app.services.notifications import notification_service
from app.database import get_db, DatabaseManager
from sqlalchemy.orm import Session
import threading

router = APIRouter()

# Initialize stats service with database support
stats_service = StatsService(use_database=True)

# Pydantic models for API requests
class EmailConfig(BaseModel):
    enabled: bool
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str
    sender_password: str
    use_tls: bool = True

class WebhookConfig(BaseModel):
    enabled: bool
    webhook_url: str
    timeout: int = 10

class TestAlertRequest(BaseModel):
    title: str = "Test Alert"
    message: str = "This is a test alert from the PPE detection system"
    severity: str = "info"

@router.get('/health')
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "notifications": "enabled" if notification_service else "disabled"
    }

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Serves the comprehensive PPE detection dashboard."""
    with open("templates/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

# Statistics endpoints
@router.get("/api/stats")
def get_stats():
    """Returns real-time PPE detection statistics."""
    return stats_service.get_stats()

@router.get("/api/stats/historical")
def get_historical_stats(days: int = 7):
    """Returns historical statistics from database."""
    try:
        return stats_service.get_historical_stats(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/stats/database")
def get_database_stats():
    """Returns statistics directly from database."""
    try:
        return stats_service.get_database_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/stats/reset")
def reset_stats():
    """Resets the detection statistics."""
    return stats_service.reset_stats()

@router.get("/api/stats/export")
def export_stats(db: Session = Depends(get_db)):
    """Export detection statistics as JSON."""
    try:
        db_manager = DatabaseManager(db)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        stats = db_manager.get_detection_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        return JSONResponse(
            content={
                "export_date": datetime.now().isoformat(),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "statistics": stats
            },
            headers={
                "Content-Disposition": "attachment; filename=ppe_stats_export.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Video source management endpoints
@router.get("/api/video-sources")
def get_video_sources():
    """Get all available video sources."""
    return {
        "sources": video_source_manager.get_sources(),
        "current_source": video_source_manager.get_current_source()
    }

@router.post("/api/video-sources/{source_id}")
def set_video_source(source_id: str):
    """Set the current video source."""
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
    """Refresh the list of available video sources."""
    video_source_manager.refresh_sources()
    return {
        "message": "Video sources refreshed",
        "sources": video_source_manager.get_sources()
    }

@router.post("/api/video-sources/custom")
def add_custom_source(source_id: str, name: str, path: str, source_type: str = "custom"):
    """Add a custom video source."""
    success = video_source_manager.add_custom_source(source_id, name, path, source_type)
    if success:
        return {
            "message": f"Custom video source {source_id} added",
            "sources": video_source_manager.get_sources()
        }
    else:
        raise HTTPException(status_code=400, detail=f"Source ID {source_id} already exists")

# Database management endpoints
@router.get("/api/database/stats")
def get_database_statistics(db: Session = Depends(get_db)):
    """Get database statistics and information."""
    try:
        db_manager = DatabaseManager(db)
        
        # Get overall stats
        overall_stats = db_manager.get_detection_stats()
        
        # Get recent activity
        recent_detections = db_manager.get_recent_detections(limit=5)
        
        return {
            "database_status": "connected",
            "statistics": overall_stats,
            "recent_activity": recent_detections,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/database/detections")
def get_detections(
    limit: int = 50,
    offset: int = 0,
    video_source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get detection records with pagination."""
    try:
        db_manager = DatabaseManager(db)
        detections = db_manager.get_recent_detections(limit=limit, video_source=video_source)
        
        return {
            "count": len(detections),
            "limit": limit,
            "offset": offset,
            "detections": detections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/database/cleanup")
def cleanup_database(days: int = 30, db: Session = Depends(get_db)):
    """Clean up old detection records."""
    try:
        db_manager = DatabaseManager(db)
        deleted_count = db_manager.cleanup_old_detections(days_to_keep=days)
        
        return {
            "message": f"Cleaned up {deleted_count} detection records older than {days} days",
            "deleted_count": deleted_count,
            "days_kept": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Notification management endpoints
@router.get("/api/notifications/config")
def get_notification_config():
    """Get current notification configuration."""
    return {
        "email": {
            "enabled": notification_service.email_config['enabled'],
            "smtp_server": notification_service.email_config['smtp_server'],
            "smtp_port": notification_service.email_config['smtp_port'],
            "use_tls": notification_service.email_config['use_tls'],
            "sender_configured": bool(notification_service.email_config['sender_email'])
        },
        "webhook": {
            "enabled": notification_service.webhook_config['enabled'],
            "timeout": notification_service.webhook_config['timeout'],
            "url_configured": bool(os.getenv('WEBHOOK_URL', ''))
        },
        "timestamp": datetime.now().isoformat()
    }

@router.post("/api/notifications/test")
def test_notification(request: TestAlertRequest):
    """Send a test notification."""
    try:
        alert_data = {
            'title': request.title,
            'message': request.message,
            'severity': request.severity,
            'type': 'test',
            'time': datetime.now().isoformat()
        }
        
        notification_service.send_alert(alert_data)
        
        return {
            "message": "Test notification sent successfully",
            "alert_data": alert_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

@router.post("/api/notifications/daily-summary")
def send_daily_summary():
    """Generate and send daily summary report."""
    try:
        import os
        recipients = os.getenv('SUMMARY_EMAILS', '').split(',')
        recipients = [email.strip() for email in recipients if email.strip()]
        
        if not recipients:
            raise HTTPException(status_code=400, detail="No email recipients configured")
        
        daily_report = stats_service.export_daily_report()
        
        if not daily_report:
            raise HTTPException(status_code=404, detail="No data available for daily report")
        
        notification_service.send_daily_summary(daily_report, recipients)
        
        return {
            "message": f"Daily summary sent to {len(recipients)} recipients",
            "recipients": recipients,
            "report_date": daily_report['date']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Video streaming endpoints
@router.get("/stream")
def video_stream():
    """Streams the live PPE detection directly into your web browser using current video source."""
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
    """Serves a simple web page that embeds the live video stream."""
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
    """The actual raw video byte stream using current video source."""
    source_path = video_source_manager.get_current_source_path()
    if not source_path:
        raise HTTPException(status_code=404, detail="No video source available")
    
    # Convert string '0' to integer for camera
    source = 0 if source_path == '0' else source_path
    
    return StreamingResponse(
        video_detection(path_x=source, stats_service=stats_service),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )