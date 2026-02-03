"""
Terminal UI - Interactive treemap visualization
"""

import os
from typing import Optional, List, Tuple, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.style import Style

from disk_scanner import FileNode
from treemap import TreemapLayout, Rectangle
from copilot_analyzer import CopilotAnalyzer

console = Console()

# Color palette for chunks
COLORS = [
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "orange1",
    "gold1",
    "dark_goldenrod",
]


class TerminalUI:
    """Interactive terminal UI for disk visualization."""
    
    def __init__(self):
        self.current_node: Optional[FileNode] = None
        self.selection_index: int = 0
        self.rectangles: List[Rectangle] = []
        from file_type_analyzer import FileTypeAnalyzer
        self.file_type_analyzer = FileTypeAnalyzer()
        self.file_type_stats: List = []
    
    def launch(self, root_node: FileNode):
        """Launch the interactive UI."""
        self.current_node = root_node
        self._refresh_display()
        self._handle_input()
    
    def _refresh_display(self):
        """Refresh the visualization."""
        console.clear()
        self._draw_header()
        self._draw_treemap()
        self._draw_footer()
    
    def _draw_header(self):
        """Draw header with current location."""
        # Breadcrumb
        breadcrumb = self._get_breadcrumb()
        
        header_text = f"📁 [bold cyan]{breadcrumb}[/bold cyan]\n"
        header_text += f"[green]Size: {self.current_node.format_size()}[/green] | "
        header_text += f"[yellow]Files: {self.current_node.file_count}[/yellow]"
        
        panel = Panel(
            header_text,
            border_style="cyan",
            padding=(0, 1)
        )
        console.print(panel)
        console.print()
    
    def _get_breadcrumb(self) -> str:
        """Get breadcrumb path from root to current node."""
        parts = []
        node = self.current_node
        
        while node is not None:
            parts.insert(0, node.name)
            node = node.parent
        
        return " → ".join(parts[:5])  # Limit to last 5 levels
    
    def _draw_treemap(self):
        """Draw the treemap visualization."""
        # Get terminal size
        width = console.width - 4
        height = 20
        
        # Calculate layout
        self.rectangles = TreemapLayout.calculate(
            self.current_node,
            x=0,
            y=0,
            width=width,
            height=height,
            max_items=12
        )
        
        if not self.rectangles:
            console.print("[yellow]📂 This directory is empty[/yellow]")
            return
        
        # Create visual grid
        grid = self._create_grid(width, height)
        self._render_grid(grid)
    
    def _create_grid(self, width: int, height: int) -> List[List]:
        """Create a 2D grid for rendering with rich cells."""
        grid = [[None for _ in range(width)] for _ in range(height)]
        
        for idx, rect in enumerate(self.rectangles):
            color_idx = idx % len(COLORS)
            color = COLORS[color_idx]
            
            # Get label (name + size)
            label = f"{idx}: {rect.node.name}"
            label_placed = False
            
            # Fill rectangle
            for dy in range(rect.height):
                for dx in range(rect.width):
                    y = rect.y + dy
                    x = rect.x + dx
                    if 0 <= y < height and 0 <= x < width:
                        cell_info = {
                            'color': color,
                            'rect_idx': idx,
                            'is_border': (dx == 0 or dy == 0 or dx == rect.width - 1 or dy == rect.height - 1),
                            'label': label if (dx == 1 and dy == 1 and not label_placed) else None,
                            'number': str(idx) if idx < 10 and dx == 1 and dy == 1 else None
                        }
                        grid[y][x] = cell_info
                        if label:
                            label_placed = True
        
        return grid
    
    def _render_grid(self, grid: List[List]):
        """Render grid with colors and chunk numbers."""
        for y, row in enumerate(grid):
            line = ""
            for x, cell in enumerate(row):
                if cell is None:
                    line += " "
                else:
                    color = cell['color']
                    
                    # Show number if this is the anchor point
                    if cell.get('number'):
                        char = cell['number']
                    else:
                        # Use block characters for visual fill
                        char = "█" if cell['is_border'] else "▒"
                    
                    line += f"[{color}]{char}[/{color}]"
            
            console.print(line)
            
        # Add legend showing what numbers mean
        if self.rectangles:
            console.print("\n[cyan]📍 Chunk Numbers (Press 0-9 to explore):[/cyan]")
            for idx in range(min(len(self.rectangles), 10)):
                rect = self.rectangles[idx]
                color = COLORS[idx % len(COLORS)]
                size_str = self._format_size(rect.node.total_size)
                console.print(
                    f"  [{color}][{idx}][/{color}] {rect.node.name:<20} {size_str:>12}",
                    end="  "
                )
                if (idx + 1) % 2 == 0:
                    console.print()
            if len(self.rectangles) % 2 != 0:
                console.print()
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}PB"
    
    def _draw_footer(self):
        """Draw footer with info and controls."""
        console.print()
        
        # Show file type statistics if available
        if hasattr(self, 'file_type_analyzer'):
            self._draw_file_type_stats()
        
        # Item list
        self._draw_item_list()
        
        # Controls
        controls = """[dim]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[cyan]0-9[/cyan] Select  [cyan]b[/cyan] Back  [cyan]s[/cyan] Stats  [cyan]a[/cyan] Analyze  [cyan]h[/cyan] Help  [cyan]q[/cyan] Quit
[/dim]"""
        console.print(controls)
    
    def _draw_file_type_stats(self):
        """Draw file type statistics."""
        try:
            stats = self.file_type_analyzer.get_statistics(self.current_node, top_n=6)
            if stats and len(stats) > 0:
                output = self.file_type_analyzer.format_statistics(stats)
                console.print()
                console.print(output)
                self.file_type_stats = stats  # Cache for later use
        except Exception as e:
            # Silently skip if there's an issue
            pass
    
    def _draw_item_list(self):
        """Draw list of items in current directory."""
        children = self.current_node.get_sorted_children()[:12]
        
        table = Table(title="📊 Top Items", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Size", justify="right")
        table.add_column("Type")
        
        for idx, child in enumerate(children):
            color = COLORS[idx % len(COLORS)]
            item_type = "📁 Dir" if child.is_dir else "📄 File"
            
            table.add_row(
                f"[{color}]{idx}[/{color}]",
                child.name,
                f"[yellow]{child.format_size()}[/yellow]",
                item_type
            )
        
        console.print(table)
    
    def _handle_input(self):
        """Handle user input."""
        while True:
            try:
                key = console.input("\n[cyan]Command:[/cyan] ").strip().lower()
                
                if key == 'q':
                    console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                    break
                
                elif key == 'h':
                    self._show_help()
                
                elif key == 'b':
                    if self.current_node.parent:
                        self.current_node = self.current_node.parent
                        self._refresh_display()
                    else:
                        console.print("[yellow]⚠️  Already at root[/yellow]")
                
                elif key == 'a':
                    self._analyze_current()
                    self._refresh_display()
                
                elif key == 's':
                    self._show_file_type_selector()
                
                elif key.isdigit():
                    idx = int(key)
                    children = self.current_node.get_sorted_children()
                    
                    if idx < len(children):
                        child = children[idx]
                        if child.is_dir:
                            self.current_node = child
                            self._refresh_display()
                        else:
                            self._show_file_info(child)
                    else:
                        console.print("[red]❌ Invalid selection[/red]")
                
                elif key == '':
                    self._refresh_display()
                
                else:
                    console.print(f"[yellow]⚠️  Unknown command. Type 'h' for help[/yellow]")
            
            except KeyboardInterrupt:
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def _show_file_info(self, node: FileNode):
        """Show information about a file."""
        info = f"""[cyan]📄 File: {node.name}[/cyan]
[green]Size:[/green] {node.format_size()}
[green]Path:[/green] {node.path}
        """
        panel = Panel(info, border_style="yellow", padding=(1, 2))
        console.print(panel)
    
    def _analyze_current(self):
        """Analyze current directory with Copilot."""
        console.print("\n[cyan]🤖 Analyzing with Copilot...[/cyan]")
        
        samples = self._get_file_samples(self.current_node, limit=5)
        
        if not samples:
            console.print("[yellow]⚠️  No files to analyze in this directory[/yellow]")
            return
        
        insights = self.copilot_analyzer.get_insights(self.current_node.path, samples)
        
        info = f"""[cyan]{insights['analysis']}[/cyan]
        
[green]Files analyzed:[/green] {insights['file_count']}
[green]Location:[/green] {insights['path']}
        """
        panel = Panel(info, border_style="magenta", padding=(1, 2), title="[bold magenta]🤖 Copilot Analysis[/bold magenta]")
        console.print(panel)
    
    def _get_file_samples(self, node: FileNode, limit: int = 5) -> List[str]:
        """Get representative file samples from a directory."""
        samples = []
        
        def collect_samples(n: FileNode, remaining: int):
            if remaining <= 0:
                return
            
            for child in n.children:
                if not child.is_dir and remaining > 0:
                    samples.append(child.path)
                    remaining -= 1
                elif child.is_dir and remaining > 0:
                    collect_samples(child, remaining)
        
        collect_samples(node, limit)
        return samples
    
    def _show_file_type_selector(self):
        """Show file type statistics and let user select one."""
        stats = self.file_type_analyzer.get_statistics(self.current_node, top_n=10)
        
        if not stats:
            console.print("[yellow]No files found in this directory[/yellow]")
            return
        
        # Show file types with numbers
        console.print("\n[bold cyan]📊 File Types in This Directory:[/bold cyan]\n")
        
        for idx, (ext, stat) in enumerate(stats):
            risk_check = self.file_type_analyzer.copilot.check_security_risks(ext, [])
            risk_icon = "⚠️ " if risk_check['risk_level'] != 'safe' else "✓ "
            
            console.print(
                f"  [{idx}] {risk_icon} {ext:<12} - {stat['percentage_by_size']:>6.1f}% "
                f"({stat['count']:>4} files, {self.file_type_analyzer._format_size(stat['size'])})"
            )
        
        # Ask user to select
        try:
            selection = console.input("\n[cyan]Select file type to analyze (0-9, or Enter to skip):[/cyan] ").strip()
            
            if selection and selection.isdigit():
                idx = int(selection)
                if 0 <= idx < len(stats):
                    ext, stat = stats[idx]
                    self._show_detailed_file_type_analysis(ext, stat)
        except KeyboardInterrupt:
            pass
    
    def _show_detailed_file_type_analysis(self, extension: str, stat: Dict):
        """Show detailed analysis of a specific file type."""
        console.print()
        
        # Risk check
        risk = self.file_type_analyzer.copilot.check_security_risks(extension, stat['files'])
        
        # Get copilot analysis
        analysis = self.file_type_analyzer.analyze_file_type(extension, stat)
        
        # Show all info
        info = f"""[cyan]📁 Analysis: {extension}[/cyan]

[green]Statistics:[/green]
  Files: {stat['count']}
  Total Size: {self.file_type_analyzer._format_size(stat['size'])}
  Percentage by Size: {stat['percentage_by_size']:.1f}%
  Percentage by Count: {stat['percentage_by_count']:.1f}%

[green]Description:[/green]
  {analysis}

[green]Security Assessment:[/green]
  {risk['message']}
"""
        
        if risk['risk_level'] != 'safe':
            info += f"\n[yellow]Locations Detected: {len(risk['locations'])} files[/yellow]"
        
        panel = Panel(info, border_style="cyan", padding=(1, 2), title=f"[bold cyan]{extension} Analysis[/bold cyan]")
        console.print(panel)
    
    def _show_help(self):
        """Show help menu."""
        help_text = """[bold cyan]📚 HELP & COMMANDS[/bold cyan]

[yellow]Navigation:[/yellow]
  [cyan]0-9[/cyan]       Select a numbered directory and open it
  [cyan]b[/cyan]        Go back to parent directory
  [cyan]r[/cyan]        Refresh current view

[yellow]File Analysis:[/yellow]
  [cyan]s[/cyan]        Show file type statistics & select one to analyze
  [cyan]a[/cyan]        Analyze current directory with Copilot

[yellow]Other:[/yellow]
  [cyan]h[/cyan]        Show this help menu
  [cyan]q[/cyan]        Quit the application

[yellow]File Type Statistics:[/yellow]
  • Shows percentage of disk used by each file type
  • ⚠️ icon indicates potentially risky file types
  • Select a file type to get Copilot analysis
  • See security risks and recommendations

[yellow]Tips:[/yellow]
  • File types show at bottom of screen
  • Use 's' to get detailed breakdown
  • Copilot analysis is cached for speed
  • Press Enter to refresh the display
        """
        
        panel = Panel(help_text, border_style="green", padding=(1, 2), 
                     title="[bold green]Help Menu[/bold green]")
        console.print(panel)
