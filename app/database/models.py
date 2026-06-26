from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    alert_preferences = relationship("AlertPreference", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")

class Detection(Base):
    """PPE detection record with full details."""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    detection_type = Column(String(20), nullable=False)  # compliance, violation, other
    video_source = Column(String(100))
    frame_number = Column(Integer)
    bbox = Column(JSON)  # Bounding box coordinates [x1, y1, x2, y2]
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    hour = Column(Integer, index=True)  # Hour of day (0-23)
    date = Column(DateTime, index=True)  # Date for daily aggregations
    
    # Additional metadata
    model_version = Column(String(50))
    processing_time = Column(Float)  # Inference time in milliseconds

class Alert(Base):
    """Alert records for PPE violations and system events."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, danger, critical
    alert_type = Column(String(50))  # ppe_violation, system_error, performance_warning
    source = Column(String(50))  # detection, system, user
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Related detection (if applicable)
    detection_id = Column(Integer, ForeignKey("detections.id"))
    detection = relationship("Detection", backref="alerts")

class AlertPreference(Base):
    """User notification preferences."""
    __tablename__ = "alert_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="alert_preferences")
    
    # Email settings
    email_enabled = Column(Boolean, default=False)
    email_address = Column(String(100))
    email_violations = Column(Boolean, default=True)
    email_system_alerts = Column(Boolean, default=True)
    email_daily_summary = Column(Boolean, default=False)
    
    # Webhook settings
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(String(500))
    webhook_events = Column(JSON)  # List of event types to send
    
    # Notification thresholds
    min_severity = Column(String(20), default="warning")  # Minimum severity to notify
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))  # HH:MM format
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(Base):
    """User activity and system event logging."""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="activity_logs")
    
    action = Column(String(100), nullable=False)  # login, logout, reset_stats, change_source
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class VideoSource(Base):
    """Configured video sources."""
    __tablename__ = "video_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source_type = Column(String(20), nullable=False)  # camera, file, url, rtsp
    source_path = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    location = Column(String(200))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemConfig(Base):
    """System configuration and settings."""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, integer, boolean, json
    description = Column(Text)
    category = Column(String(50))  # general, detection, alerts, performance
    is_sensitive = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DetectionSummary(Base):
    """Aggregated detection statistics for performance."""
    __tablename__ = "detection_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    hour = Column(Integer, index=True)
    video_source = Column(String(100), index=True)
    
    # Counters
    total_detections = Column(Integer, default=0)
    compliance_count = Column(Integer, default=0)
    violation_count = Column(Integer, default=0)
    other_count = Column(Integer, default=0)
    
    # Class breakdowns
    class_counts = Column(JSON)  # {"Hardhat": 10, "NO-Hardhat": 5, ...}
    
    # Performance metrics
    avg_confidence = Column(Float)
    avg_processing_time = Column(Float)
    max_processing_time = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)