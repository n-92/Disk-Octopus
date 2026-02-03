"""
File Type Analysis - Analyze file types and statistics
"""

from typing import Dict, List, Tuple
from disk_scanner import FileNode
from copilot_analyzer import CopilotBinaryAnalyzer


class FileTypeAnalyzer:
    """Analyzes file types and their statistics."""
    
    def __init__(self):
        self.copilot = CopilotBinaryAnalyzer()
    
    def get_statistics(self, node: FileNode, top_n: int = 10) -> List[Tuple[str, Dict]]:
        """
        Get file type statistics sorted by size.
        
        Returns:
            List of (extension, stats_dict) tuples
            stats_dict contains: count, size, percentage_by_size, percentage_by_count
        """
        ext_stats = node.get_extension_stats()
        
        # Remove directory entries
        ext_stats = {k: v for k, v in ext_stats.items() if k != '<dir>'}
        
        if not ext_stats:
            return []
        
        total_size = sum(v['size'] for v in ext_stats.values())
        total_count = sum(v['count'] for v in ext_stats.values())
        
        # Calculate percentages
        for ext, stats in ext_stats.items():
            stats['percentage_by_size'] = (stats['size'] / total_size * 100) if total_size > 0 else 0
            stats['percentage_by_count'] = (stats['count'] / total_count * 100) if total_count > 0 else 0
        
        # Sort by size descending
        sorted_stats = sorted(
            ext_stats.items(),
            key=lambda x: x[1]['size'],
            reverse=True
        )
        
        return sorted_stats[:top_n]
    
    def format_statistics(self, statistics: List[Tuple[str, Dict]]) -> str:
        """Format statistics for display."""
        if not statistics:
            return "No files found"
        
        output = "[cyan]📊 File Types by Size:[/cyan]\n"
        
        for ext, stats in statistics:
            output += f"  [yellow]{ext:<12}[/yellow] "
            output += f"[green]{stats['percentage_by_size']:>6.1f}%[/green] "
            output += f"({self._format_size(stats['size']):>8}, "
            output += f"{stats['count']:>4} files)\n"
        
        return output
    
    def get_file_type_info(self, extension: str, statistics: List[Tuple[str, Dict]]) -> Dict:
        """Get detailed info about a specific file type."""
        for ext, stats in statistics:
            if ext.lower() == extension.lower():
                return {
                    'extension': ext,
                    'count': stats['count'],
                    'size': stats['size'],
                    'percentage_by_size': stats['percentage_by_size'],
                    'percentage_by_count': stats['percentage_by_count'],
                    'files': stats['files']
                }
        return None
    
    def analyze_file_type(self, extension: str, stats: Dict) -> str:
        """Get Copilot analysis of a file type."""
        return self.copilot.analyze_file_type(
            extension,
            stats['files'][:5],  # Sample 5 files
            stats['count'],
            stats['size']
        )
    
    def check_security(self, extension: str, node: FileNode) -> Dict:
        """Check security concerns for file type."""
        locations = []
        
        # Find where these files are located
        all_files = []
        self._collect_files(node, all_files)
        
        for f in all_files:
            if f.path.endswith(extension):
                locations.append(f.path)
        
        return self.copilot.check_security_risks(extension, locations[:5])
    
    def _collect_files(self, node: FileNode, files: List):
        """Recursively collect all files."""
        for child in node.children:
            if child.is_dir:
                self._collect_files(child, files)
            else:
                files.append(child)
    
    def get_security_summary(self, node: FileNode) -> Dict:
        """Get overall security summary for directory."""
        ext_stats = node.get_extension_stats()
        
        critical_extensions = {'.exe', '.dll', '.scr', '.com', '.vbs'}
        warning_extensions = {'.bat', '.cmd', '.ps1', '.js'}
        
        summary = {
            'critical_files': 0,
            'warning_files': 0,
            'total_files': 0,
            'safe': True,
            'warnings': [],
            'recommendations': []
        }
        
        for ext, stats in ext_stats.items():
            if ext in critical_extensions:
                summary['critical_files'] += stats['count']
                summary['safe'] = False
                summary['warnings'].append(
                    f"⚠️ CRITICAL: Found {stats['count']} {ext} executable files"
                )
            elif ext in warning_extensions:
                summary['warning_files'] += stats['count']
                summary['warnings'].append(
                    f"⚠️ WARNING: Found {stats['count']} {ext} script files"
                )
            
            summary['total_files'] += stats['count']
        
        if summary['critical_files'] > 0:
            summary['recommendations'].append(
                "Review all executable files for legitimacy"
            )
            summary['recommendations'].append(
                "Consider running antivirus scan"
            )
        
        if summary['warning_files'] > 0:
            summary['recommendations'].append(
                "Script files should come from trusted sources only"
            )
        
        if summary['safe']:
            summary['warnings'].append("✓ No obvious security concerns detected")
        
        return summary
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format bytes to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}PB"
