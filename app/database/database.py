from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.database.models import Base
import os
from pathlib import Path
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ppe_detection.db")

# Create database directory if it doesn't exist
db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
if db_path.exists():
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """
    Dependency for getting database sessions.
    Usage in FastAPI routes:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def reset_db():
    """Drop all tables and recreate them (WARNING: Deletes all data)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

class DatabaseManager:
    """Helper class for common database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def bulk_insert_detections(self, detections_data):
        """Bulk insert detection records for performance."""
        from app.database.models import Detection
        
        detections = [
            Detection(
                class_name=data['class'],
                confidence=data['confidence'],
                detection_type=data['type'],
                video_source=data.get('video_source'),
                bbox=data.get('bbox'),
                timestamp=datetime.fromisoformat(data['time']) if isinstance(data['time'], str) else data['time'],
                hour=datetime.fromisoformat(data['time']).hour if isinstance(data['time'], str) else data['time'].hour
            )
            for data in detections_data
        ]
        
        self.db.bulk_save_objects(detections)
        self.db.commit()
        
    def get_detection_stats(self, start_date=None, end_date=None, video_source=None):
        """Get aggregated detection statistics."""
        from app.database.models import Detection
        from sqlalchemy import func, and_
        
        query = self.db.query(
            func.count(Detection.id).label('total'),
            func.sum(func.case([(Detection.detection_type == 'compliance', 1)], else_=0)).label('compliance'),
            func.sum(func.case([(Detection.detection_type == 'violation', 1)], else_=0)).label('violations'),
            func.sum(func.case([(Detection.detection_type == 'other', 1)], else_=0)).label('other'),
            func.avg(Detection.confidence).label('avg_confidence')
        )
        
        # Apply filters
        filters = []
        if start_date:
            filters.append(Detection.timestamp >= start_date)
        if end_date:
            filters.append(Detection.timestamp <= end_date)
        if video_source:
            filters.append(Detection.video_source == video_source)
        
        if filters:
            query = query.filter(and_(*filters))
        
        result = query.first()
        
        return {
            'total': result.total or 0,
            'compliance': result.compliance or 0,
            'violations': result.violations or 0,
            'other': result.other or 0,
            'avg_confidence': float(result.avg_confidence) if result.avg_confidence else 0.0,
            'compliance_rate': (result.compliance / result.total * 100) if result.total else 0.0
        }
    
    def get_hourly_detection_data(self, date=None):
        """Get hourly detection counts for a specific date."""
        from app.database.models import Detection
        from sqlalchemy import func, extract
        
        query = self.db.query(
            extract('hour', Detection.timestamp).label('hour'),
            func.count(Detection.id).label('count')
        )
        
        if date:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(
                Detection.timestamp >= start_of_day,
                Detection.timestamp <= end_of_day
            )
        
        results = query.group_by(extract('hour', Detection.timestamp)).all()
        
        # Create 24-hour array
        hourly_data = [0] * 24
        for hour, count in results:
            hourly_data[int(hour)] = count
        
        return hourly_data
    
    def get_recent_detections(self, limit=10, video_source=None):
        """Get recent detection records."""
        from app.database.models import Detection
        
        query = self.db.query(Detection).order_by(Detection.timestamp.desc())
        
        if video_source:
            query = query.filter(Detection.video_source == video_source)
        
        detections = query.limit(limit).all()
        
        return [
            {
                'id': d.id,
                'class': d.class_name,
                'confidence': d.confidence,
                'type': d.detection_type,
                'time': d.timestamp.strftime('%H:%M:%S'),
                'video_source': d.video_source,
                'bbox': d.bbox
            }
            for d in detections
        ]
    
    def cleanup_old_detections(self, days_to_keep=30):
        """Remove detection records older than specified days."""
        from app.database.models import Detection
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted = self.db.query(Detection).filter(
            Detection.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted
    
    def create_alert(self, title, message, severity, alert_type, detection_id=None):
        """Create a new alert record."""
        from app.database.models import Alert
        
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            alert_type=alert_type,
            detection_id=detection_id
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        return alert

# Initialize database on import
try:
    init_db()
except Exception as e:
    print(f"Database initialization error: {e}")