"""
Configuration module for the disk visualizer
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    """Configuration settings for the visualizer."""
    
    # Display settings
    max_items_display: int = 12  # Maximum items to show in treemap
    max_items_table: int = 8     # Maximum items in the table
    treemap_height: int = 20     # Height of treemap visualization
    
    # Scan settings
    follow_symlinks: bool = False  # Don't follow symlinks
    max_depth: int = None          # Max recursion depth (None = unlimited)
    
    # Colors
    use_colors: bool = True        # Enable colors
    
    # Analysis settings
    max_file_samples: int = 5      # Files to sample for AI analysis
    cache_analysis: bool = True    # Cache Copilot analyses
    
    # Performance
    skip_hidden: bool = False      # Skip hidden files
    skip_system: bool = True       # Skip system files
    
    # Paths to skip (patterns)
    skip_patterns: List[str] = None
    
    def __post_init__(self):
        if self.skip_patterns is None:
            self.skip_patterns = [
                'node_modules',
                '.git',
                '__pycache__',
                '.venv',
                'venv',
                '.env',
                'dist',
                'build',
                '.pytest_cache',
            ]


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global config instance."""
    return config


def set_config(cfg: Config):
    """Set the global config instance."""
    global config
    config = cfg
