import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import os

class StatsService:
    """
    Manages real-time statistics for PPE detection system.
    Tracks detections, compliance rates, and generates analytics.
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
        self.other_classes = ['Person', 'Safety Cone', 'machinery', 'vehicle']
        
        self.running = False
        self.stats_thread = None
        
    def start(self):
        """Start the statistics service in background thread."""
        if not self.running:
            self.running = True
            self.stats_thread = threading.Thread(target=self._cleanup_old_data, daemon=True)
            self.stats_thread.start()
    
    def stop(self):
        """Stop the statistics service."""
        self.running = False
        if self.stats_thread:
            self.stats_thread.join(timeout=1)
    
    def add_detection(self, class_name: str, confidence: float, bbox: tuple = None):
        """
        Add a new detection to the statistics.
        
        Args:
            class_name: Name of the detected class
            confidence: Detection confidence score (0-1)
            bbox: Bounding box coordinates (x1, y1, x2, y2)
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
            
            # Keep only last 1000 detections in memory
            if len(self.stats['detections']) > 1000:
                self.stats['detections'] = self.stats['detections'][:1000]
            
            # Keep only last 50 alerts
            if len(self.stats['alerts']) > 50:
                self.stats['alerts'] = self.stats['alerts'][:50]
    
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
        
        Returns:
            Dictionary containing current statistics
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
        """Reset all statistics."""
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
            return {'message': 'Statistics reset successfully', 'stats': self.get_stats()}
    
    def _cleanup_old_data(self):
        """Background task to clean up old data periodically."""
        while self.running:
            time.sleep(300)  # Run every 5 minutes
            
            with self.lock:
                # Remove detections older than 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.stats['detections'] = [
                    det for det in self.stats['detections']
                    if datetime.fromisoformat(det['time']) > cutoff_time
                ]
                
                # Remove alerts older than 1 hour
                alert_cutoff = datetime.now() - timedelta(hours=1)
                self.stats['alerts'] = [
                    alert for alert in self.stats['alerts']
                    if datetime.fromisoformat(alert['time']) > alert_cutoff
                ]
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get detailed compliance summary."""
        with self.lock:
            return {
                'total_compliance': self.stats['compliance'],
                'total_violations': self.stats['violations'],
                'compliance_rate': round(
                    (self.stats['compliance'] / max(self.stats['total'], 1)) * 100, 1
                ),
                'by_class': {
                    class_name: count 
                    for class_name, count in self.stats['class_counts'].items()
                },
                'violation_breakdown': {
                    class_name: self.stats['class_counts'].get(class_name, 0)
                    for class_name in self.violation_classes
                }
            }
    
    def export_stats(self, filepath: str = None) -> str:
        """
        Export statistics to JSON file.
        
        Args:
            filepath: Path to save the JSON file. If None, uses default location.
            
        Returns:
            Path to the exported file
        """
        if filepath is None:
            os.makedirs('outputs', exist_ok=True)
            filepath = f'outputs/stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with self.lock:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_stats(),
                'compliance_summary': self.get_compliance_summary()
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        return filepath

# Global instance for application-wide access
stats_instance = StatsService()