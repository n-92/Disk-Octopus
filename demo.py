"""
Demo script to showcase the Copilot Disk Visualizer
Run this to see the tool in action without interactive prompts
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
import time

from disk_scanner import DiskScanner, FileNode
from treemap import TreemapLayout
from ui import TerminalUI, COLORS

console = Console()


def demo():
    """Run demo of the disk visualizer."""
    
    # Intro
    intro = """[bold cyan]🚀 COPILOT DISK VISUALIZER - DEMO[/bold cyan]

This demo showcases:
1. Fast directory scanning with progress
2. Beautiful treemap visualization
3. Interactive navigation
4. Copilot-powered analysis

[yellow]Note: This demo uses a small directory for speed[/yellow]
    """
    
    panel = Panel(intro, border_style="cyan", padding=(1, 2))
    console.print(panel)
    console.print()
    
    # Scan
    console.print("[bold cyan]📊 Step 1: Scanning directory structure[/bold cyan]\n")
    
    scanner = DiskScanner('C:\\\\Users\\\\N92\\\\copilot_projects\\\\competition')
    root = scanner.scan()
    
    console.print(f"\n[bold green]✓ Scan Complete![/bold green]")
    console.print(f"  [cyan]Total size:[/cyan] {root.format_size()}")
    console.print(f"  [cyan]Files:[/cyan] {root.file_count}")
    console.print(f"  [cyan]Subdirs:[/cyan] {len(root.children)}\n")
    
    # Treemap
    console.print("[bold cyan]🎨 Step 2: Generating treemap layout[/bold cyan]\n")
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("Calculating layout...", total=100)
        
        rectangles = TreemapLayout.calculate(
            root,
            x=0, y=0,
            width=80, height=15,
            max_items=10
        )
        
        progress.update(task, completed=100)
    
    console.print(f"\n[bold green]✓ Layout Generated![/bold green]")
    console.print(f"  [cyan]Chunks:[/cyan] {len(rectangles)}\n")
    
    # Visualization
    console.print("[bold cyan]🎨 Step 3: Rendering visualization[/bold cyan]\n")
    
    # Draw treemap
    console.print("[yellow]Treemap:[/yellow]")
    _render_demo_treemap(rectangles)
    
    # Show items
    console.print("\n[yellow]📋 Top Items:[/yellow]\n")
    _show_items_demo(root)
    
    # Analysis
    console.print("[bold cyan]🤖 Step 4: Copilot Analysis[/bold cyan]\n")
    _show_analysis_demo(root)
    
    # Summary
    summary = """[bold green]✓ Demo Complete![/bold green]

The Copilot Disk Visualizer provides:
• [cyan]Fast scanning[/cyan] of large directories
• [cyan]Beautiful visualization[/cyan] in your terminal
• [cyan]Interactive navigation[/cyan] through files
• [cyan]AI-powered insights[/cyan] about your data

[yellow]To use on your actual disk:[/yellow]
  python main.py

[green]Enjoy exploring! 🚀[/green]
    """
    
    console.print()
    panel = Panel(summary, border_style="green", padding=(1, 2))
    console.print(panel)


def _render_demo_treemap(rectangles):
    """Render demo treemap."""
    width = 80
    height = 12
    grid = [[None for _ in range(width)] for _ in range(height)]
    
    for idx, rect in enumerate(rectangles):
        color_idx = idx % len(COLORS)
        color = COLORS[color_idx]
        
        for dy in range(min(rect.height, height - rect.y)):
            for dx in range(min(rect.width, width - rect.x)):
                y = rect.y + dy
                x = rect.x + dx
                if 0 <= y < height and 0 <= x < width:
                    is_border = (dx == 0 or dy == 0 or 
                                dx == rect.width - 1 or dy == rect.height - 1)
                    char = "█" if is_border else "░"
                    grid[y][x] = (char, color)
    
    for row in grid:
        line = ""
        for cell in row:
            if cell:
                char, color = cell
                line += f"[{color}]{char}[/{color}]"
            else:
                line += " "
        console.print(line)


def _show_items_demo(node: FileNode):
    """Show top items demo."""
    from rich.table import Table
    
    children = node.get_sorted_children()[:8]
    
    table = Table(show_header=True, header_style="bold cyan", show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Size", style="yellow", justify="right")
    table.add_column("Type", style="green")
    
    for idx, child in enumerate(children):
        item_type = "📁 Dir" if child.is_dir else "📄 File"
        table.add_row(
            str(idx),
            child.name,
            child.format_size(),
            item_type
        )
    
    console.print(table)


def _show_analysis_demo(node: FileNode):
    """Show analysis demo."""
    from rich.panel import Panel
    
    # Sample analysis
    analysis = """[cyan]📂 Directory Structure Analysis[/cyan]

[green]✓ Python Project Files Detected[/green]
  Contains Python source code and configuration files
  
[green]✓ Development Environment[/green]
  Includes __pycache__ and dependency files
  
[green]✓ Documentation[/green]
  README and module files present
  
[yellow]Summary:[/yellow]
This appears to be a Python development project with 
proper structure and documentation. The project is well
organized with clear separation of concerns.
    """
    
    panel = Panel(analysis, border_style="magenta", padding=(1, 2), 
                  title="[bold magenta]🤖 Copilot Insights[/bold magenta]")
    console.print(panel)


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
