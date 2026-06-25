import os
from typing import List, Dict, Optional
from pathlib import Path

class VideoSourceManager:
    """
    Manages available video sources for PPE detection system.
    Handles both video files and camera streams.
    """
    
    def __init__(self, videos_dir: str = "videos"):
        self.videos_dir = videos_dir
        self.available_sources = self._discover_sources()
        self.current_source = self.available_sources[0]['id'] if self.available_sources else None
        
    def _discover_sources(self) -> List[Dict[str, str]]:
        """
        Discover available video sources from the videos directory.
        
        Returns:
            List of source dictionaries with id, name, and path
        """
        sources = []
        
        # Add camera sources
        sources.append({
            'id': 'camera_0',
            'name': 'Camera 0 (Default)',
            'type': 'camera',
            'path': '0'
        })
        
        # Check if videos directory exists
        if os.path.exists(self.videos_dir):
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
            
            # Scan for video files
            for file in os.listdir(self.videos_dir):
                file_path = Path(file)
                if file_path.suffix.lower() in video_extensions:
                    source_id = f"video_{file_path.stem}"
                    sources.append({
                        'id': source_id,
                        'name': f"Video: {file_path.name}",
                        'type': 'file',
                        'path': os.path.join(self.videos_dir, file)
                    })
        
        return sources
    
    def get_sources(self) -> List[Dict[str, str]]:
        """
        Get all available video sources.
        
        Returns:
            List of available video sources
        """
        return self.available_sources
    
    def get_source(self, source_id: str) -> Optional[Dict[str, str]]:
        """
        Get a specific video source by ID.
        
        Args:
            source_id: The ID of the video source
            
        Returns:
            Source dictionary or None if not found
        """
        for source in self.available_sources:
            if source['id'] == source_id:
                return source
        return None
    
    def set_current_source(self, source_id: str) -> bool:
        """
        Set the current active video source.
        
        Args:
            source_id: The ID of the video source to set as current
            
        Returns:
            True if successful, False otherwise
        """
        source = self.get_source(source_id)
        if source:
            self.current_source = source_id
            return True
        return False
    
    def get_current_source(self) -> Optional[Dict[str, str]]:
        """
        Get the currently active video source.
        
        Returns:
            Current source dictionary or None if none is set
        """
        if self.current_source:
            return self.get_source(self.current_source)
        return None
    
    def get_current_source_path(self) -> Optional[str]:
        """
        Get the path of the current video source.
        
        Returns:
            Path string or None if no source is set
        """
        current = self.get_current_source()
        return current['path'] if current else None
    
    def refresh_sources(self):
        """Refresh the list of available video sources."""
        self.available_sources = self._discover_sources()
        
        # Reset current source if it no longer exists
        if self.current_source:
            exists = any(source['id'] == self.current_source for source in self.available_sources)
            if not exists and self.available_sources:
                self.current_source = self.available_sources[0]['id']
    
    def add_custom_source(self, source_id: str, name: str, path: str, source_type: str = 'custom') -> bool:
        """
        Add a custom video source.
        
        Args:
            source_id: Unique identifier for the source
            name: Display name for the source
            path: Path or URL to the video source
            source_type: Type of source ('file', 'camera', 'url', 'custom')
            
        Returns:
            True if added successfully, False otherwise
        """
        # Check if source ID already exists
        if self.get_source(source_id):
            return False
        
        new_source = {
            'id': source_id,
            'name': name,
            'type': source_type,
            'path': path
        }
        
        self.available_sources.append(new_source)
        return True

# Global instance for application-wide access
video_source_manager = VideoSourceManager()