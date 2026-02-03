#!/usr/bin/env python3
"""
Quick reference - Common usage patterns
"""

# ============================================================================
# GETTING STARTED EXAMPLES
# ============================================================================

# Example 1: Basic Usage
# ----------------------
# 1. Install: pip install -r requirements.txt
# 2. Run: python main.py
# 3. Select drive: C (or D, E, etc.)
# 4. Navigate: Press 0-9 to select items
# 5. Analyze: Press 'a' for AI insights
# 6. Go back: Press 'b'
# 7. Quit: Press 'q'


# ============================================================================
# PROGRAMMATIC USAGE
# ============================================================================

from disk_scanner import DiskScanner
from treemap import TreemapLayout
from copilot_analyzer import CopilotAnalyzer

# Example 2: Scan a directory programmatically
def scan_example():
    scanner = DiskScanner('C:\\Users\\YourName\\Documents')
    root = scanner.scan()
    
    print(f"Total size: {root.format_size()}")
    print(f"Files: {root.file_count}")
    print(f"Subdirs: {len(root.children)}")
    
    # Access largest items
    for child in root.get_sorted_children()[:5]:
        print(f"  - {child.name}: {child.format_size()}")


# Example 3: Generate treemap layout
def treemap_example():
    scanner = DiskScanner('C:\\')
    root = scanner.scan()
    
    rectangles = TreemapLayout.calculate(
        node=root,
        x=0, y=0,
        width=80, height=20,
        max_items=12
    )
    
    print(f"Generated {len(rectangles)} rectangles")


# Example 4: Use Copilot analysis
def analysis_example():
    analyzer = CopilotAnalyzer()
    
    insights = analyzer.get_insights(
        'C:\\Users\\YourName\\Documents',
        ['file1.txt', 'file2.py', 'file3.md']
    )
    
    print(insights['analysis'])


# ============================================================================
# COMMAND REFERENCE (IN-APP)
# ============================================================================

COMMANDS = {
    '0-9': 'Select and open numbered directory',
    'b': 'Go back to parent directory',
    'a': 'Analyze current directory with Copilot',
    'r': 'Refresh the display',
    'h': 'Show help menu',
    'q': 'Quit the application',
    'Enter': 'Refresh display',
}


# ============================================================================
# CONFIGURATION EXAMPLES
# ============================================================================

from config import Config, set_config

# Example 5: Custom configuration
def config_example():
    custom_config = Config(
        max_items_display=15,
        max_items_table=10,
        treemap_height=25,
        max_file_samples=10,
        use_colors=True
    )
    set_config(custom_config)


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

TROUBLESHOOTING = {
    'Access Denied': 'Normal for system folders. Scanner handles gracefully.',
    'Slow Scan': 'Large drives take time. Progress bar shows status.',
    'No Copilot': 'Set GITHUB_TOKEN env var. Mock analysis still works.',
    'Display Issues': 'Maximize terminal to at least 80x20 characters.',
}


# ============================================================================
# TIPS & TRICKS
# ============================================================================

TIPS = [
    'Drill down into large directories to find what\'s using space',
    'Use "a" command to understand unknown directories',
    'Analyses are cached - second view is instant',
    'Press "b" repeatedly to backtrack quickly',
    'Large rectangles in treemap = large directories',
    'Table shows top items sorted by size',
    'Colors help distinguish between different folders',
    'Help menu (h) shows all commands anytime',
]


# ============================================================================
# FEATURE MATRIX
# ============================================================================

FEATURES = {
    'Disk Scanning': {
        'Speed': '★★★★☆ (depends on drive size)',
        'Coverage': '★★★★★ (all accessible folders)',
        'Details': '★★★★★ (size, type, count)',
    },
    'Visualization': {
        'Beauty': '★★★★★ (colors, unicode, layout)',
        'Clarity': '★★★★★ (visual hierarchy)',
        'Interactive': '★★★★★ (fully clickable)',
    },
    'Analysis': {
        'Intelligence': '★★★★☆ (AI-powered)',
        'Accuracy': '★★★★☆ (file sampling)',
        'Speed': '★★★★★ (cached)',
    },
    'UX': {
        'Intuitiveness': '★★★★★ (easy to learn)',
        'Feedback': '★★★★★ (progress everywhere)',
        'Error Handling': '★★★★★ (graceful)',
    },
}


# ============================================================================
# PERFORMANCE CHARACTERISTICS
# ============================================================================

PERFORMANCE = {
    'Small drive (< 100GB)': 'Instant - 10 seconds',
    'Medium drive (100-500GB)': 'Quick - 15-30 seconds',
    'Large drive (500GB-1TB)': 'Reasonable - 30-60 seconds',
    'Very large (1TB+)': 'Patient - 60-120+ seconds',
    'Subsequent navigation': 'Instant',
    'Analysis caching': 'Instant on second view',
}


if __name__ == '__main__':
    # Show this as reference
    print("See inline comments for usage examples")
    print("\nRun: python main.py")
    print("Or: python demo.py")
