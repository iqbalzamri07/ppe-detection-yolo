import threading
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any
from app.database import get_db, DatabaseManager
from app.services.notifications import notification_service

class StatsService:
    """
    Enhanced statistics service with database persistence and notifications.
    """
    
    def __init__(self, use_database=True):
        self.lock = threading.Lock()
        self.use_database = use_database
        
        # In-memory statistics for fast access
        self.stats = {
            'total': 0,
            'compliance': 0,
            'violations': 0,
            'other': 0,
            'detections': [],
            'hourly_data': defaultdict(int),
            'class_counts': defaultdict(int),
            'alerts': []
        }
        
        self.compliance_classes = ['Hardhat', 'Mask', 'Safety Vest']
        self.violation_classes = ['NO-Hardhat', 'NO-Mask', 'NO-Safety Vest']
        
        # Batch insert tracking for database efficiency
        self.pending_detections = []
        self.batch_size = 50  # Insert detections in batches
        
    def start(self):
        """Placeholder for compatibility."""
        pass
    
    def stop(self):
        """Placeholder for compatibility."""
        # Flush any pending detections to database
        if self.pending_detections:
            self._flush_detections_to_db()
    
    def add_detection(self, class_name: str, confidence: float, bbox: tuple = None, video_source: str = None):
        """
        Add a new detection to the statistics with database persistence.
        """
        with self.lock:
            now = datetime.now()
            hour = now.hour
            
            detection = {
                'class': class_name,
                'confidence': round(confidence * 100, 2),
                'time': now.isoformat(),
                'hour': hour,
                'bbox': bbox,
                'video_source': video_source or 'default'
            }
            
            self.stats['total'] += 1
            self.stats['hourly_data'][hour] += 1
            self.stats['class_counts'][class_name] += 1
            
            if class_name in self.compliance_classes:
                self.stats['compliance'] += 1
                detection['type'] = 'compliance'
            elif class_name in self.violation_classes:
                self.stats['violations'] += 1
                detection['type'] = 'violation'
                self._send_violation_alert(detection)
            else:
                self.stats['other'] += 1
                detection['type'] = 'other'
            
            self.stats['detections'].insert(0, detection)
            
            # Keep only last 100 detections in memory
            if len(self.stats['detections']) > 100:
                self.stats['detections'] = self.stats['detections'][:100]
            
            # Keep only last 10 alerts in memory
            if len(self.stats['alerts']) > 10:
                self.stats['alerts'] = self.stats['alerts'][:10]
            
            # Queue for database insertion
            if self.use_database:
                self.pending_detections.append(detection)
                if len(self.pending_detections) >= self.batch_size:
                    self._flush_detections_to_db()
    
    def _flush_detections_to_db(self):
        """Flush pending detections to database."""
        if not self.pending_detections:
            return
            
        try:
            db = next(get_db())
            db_manager = DatabaseManager(db)
            db_manager.bulk_insert_detections(self.pending_detections)
            db.close()
            self.pending_detections = []
        except Exception as e:
            print(f"Error flushing detections to database: {e}")
    
    def _send_violation_alert(self, detection: Dict):
        """Send notification for PPE violations."""
        try:
            alert_data = {
                'title': f'PPE Violation: {detection["class"]}',
                'message': f'{detection["class"]} detected with {detection["confidence"]}% confidence',
                'severity': 'danger',
                'type': 'ppe_violation',
                'class_name': detection['class'],
                'confidence': detection['confidence'],
                'video_source': detection.get('video_source'),
                'time': detection['time']
            }
            
            # Add to in-memory alerts
            self.stats['alerts'].insert(0, alert_data)
            
            # Send notifications
            notification_service.send_alert(alert_data)
            
        except Exception as e:
            print(f"Error sending violation alert: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics from memory and database.
        """
        with self.lock:
            total_detections = self.stats['total']
            compliance_rate = 0
            if total_detections > 0:
                compliance_rate = round((self.stats['compliance'] / total_detections) * 100, 1)
            
            # Convert hourly_data to list format for chart
            hourly_list = [self.stats['hourly_data'][i] for i in range(24)]
            
            # Format recent detections for display
            recent_detections = [
                {
                    'class': det['class'],
                    'confidence': det['confidence'],
                    'time': datetime.fromisoformat(det['time']).strftime('%H:%M:%S'),
                    'type': det['type']
                }
                for det in self.stats['detections'][:10]
            ]
            
            return {
                'total': total_detections,
                'compliance': self.stats['compliance'],
                'violations': self.stats['violations'],
                'other': self.stats['other'],
                'compliance_rate': compliance_rate,
                'hourly_data': hourly_list,
                'recent_detections': recent_detections,
                'class_counts': dict(self.stats['class_counts']),
                'alerts': self.stats['alerts'][:5],
                'last_updated': datetime.now().isoformat()
            }
    
    def get_historical_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get historical statistics from database for the specified number of days.
        """
        if not self.use_database:
            return self.get_stats()
        
        try:
            db = next(get_db())
            db_manager = DatabaseManager(db)
            
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            stats = db_manager.get_detection_stats(
                start_date=start_date,
                end_date=end_date
            )
            
            # Get hourly data for today
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            hourly_data = db_manager.get_hourly_detection_data(date=today)
            
            db.close()
            
            return {
                **stats,
                'hourly_data': hourly_data,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except Exception as e:
            print(f"Error getting historical stats: {e}")
            return self.get_stats()
    
    def reset_stats(self):
        """
        Reset all statistics.
        """
        with self.lock:
            # Clear in-memory stats
            self.stats = {
                'total': 0,
                'compliance': 0,
                'violations': 0,
                'other': 0,
                'detections': [],
                'hourly_data': defaultdict(int),
                'class_counts': defaultdict(int),
                'alerts': []
            }
            
            # Clear pending database insertions
            self.pending_detections = []
            
            return {'message': 'Statistics reset successfully'}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics directly from database.
        """
        if not self.use_database:
            return self.get_stats()
        
        try:
            db = next(get_db())
            db_manager = DatabaseManager(db)
            
            # Get overall stats
            overall_stats = db_manager.get_detection_stats()
            
            # Get recent detections
            recent_detections = db_manager.get_recent_detections(limit=10)
            
            # Get hourly data for today
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            hourly_data = db_manager.get_hourly_detection_data(date=today)
            
            db.close()
            
            return {
                'total': overall_stats['total'],
                'compliance': overall_stats['compliance'],
                'violations': overall_stats['violations'],
                'other': overall_stats['other'],
                'compliance_rate': overall_stats['compliance_rate'],
                'avg_confidence': overall_stats['avg_confidence'],
                'hourly_data': hourly_data,
                'recent_detections': recent_detections,
                'source': 'database',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return self.get_stats()
    
    def export_daily_report(self) -> Dict[str, Any]:
        """
        Generate daily report for email summary.
        """
        try:
            stats = self.get_historical_stats(days=1)
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total': stats['total'],
                'compliance': stats['compliance'],
                'violations': stats['violations'],
                'other': stats['other'],
                'compliance_rate': stats['compliance_rate'],
                'class_counts': stats.get('class_counts', {})
            }
            
        except Exception as e:
            print(f"Error generating daily report: {e}")
            return {}