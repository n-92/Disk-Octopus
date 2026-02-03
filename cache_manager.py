"""
Cache Manager - Persistent caching for disk scans
Enables instant loads on repeated scans of the same directory
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Optional
from dataclasses import asdict
from disk_scanner import FileNode


class ScanCache:
    """Manages persistent caching of disk scans."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to ~/.disk-octopus-cache
        """
        self.cache_dir = cache_dir or Path.home() / '.disk-octopus-cache'
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.memory_cache = {}  # In-memory cache for current session
    
    def _get_cache_key(self, path: str) -> str:
        """Generate unique cache key from path."""
        normalized_path = os.path.normpath(path).lower()
        return hashlib.md5(normalized_path.encode()).hexdigest()
    
    def _serialize_node(self, node: FileNode) -> dict:
        """Convert FileNode to serializable dict."""
        def node_to_dict(n: FileNode) -> dict:
            return {
                'name': n.name,
                'path': n.path,
                'size': n.size,
                'is_dir': n.is_dir,
                'children': [node_to_dict(child) for child in n.children],
            }
        
        return node_to_dict(node)
    
    def _deserialize_node(self, data: dict, parent: Optional[FileNode] = None) -> FileNode:
        """Convert dict back to FileNode."""
        node = FileNode(
            name=data['name'],
            path=data['path'],
            size=data['size'],
            is_dir=data['is_dir'],
            parent=parent
        )
        
        # Recursively deserialize children
        for child_data in data.get('children', []):
            child = self._deserialize_node(child_data, parent=node)
            node.children.append(child)
        
        # Invalidate cache flags so they're rebuilt on first access
        node._stats_dirty = True
        node._total_size_cache = -1
        
        return node
    
    def save_scan(self, path: str, node: FileNode) -> bool:
        """Save scan result to persistent cache.
        
        Args:
            path: Directory path that was scanned
            node: Root FileNode of the scan
        
        Returns:
            True if save succeeded, False otherwise
        """
        try:
            cache_key = self._get_cache_key(path)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            # Serialize and save
            serialized = self._serialize_node(node)
            with open(cache_file, 'w') as f:
                json.dump(serialized, f, indent=2)
            
            # Also store in memory cache
            self.memory_cache[cache_key] = node
            
            return True
        except Exception as e:
            print(f"Cache save failed: {e}")
            return False
    
    def load_scan(self, path: str) -> Optional[FileNode]:
        """Load previous scan from cache if available.
        
        Args:
            path: Directory path to load cache for
        
        Returns:
            Cached FileNode if available and valid, None otherwise
        """
        try:
            cache_key = self._get_cache_key(path)
            
            # Check memory cache first (fastest)
            if cache_key in self.memory_cache:
                return self.memory_cache[cache_key]
            
            # Check disk cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Deserialize
                node = self._deserialize_node(data)
                
                # Store in memory cache
                self.memory_cache[cache_key] = node
                
                return node
        except Exception as e:
            print(f"Cache load failed: {e}")
        
        return None
    
    def clear_cache(self, path: Optional[str] = None) -> bool:
        """Clear cache for specific path or all cache.
        
        Args:
            path: Directory path to clear cache for. If None, clears all cache.
        
        Returns:
            True if successful
        """
        try:
            if path is None:
                # Clear all
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                self.memory_cache.clear()
            else:
                # Clear specific
                cache_key = self._get_cache_key(path)
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    cache_file.unlink()
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
            
            return True
        except Exception as e:
            print(f"Cache clear failed: {e}")
            return False


# Global cache instance
_cache_instance = None


def get_cache() -> ScanCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ScanCache()
    return _cache_instance
