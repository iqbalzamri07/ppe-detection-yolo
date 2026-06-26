import threading
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any

class StatsService:
    """
    Simplified statistics service for PPE detection system.
    """
    
    def __init__(self):
        self.lock = threading.Lock()
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
        
    def start(self):
        """Placeholder for compatibility."""
        pass
    
    def stop(self):
        """Placeholder for compatibility."""
        pass
    
    def add_detection(self, class_name: str, confidence: float, bbox: tuple = None):
        """
        Add a new detection to the statistics.
        """
        with self.lock:
            now = datetime.now()
            hour = now.hour
            
            detection = {
                'class': class_name,
                'confidence': round(confidence * 100, 2),
                'time': now.isoformat(),
                'hour': hour,
                'bbox': bbox
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
                self._add_violation_alert(class_name, confidence)
            else:
                self.stats['other'] += 1
                detection['type'] = 'other'
            
            self.stats['detections'].insert(0, detection)
            
            # Keep only last 100 detections in memory
            if len(self.stats['detections']) > 100:
                self.stats['detections'] = self.stats['detections'][:100]
            
            # Keep only last 10 alerts
            if len(self.stats['alerts']) > 10:
                self.stats['alerts'] = self.stats['alerts'][:10]
    
    def _add_violation_alert(self, class_name: str, confidence: float):
        """Add a violation alert."""
        alert = {
            'title': f'PPE Violation: {class_name}',
            'message': f'{class_name} detected with {round(confidence * 100, 1)}% confidence',
            'severity': 'danger',
            'time': datetime.now().isoformat()
        }
        self.stats['alerts'].insert(0, alert)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.
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
    
    def reset_stats(self):
        """
        Reset all statistics.
        """
        with self.lock:
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
            return {'message': 'Statistics reset successfully'}