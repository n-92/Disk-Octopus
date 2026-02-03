"""
Disk Scanner - Efficiently scan directory trees and build hierarchical data structure
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.console import Console

console = Console()


@dataclass
class FileNode:
    """Represents a file or directory in the tree."""
    name: str
    path: str
    size: int = 0
    is_dir: bool = False
    children: List['FileNode'] = field(default_factory=list)
    parent: Optional['FileNode'] = None
    extension_stats: dict = field(default_factory=dict)  # {ext: {count, size}}
    is_scanned: bool = False  # Track if this directory has been fully scanned
    
    @property
    def total_size(self) -> int:
        """Calculate total size including children."""
        if self.is_dir:
            return sum(child.total_size for child in self.children)
        return self.size
    
    @property
    def file_count(self) -> int:
        """Count total files including in subdirectories."""
        if not self.is_dir:
            return 1
        return sum(child.file_count for child in self.children)
    
    def get_sorted_children(self) -> List['FileNode']:
        """Get children sorted by size (largest first)."""
        return sorted(self.children, key=lambda x: x.total_size, reverse=True)
    
    def format_size(self) -> str:
        """Format size in human-readable format."""
        size = self.total_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    def get_extension_stats(self) -> dict:
        """Get file extension statistics for this directory and subdirs."""
        stats = {}
        self._collect_extension_stats(stats)
        return stats
    
    def _collect_extension_stats(self, stats: dict):
        """Recursively collect extension statistics."""
        for child in self.children:
            if not child.is_dir:
                ext = child.get_extension()
                if ext not in stats:
                    stats[ext] = {'count': 0, 'size': 0, 'files': []}
                stats[ext]['count'] += 1
                stats[ext]['size'] += child.size
                stats[ext]['files'].append(child.path)
            else:
                child._collect_extension_stats(stats)
    
    def get_extension(self) -> str:
        """Get file extension."""
        if self.is_dir:
            return '<dir>'
        ext = Path(self.path).suffix.lower()
        return ext if ext else '<no-ext>'


class DiskScanner:
    """Scans disk and builds directory tree."""
    
    def __init__(self, drive: str):
        self.drive = drive
        self.total_dirs = 0
        self.total_files = 0
    
    def scan(self, max_depth: Optional[int] = None) -> FileNode:
        """
        Scan the drive and return root FileNode.
        Uses progress bar for user feedback.
        """
        root = FileNode(
            name=self.drive,
            path=self.drive,
            is_dir=True
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Scanning directories...", total=None)
            self._scan_recursive(root, progress, task, max_depth=max_depth)
        
        return root
    
    def _scan_recursive(self, node: FileNode, progress: Progress, task, 
                        current_depth: int = 0, max_depth: Optional[int] = None):
        """Recursively scan directories."""
        
        # Check depth limit
        if max_depth is not None and current_depth >= max_depth:
            return
        
        try:
            entries = os.listdir(node.path)
        except (PermissionError, OSError):
            progress.update(task, description=f"[cyan]Scanning (access denied: {node.name})...")
            return
        
        progress.update(task, description=f"[cyan]Scanning: {node.name}...")
        
        for entry in entries:
            try:
                full_path = os.path.join(node.path, entry)
                
                if os.path.islink(full_path):
                    # Skip symlinks
                    continue
                
                if os.path.isdir(full_path):
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        is_dir=True,
                        parent=node
                    )
                    node.children.append(child)
                    self.total_dirs += 1
                    self._scan_recursive(child, progress, task, current_depth + 1, max_depth)
                
                else:
                    # File
                    try:
                        size = os.path.getsize(full_path)
                    except (OSError, PermissionError):
                        size = 0
                    
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        size=size,
                        is_dir=False,
                        parent=node
                    )
                    node.children.append(child)
                    self.total_files += 1
            
            except (OSError, PermissionError):
                # Skip files/dirs we can't access
                continue
        
        # Sort children by size
        node.children.sort(key=lambda x: x.total_size, reverse=True)
