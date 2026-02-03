"""
Textual-based UI for Disk Octopus.
Split-view interface with file tree on left and statistics on right.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Tree, DataTable, Label, ProgressBar
from textual.screen import Screen
from rich.text import Text
import asyncio
import os

from disk_scanner import DiskScanner, FileNode
from file_type_analyzer import FileTypeAnalyzer
from copilot_analyzer import CopilotBinaryAnalyzer
from cache_manager import get_cache


class DiskVisualizerApp(Screen):
    """Main Textual application for disk visualization."""
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "show_help", "Help"),
        ("s", "show_stats", "Stats"),
        ("a", "analyze", "Analyze"),
        ("d", "deep_analyze", "Deep Analysis"),
        ("enter", "select_tree_node", "Select"),
    ]
    
    def __init__(self, drive_path: str = None):
        super().__init__()
        self.drive_path = drive_path or "C:\\"
        self.scanner = None
        self.root_node = None
        self.selected_node = None
        self.file_type_analyzer = FileTypeAnalyzer()
        self.copilot_analyzer = CopilotBinaryAnalyzer()
        self.cache = get_cache()
        self.scanning = False
        self.scan_progress = 0
        self.scan_total = 100
        self.extension_data = {}
        self.tree_nodes_map = {}
        self.title = f"Disk Octopus | {self.drive_path}"
        self._scan_count = 0  # Track items scanned
        
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=False)
        
        # Main content area with two columns
        with Horizontal(id="main-content"):
            # Left panel: File tree
            with Vertical(id="left-panel"):
                yield Label("[bold][ Directory Tree ][/bold]", id="tree-header")
                yield Tree(self.drive_path, id="file-tree")
            
            # Right panel: Statistics, Analysis, and paths
            with Vertical(id="right-panel"):
                # Top row: Statistics (left) + Analysis (right)
                with Horizontal(id="top-row"):
                    # Statistics panel
                    with Vertical(id="stats-section"):
                        yield Label("[bold][ File Statistics ][/bold]", id="stats-header")
                        yield DataTable(id="stats-table")
                    
                    # Copilot Analysis panel (scrollable)
                    with Vertical(id="analysis-section"):
                        yield Label("[bold][ Copilot Analysis ][/bold]", id="analysis-header")
                        with VerticalScroll(id="analysis-scroll"):
                            yield Static("", id="analysis-panel")
                
                # Bottom row: File paths (left) + Deep Analysis Results (right)
                with Horizontal(id="bottom-row"):
                    # File paths grid
                    with Vertical(id="paths-section"):
                        yield Label("[bold][ File Paths ][/bold]", id="paths-header")
                        yield DataTable(id="paths-table")
                    
                    # Deep Analysis Results
                    with Vertical(id="deep-analysis-section"):
                        yield Label("[bold][ Deep Analysis Results ][/bold]", id="deep-analysis-header")
                        with VerticalScroll(id="deep-analysis-scroll"):
                            yield Static("", id="deep-analysis-panel")
        
        # Status bar at bottom (OUTSIDE main-content for proper docking)
        # Only shows progress bar, no status message
        with Horizontal(id="status-bar"):
            yield ProgressBar(total=100, id="progress-bar")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize, setup, and start scanning."""
        self.title = f"Disk Octopus | {self.drive_path}"
        self.setup_stats_table()
        self.setup_paths_table()
        self.setup_file_tree()
        
        # Focus the tree
        tree = self.query_one("#file-tree", Tree)
        tree.focus()
        
        # Now start the scan
        await self.start_scan()
    
    def setup_stats_table(self) -> None:
        """Configure the statistics table."""
        table = self.query_one("#stats-table", DataTable)
        table.add_columns(
            "Extension",
            "Count",
            "Size",
            "%"
        )
        table.cursor_type = "row"
    
    def setup_paths_table(self) -> None:
        """Configure the file paths table."""
        try:
            table = self.query_one("#paths-table", DataTable)
            table.add_columns("File Path")
        except:
            pass  # Table may not exist yet
        
    
    def setup_file_tree(self) -> None:
        """Configure the file tree widget."""
        tree = self.query_one("#file-tree", Tree)
        tree.show_root = True
        
        # Format the root label to show proper icon
        root_label = self.format_tree_root_label(self.drive_path)
        tree.root.label = root_label
    
    async def start_scan(self) -> None:
        """Start disk scan - load first level folders only. Uses cache if available."""
        self.scanning = True
        self._scan_count = 0
        
        try:
            tree = self.query_one("#file-tree", Tree)
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            
            # Try to load from cache first
            self.title = f"Disk Octopus | Checking cache..."
            progress_bar.progress = 25
            self.refresh()
            await asyncio.sleep(0)
            
            cached_node = await asyncio.to_thread(
                self.cache.load_scan, self.drive_path
            )
            
            if cached_node:
                # Use cached data!
                self.title = f"Disk Octopus | Loaded from cache..."
                progress_bar.progress = 50
                self.refresh()
                await asyncio.sleep(0)
                
                self.root_node = cached_node
                await self._populate_tree_from_node(tree.root, cached_node)
                
                self.scanning = False
                progress_bar.progress = 100
                self.title = f"Disk Octopus | {self.drive_path} | Ready (cached)"
                self.refresh()
                return
            
            # No cache, do full scan
            self.title = f"Disk Octopus | Loading first level..."
            progress_bar.progress = 0
            tree.clear()
            root = tree.root
            root.label = f"[D] {self.drive_path}"
            self.refresh()
            await asyncio.sleep(0)
            
            # Get first level entries in background using simple os.listdir
            entries = await asyncio.to_thread(
                self._get_first_level_entries, self.drive_path
            )
            
            # Populate tree on main thread
            if entries:
                root.data = {"path": self.drive_path, "is_dir": True}
                root.label = f"[D] {self.drive_path}"
                
                for entry_name, entry_path, is_dir, size in entries:
                    icon = "[d]" if is_dir else "[f]"
                    size_str = self.format_size(size) if size > 0 else ""
                    label = f"{icon} {entry_name:<30} {size_str:>10}"
                    
                    tree_node = root.add(label)
                    tree_node.data = {"path": entry_path, "name": entry_name, "is_dir": is_dir, "size": size, "scanned": False}
                    
                    # Add placeholder for directories
                    if is_dir:
                        tree_node.add("[...]")
                
                # Expand the root node to show children
                root.expand()
                self.refresh()
            
            # Save to cache for next time
            if self.root_node:
                await asyncio.to_thread(
                    self.cache.save_scan, self.drive_path, self.root_node
                )
            
            # Complete
            self.scanning = False
            progress_bar.progress = 100
            self.title = f"Disk Octopus | {self.drive_path} | Ready"
            self.refresh()
            
        except Exception as e:
            self.scanning = False
            self.title = f"Disk Octopus | ERROR"
            self.refresh()
            self.notify(f"Error: {str(e)[:50]}", severity="error")
    
    def _get_first_level_entries(self, path: str) -> list:
        """Get first-level directory entries as (name, path, is_dir, size) tuples."""
        entries = []
        try:
            for entry in os.listdir(path):
                try:
                    full_path = os.path.join(path, entry)
                    
                    if os.path.islink(full_path):
                        continue
                    
                    is_dir = os.path.isdir(full_path)
                    size = 0
                    
                    if is_dir:
                        # Don't calculate folder size - just mark as directory
                        size = 0
                    else:
                        try:
                            size = os.path.getsize(full_path)
                        except:
                            size = 0
                    
                    entries.append((entry, full_path, is_dir, size))
                except:
                    pass
        except:
            pass
        
        # Sort by name
        entries.sort(key=lambda x: x[0])
        return entries
    
    async def _populate_tree_node(self, tree_node, file_node: FileNode) -> None:
        """Recursively populate a tree node with children."""
        if not file_node.children:
            return
        
        for child in sorted(file_node.children, key=lambda x: x.total_size if x.is_dir else x.size, reverse=True):
            label = self.format_node_label(child)
            new_tree_node = tree_node.add(label, data=child)
            
            # Yield to UI
            await asyncio.sleep(0)
            
            # Recurse
            if child.is_dir and child.children:
                await self._populate_tree_node(new_tree_node, child)
    
    def watch_tree_cursor(self) -> None:
        """Watch for tree cursor changes - load children on demand."""
        try:
            tree = self.query_one("#file-tree", Tree)
            if tree.cursor_node:
                node = tree.cursor_node
                file_node = node.data
                
                # If this is a directory with children placeholder, load its children
                if file_node and file_node.is_dir:
                    # Check if it has placeholder children
                    has_placeholder = any(
                        child.data is None for child in node.children
                    )
                    
                    if has_placeholder and not file_node.is_scanned:
                        # Load children in background
                        asyncio.create_task(self._load_node_children(node, file_node))
        except:
            pass
    
    async def _load_node_children(self, tree_node, file_node: FileNode) -> None:
        """Load children of a node on demand."""
        try:
            # Scan directory in background
            await asyncio.to_thread(
                self._scan_directory, file_node
            )
            
            # Update tree on main thread
            if file_node.children:
                # Remove placeholder children
                tree_node.children = []
                
                # Add real children
                for child in sorted(
                    file_node.children,
                    key=lambda x: x.total_size if x.is_dir else x.size,
                    reverse=True
                ):
                    label = self.format_node_label(child)
                    new_tree_node = tree_node.add(label, data=child)
                    
                    # Add placeholder for directories
                    if child.is_dir:
                        new_tree_node.add("[...]")
                
                self.refresh()
        except:
            pass
    
    def _scan_full_tree(self, path: str) -> FileNode:
        """Scan full directory tree (unlimited depth)."""
        root = FileNode(name=path, path=path, is_dir=True)
        self._scan_recursive(root, depth=0)
        return root
    
    def _scan_recursive(self, node: FileNode, depth: int = 0) -> None:
        """Recursively scan all directories."""
        if depth > 10:  # Limit depth to avoid infinite recursion
            return
        
        try:
            entries = os.listdir(node.path)
        except (PermissionError, OSError):
            return
        
        for entry in entries:
            try:
                full_path = os.path.join(node.path, entry)
                
                if os.path.islink(full_path):
                    continue
                
                if os.path.isdir(full_path):
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        is_dir=True,
                        parent=node,
                        is_scanned=True
                    )
                    node.children.append(child)
                    self._scan_recursive(child, depth + 1)  # Recurse
                else:
                    try:
                        size = os.path.getsize(full_path)
                    except (OSError, PermissionError):
                        size = 0
                    
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        size=size,
                        is_dir=False,
                        parent=node,
                        is_scanned=True
                    )
                    node.children.append(child)
            except Exception:
                pass
    
    def _quick_scan_only(self, path: str) -> FileNode:
        """Fast scan limited to depth 5 (no UI operations)."""
        root = FileNode(name=path, path=path, is_dir=True)
        self._scan_limited_depth(root, depth=0, max_depth=5)
        return root
    
    def _scan_first_level_only(self, path: str) -> FileNode:
        """Scan only first level (immediate children only) - FASTEST."""
        root = FileNode(name=path, path=path, is_dir=True)
        
        try:
            entries = os.listdir(path)
        except (PermissionError, OSError):
            root.is_scanned = True
            return root
        
        for entry in entries:
            try:
                full_path = os.path.join(path, entry)
                
                if os.path.islink(full_path):
                    continue
                
                if os.path.isdir(full_path):
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        is_dir=True,
                        parent=root,
                        is_scanned=False  # Mark as not yet scanned
                    )
                    root.children.append(child)
                else:
                    try:
                        size = os.path.getsize(full_path)
                    except (OSError, PermissionError):
                        size = 0
                    
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        size=size,
                        is_dir=False,
                        parent=root,
                        is_scanned=True  # Files don't need scanning
                    )
                    root.children.append(child)
            except Exception:
                pass
        
        root.is_scanned = True
        return root
    
    def _scan_limited_depth(self, node: FileNode, depth: int = 0, max_depth: int = 5) -> None:
        """Recursively scan with depth limit (pure data, no UI)."""
        if depth > max_depth:
            return
        
        try:
            entries = os.listdir(node.path)
        except (PermissionError, OSError):
            return
        
        for entry in entries:
            try:
                full_path = os.path.join(node.path, entry)
                
                if os.path.islink(full_path):
                    continue
                
                if os.path.isdir(full_path):
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        is_dir=True,
                        parent=node
                    )
                    node.children.append(child)
                    self._scan_limited_depth(child, depth + 1, max_depth)
                else:
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
                    
            except Exception:
                pass
    
    async def populate_tree_async(self) -> None:
        """Populate tree widget on main thread (UI-safe)."""
        tree = self.query_one("#file-tree", Tree)
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        
        if not self.root_node:
            return
        
        try:
            tree.clear()
            root = tree.root
            root.data = self.root_node
            root.label = self.format_node_label(self.root_node)
            
            # Populate with UI yields
            await self.add_tree_nodes_async(root, self.root_node, progress_bar)
        except Exception as e:
            pass
    
    async def add_tree_nodes_async(self, tree_node, file_node: FileNode, progress_bar, depth: int = 0) -> None:
        """Recursively add nodes with progress updates on main thread."""
        if not file_node.children:
            return
        
        sorted_children = sorted(
            file_node.children,
            key=lambda x: x.total_size,
            reverse=True
        )
        
        for idx, child in enumerate(sorted_children):
            try:
                label = self.format_node_label(child)
                new_tree_node = tree_node.add(label, data=child)
                
                # Recursively add children
                if child.children:
                    if depth == 0 and idx % 5 == 0:
                        # Yield to UI every 5 nodes at depth 0
                        self.title = f"Disk Octopus | Building tree... {idx}/{len(sorted_children)}"
                        progress_bar.progress = 50 + (idx / len(sorted_children)) * 50
                        self.refresh()
                        await asyncio.sleep(0)
                    
                    await self.add_tree_nodes_async(new_tree_node, child, progress_bar, depth + 1)
            except Exception:
                pass
    
    async def populate_tree(self) -> None:
        """Populate the tree widget from FileNode structure."""
        tree = self.query_one("#file-tree", Tree)
        
        if not self.root_node:
            return
        
        try:
            # Clear and add nodes recursively
            tree.clear()
            root = tree.root
            root.data = self.root_node
            root.label = self.format_node_label(self.root_node)
            
            # Populate tree with yield for UI responsiveness
            await self.add_tree_nodes(root, self.root_node)
        except Exception as e:
            pass  # Silently fail if tree has issues
    
    async def add_tree_nodes(self, tree_node, file_node: FileNode, depth: int = 0) -> None:
        """Recursively add FileNode children to tree with UI yields."""
        if not file_node.children:
            return
        
        # Sort by size descending
        sorted_children = sorted(
            file_node.children,
            key=lambda x: x.size,
            reverse=True
        )
        
        for child in sorted_children:
            try:
                label = self.format_node_label(child)
                new_tree_node = tree_node.add(label, data=child)
                
                # Recursively add children
                if child.children:
                    # Yield control to event loop every 10 nodes at depth 0
                    # This keeps UI responsive during large tree builds
                    if depth == 0 and sorted_children.index(child) % 10 == 0:
                        await asyncio.sleep(0)
                    
                    await self.add_tree_nodes(new_tree_node, child, depth + 1)
            except Exception:
                pass  # Skip nodes that have issues
    
    def format_node_label(self, node: FileNode) -> Text:
        """Format a node for display in tree with ASCII-safe icons."""
        # Use ASCII characters that render properly in PowerShell
        # Instead of emoji which often show as ?
        
        if not hasattr(node, 'is_dir') or not hasattr(node, 'name'):
            return Text("[?] Unknown", style="red")
        
        # ASCII-safe icons
        icon = "[?]"  # Default fallback (but should be overridden)
        style = "white"
        
        try:
            if node.is_dir:
                # Folder icons using ASCII brackets
                if node.total_size > 1e9:  # > 1GB
                    icon = "[D]"  # Directory - Large
                    style = "bold red"
                elif node.total_size > 1e8:  # > 100MB
                    icon = "[d]"  # directory - medium
                    style = "bold yellow"
                else:
                    icon = "[d]"  # Directory - small
                    style = "bold cyan"
            else:
                # File icons using ASCII brackets
                if node.size > 1e9:  # > 1GB
                    icon = "[F]"  # File - Large
                    style = "bold red"
                elif node.size > 1e8:  # > 100MB
                    icon = "[f]"  # file - medium
                    style = "bold yellow"
                else:
                    icon = "[f]"  # file - small
                    style = "green"
        except Exception:
            icon = "[!]"  # Warning
            style = "yellow"
        
        try:
            # Get total_size for dirs, size for files
            if hasattr(node, 'total_size') and node.is_dir:
                size = node.total_size
            elif hasattr(node, 'size'):
                size = node.size
            else:
                size = 0
            
            size_str = self.format_size(size)
            # Format: [D] name                 size (more compact)
            label = f"{icon} {node.name:<35} {size_str:>10}"
            return Text(label, style=style)
        except Exception as e:
            return Text(f"{icon} {node.name}", style=style)
    
    def format_tree_root_label(self, drive_path: str) -> Text:
        """Format the root node label for the tree."""
        # Root is a drive, show [D] for directory/drive
        icon = "[D]"
        style = "bold red"
        
        try:
            # Format: [D] C:\                      Total Size
            label = f"{icon} {drive_path:<35} "
            return Text(label, style=style)
        except Exception:
            return Text(f"{icon} {drive_path}", style=style)
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format bytes to human readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
    
    def on_tree_node_selected(self, message: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        node = message.node
        
        if not node.data:
            return
        
        # Handle both dict (lazy-loading) and FileNode (initial load) formats
        if isinstance(node.data, dict):
            # Dict-based node from lazy-loading
            file_path = node.data.get("path")
            is_dir = node.data.get("is_dir", False)
            scanned = node.data.get("scanned", False)
            
            # If it's a directory that hasn't been scanned yet, load its children
            if is_dir and not scanned and file_path:
                # Load children asynchronously
                asyncio.create_task(self._load_children_on_expand(node, file_path))
            
            # Store the node data for analysis
            self.selected_node = node.data
            
            # Update analysis panel with dict data
            self.update_analysis_panel_from_dict(node.data)
            
            # Update statistics if it's a directory
            if is_dir:
                self.update_statistics_from_dict(node.data)
        else:
            # FileNode object from initial tree load
            file_node = node.data
            
            # Store the node for analysis
            self.selected_node = file_node
            
            # Update analysis panel with FileNode data
            self.update_analysis_panel_from_filenode(file_node)
            
            # Update statistics if it's a directory
            if hasattr(file_node, 'is_dir') and file_node.is_dir:
                self.update_statistics_from_filenode(file_node)

    
    async def _load_children_on_expand(self, tree_node, file_path: str) -> None:
        """Load children of a folder when node is expanded."""
        try:
            # Get entries in background
            entries = await asyncio.to_thread(
                self._get_directory_entries, file_path
            )
            
            # Add to tree on main thread
            if entries:
                for entry_name, entry_path, is_dir, size in entries:
                    icon = "[d]" if is_dir else "[f]"
                    size_str = self.format_size(size) if size > 0 else ""
                    # Format: [d] name                 size (more compact)
                    label = f"{icon} {entry_name:<35} {size_str:>10}"
                    
                    child_node = tree_node.add(label)
                    child_node.data = {"path": entry_path, "name": entry_name, "is_dir": is_dir, "size": size, "scanned": False}
                    
                    # Add placeholder for subdirectories
                    if is_dir:
                        child_node.add("[...]")
                
                # Mark as scanned
                tree_node.data["scanned"] = True
                self.refresh()
        except Exception:
            pass
    
    def _get_directory_entries(self, path: str) -> list:
        """Get directory entries as (name, path, is_dir, size) tuples."""
        entries = []
        try:
            for entry in os.listdir(path):
                try:
                    full_path = os.path.join(path, entry)
                    
                    if os.path.islink(full_path):
                        continue
                    
                    is_dir = os.path.isdir(full_path)
                    size = 0
                    
                    if is_dir:
                        # Don't calculate folder size - just mark as directory
                        size = 0
                    else:
                        try:
                            size = os.path.getsize(full_path)
                        except:
                            size = 0
                    
                    entries.append((entry, full_path, is_dir, size))
                except:
                    pass
        except:
            pass
        
        # Sort by name
        entries.sort(key=lambda x: x[0])
        return entries
    
    def update_statistics_from_dict(self, node_dict: dict) -> None:
        """Update statistics table from dict-based node (directory)."""
        try:
            is_dir = node_dict.get("is_dir", False)
            if not is_dir:
                return
            
            path = node_dict.get("path", "")
            if not path:
                return
            
            # Collect file statistics for this directory
            extension_stats = {}
            
            try:
                entries = os.listdir(path)
            except (PermissionError, OSError):
                return
            
            for entry in entries:
                try:
                    full_path = os.path.join(path, entry)
                    
                    if os.path.islink(full_path):
                        continue
                    
                    if os.path.isdir(full_path):
                        continue  # Skip subdirectories
                    
                    # Get file size and extension
                    try:
                        size = os.path.getsize(full_path)
                    except:
                        size = 0
                    
                    # Extract extension
                    if '.' in entry:
                        ext = entry.split('.')[-1].lower()
                        ext = f".{ext}"
                    else:
                        ext = "Other"
                    
                    if ext not in extension_stats:
                        extension_stats[ext] = {'count': 0, 'size': 0, 'files': []}
                    
                    extension_stats[ext]['count'] += 1
                    extension_stats[ext]['size'] += size
                    extension_stats[ext]['files'].append(full_path)
                except:
                    pass
            
            # Update the stats table
            table = self.query_one("#stats-table", DataTable)
            table.clear()
            
            # Store extension data for later path display
            self.extension_data = extension_stats
            
            # Calculate total size
            total_size = sum(stat['size'] for stat in extension_stats.values())
            
            # Sort by size descending
            sorted_stats = sorted(
                extension_stats.items(),
                key=lambda x: x[1]['size'],
                reverse=True
            )
            
            # Add rows to table (top 20)
            for ext, data in sorted_stats[:20]:
                count = data['count']
                size = data['size']
                percentage = (size / total_size * 100) if total_size > 0 else 0
                
                ext_display = ext if ext else "Other"
                size_display = self.format_size(size)
                
                table.add_row(
                    ext_display,
                    str(count),
                    size_display,
                    f"{percentage:.1f}%"
                )
        except Exception as e:
            pass
    
    async def _load_children_async(self, tree_node, file_node: FileNode) -> None:
        """Load children of a folder asynchronously."""
        try:
            # Scan directory in background
            await asyncio.to_thread(
                self._scan_directory, file_node
            )
            
            # Update tree on main thread
            if file_node.children:
                # Remove all children (including placeholder)
                for child in list(tree_node.children):
                    tree_node.children.remove(child)
                
                # Sort and add children
                sorted_children = sorted(
                    file_node.children,
                    key=lambda x: x.total_size if x.is_dir else x.size,
                    reverse=True
                )
                
                for child in sorted_children:
                    label = self.format_node_label(child)
                    new_tree_node = tree_node.add(label, data=child)
                    
                    # Add placeholder for directories (to show they're expandable)
                    if child.is_dir and not child.is_scanned:
                        new_tree_node.add("[loading]", data=None)
                
                # Refresh to show changes
                self.refresh()
        except Exception as e:
            pass
    
    def _scan_directory(self, node: FileNode) -> None:
        """Scan a single directory and populate its children."""
        # If already scanned, skip
        if node.is_scanned:
            return
        
        if not node.is_dir:
            return
        
        try:
            entries = os.listdir(node.path)
        except (PermissionError, OSError):
            node.is_scanned = True
            return
        
        for entry in entries:
            try:
                full_path = os.path.join(node.path, entry)
                
                if os.path.islink(full_path):
                    continue
                
                if os.path.isdir(full_path):
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        is_dir=True,
                        parent=node,
                        is_scanned=False  # Mark subdirectories as not yet scanned
                    )
                    node.children.append(child)
                else:
                    try:
                        size = os.path.getsize(full_path)
                    except (OSError, PermissionError):
                        size = 0
                    
                    child = FileNode(
                        name=entry,
                        path=full_path,
                        size=size,
                        is_dir=False,
                        parent=node,
                        is_scanned=True  # Files are "scanned" (no children)
                    )
                    node.children.append(child)
            except Exception:
                pass
        
        node.is_scanned = True
    
    def update_statistics(self, node: FileNode) -> None:
        """Update statistics table from node."""
        try:
            stats = self.file_type_analyzer.get_statistics(node)
            
            table = self.query_one("#stats-table", DataTable)
            table.clear()
            
            # Store extension data for later path display
            self.extension_data = {}
            
            if stats:
                # stats is list of (extension, stats_dict) tuples
                for ext, data in stats[:20]:  # Top 20
                    count = data['count']
                    size = data['size']
                    percentage = data.get('percentage_by_size', 0)  # Use correct key
                    files = data.get('files', [])  # Get file paths
                    
                    # Store for later access
                    self.extension_data[ext] = files
                    
                    ext_display = ext if ext else "Other"
                    size_display = self.format_size(size)
                    
                    table.add_row(
                        ext_display,
                        str(count),
                        size_display,
                        f"{percentage:.1f}%"
                    )
        except Exception as e:
            self.notify(f"Stats error: {e}", severity="error")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle statistics table row selection - show file paths in separate grid."""
        try:
            # Determine which table sent the event by checking widget
            if not hasattr(event, 'control'):
                return
            
            stats_table = self.query_one("#stats-table", DataTable)
            paths_table = self.query_one("#paths-table", DataTable)
            
            # Only process stats table events
            if event.control != stats_table:
                return
            
            row_key = event.row_key
            
            # Get extension from table
            row_data = stats_table.get_row(row_key)
            # Extension is in first column
            extension = row_data[0].plain if hasattr(row_data[0], 'plain') else str(row_data[0])
            
            # Normalize the extension for matching (handle both ".txt" and "txt" formats)
            # Check if extension exists in extension_data
            if extension not in self.extension_data:
                # Try with dot prefix
                if f".{extension}" in self.extension_data:
                    extension = f".{extension}"
                # Try without dot
                elif extension.startswith(".") and extension[1:] in self.extension_data:
                    extension = extension[1:]
                else:
                    return
            
            # Get file paths for this extension
            data = self.extension_data.get(extension, {})
            if isinstance(data, dict):
                files = data.get('files', [])
            else:
                # Legacy format: extension_data[ext] is just the files list
                files = data if isinstance(data, list) else []
            
            if not files:
                return
            
            # Update paths table with all file paths
            paths_table.clear()
            
            # Show all file paths
            for file_path in files:
                paths_table.add_row(file_path)
            
            # Update header to show count
            paths_header = self.query_one("#paths-header", Label)
            paths_header.update(f"[bold][ File Paths - {extension} ({len(files)} files) ][/bold]")
                
        except Exception as e:
            # Silently handle errors
            pass


    
    def _get_file_metadata(self, extension: str) -> dict:
        """Get metadata about file type (popularity, safety, etc.)."""
        # Common file extensions and their properties
        common_extensions = {
            # System & very common
            '.txt': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Text'},
            '.pdf': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Document'},
            '.docx': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Document'},
            '.doc': {'popularity': 'High', 'safety': 'Safe', 'type': 'Document'},
            '.xlsx': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Spreadsheet'},
            '.xls': {'popularity': 'High', 'safety': 'Safe', 'type': 'Spreadsheet'},
            '.pptx': {'popularity': 'High', 'safety': 'Safe', 'type': 'Presentation'},
            '.jpg': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Image'},
            '.jpeg': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Image'},
            '.png': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Image'},
            '.gif': {'popularity': 'High', 'safety': 'Safe', 'type': 'Image'},
            '.mp4': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Video'},
            '.mp3': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Audio'},
            '.zip': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Archive'},
            '.rar': {'popularity': 'High', 'safety': 'Safe', 'type': 'Archive'},
            '.7z': {'popularity': 'Medium', 'safety': 'Safe', 'type': 'Archive'},
            
            # Code (safe)
            '.py': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Code'},
            '.js': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Code'},
            '.html': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Code'},
            '.css': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Code'},
            '.json': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Data'},
            '.xml': {'popularity': 'High', 'safety': 'Safe', 'type': 'Data'},
            '.yaml': {'popularity': 'High', 'safety': 'Safe', 'type': 'Data'},
            '.yml': {'popularity': 'High', 'safety': 'Safe', 'type': 'Data'},
            '.md': {'popularity': 'Very High', 'safety': 'Safe', 'type': 'Documentation'},
            '.log': {'popularity': 'High', 'safety': 'Safe', 'type': 'Log'},
            
            # Potentially risky
            '.exe': {'popularity': 'Very High', 'safety': 'Warning', 'type': 'Executable'},
            '.dll': {'popularity': 'Very High', 'safety': 'Warning', 'type': 'Library'},
            '.bat': {'popularity': 'High', 'safety': 'Warning', 'type': 'Script'},
            '.cmd': {'popularity': 'High', 'safety': 'Warning', 'type': 'Script'},
            '.ps1': {'popularity': 'High', 'safety': 'Warning', 'type': 'Script'},
            '.vbs': {'popularity': 'Medium', 'safety': 'Risky', 'type': 'Script'},
            '.scr': {'popularity': 'Low', 'safety': 'Risky', 'type': 'Screensaver'},
            '.msi': {'popularity': 'High', 'safety': 'Warning', 'type': 'Installer'},
        }
        
        ext_lower = extension.lower()
        return common_extensions.get(ext_lower, {
            'popularity': 'Unknown',
            'safety': 'Unknown',
            'type': 'Unknown'
        })
    
    def update_analysis_panel(self) -> None:
        """Update analysis panel with Copilot intelligence and metadata."""
        if not self.selected_node:
            return
        
        try:
            panel = self.query_one("#analysis-panel", Static)
            
            lines = []
            
            # Handle both dict and FileNode data
            if isinstance(self.selected_node, dict):
                self.update_analysis_panel_from_dict(self.selected_node)
                return
            
            lines.append(f"[bold cyan]{self.selected_node.name}[/bold cyan]")
            
            # File info
            size_val = self.selected_node.size if hasattr(self.selected_node, 'size') else self.selected_node.total_size
            lines.append(f"Size: [bold]{self.format_size(size_val)}[/bold]")
            
            if hasattr(self.selected_node, 'children') and self.selected_node.children:
                lines.append(f"Items: [bold]{len(self.selected_node.children)}[/bold]")
            
            # Get file type analysis and metadata
            extension = self.selected_node.get_extension() if hasattr(self.selected_node, 'get_extension') else ''
            if extension:
                # Get file metadata
                metadata = self._get_file_metadata(extension)
                
                # Safety status
                safety = metadata.get('safety', 'Unknown')
                if safety == 'Safe':
                    safety_color = 'green'
                    safety_icon = '✓'
                elif safety == 'Warning':
                    safety_color = 'yellow'
                    safety_icon = '⚠'
                elif safety == 'Risky':
                    safety_color = 'red'
                    safety_icon = '✗'
                else:
                    safety_color = 'cyan'
                    safety_icon = '?'
                
                lines.append("")
                lines.append(f"[bold cyan]File Metadata:[/bold cyan]")
                lines.append(f"Type: [cyan]{metadata.get('type', 'Unknown')}[/cyan]")
                lines.append(f"Popularity: [cyan]{metadata.get('popularity', 'Unknown')}[/cyan]")
                lines.append(f"[{safety_color}]{safety_icon} Safety: {safety}[/{safety_color}]")
                
                # Get Copilot analysis
                try:
                    analysis = self.copilot_analyzer.analyze_file_type(
                        extension,
                        [],
                        0,
                        size_val
                    )
                    lines.append(f"\n[bold cyan]Analysis:[/bold cyan]")
                    lines.append(f"{analysis}")
                except:
                    pass
            
            panel.update("\n".join(lines))
            
        except Exception as e:
            pass  # Panel may not exist yet
    
    def update_analysis_panel_from_dict(self, node_dict: dict) -> None:
        """Update analysis panel from dict-based node data."""
        try:
            panel = self.query_one("#analysis-panel", Static)
            
            lines = []
            name = node_dict.get("name", "Unknown")
            size = node_dict.get("size", 0)
            is_dir = node_dict.get("is_dir", False)
            
            lines.append(f"[bold cyan]{name}[/bold cyan]")
            lines.append(f"Type: [cyan]{'Directory' if is_dir else 'File'}[/cyan]")
            lines.append(f"Size: [bold]{self.format_size(size)}[/bold]")
            lines.append(f"Path: [dim]{node_dict.get('path', '')}[/dim]")
            
            # Get metadata for files
            if not is_dir and name:
                # Extract extension from name
                if '.' in name:
                    extension = '.' + name.split('.')[-1]
                    metadata = self._get_file_metadata(extension)
                    
                    # Safety status
                    safety = metadata.get('safety', 'Unknown')
                    if safety == 'Safe':
                        safety_color = 'green'
                        safety_icon = '✓'
                    elif safety == 'Warning':
                        safety_color = 'yellow'
                        safety_icon = '⚠'
                    elif safety == 'Risky':
                        safety_color = 'red'
                        safety_icon = '✗'
                    else:
                        safety_color = 'cyan'
                        safety_icon = '?'
                    
                    lines.append("")
                    lines.append(f"[bold cyan]File Info:[/bold cyan]")
                    lines.append(f"Type: [cyan]{metadata.get('type', 'Unknown')}[/cyan]")
                    lines.append(f"Popularity: [cyan]{metadata.get('popularity', 'Unknown')}[/cyan]")
                    lines.append(f"[{safety_color}]{safety_icon} Safety: {safety}[/{safety_color}]")
            
            panel.update("\n".join(lines))
        except Exception as e:
            pass  # Panel may not exist yet
    
    def update_analysis_panel_from_filenode(self, file_node: FileNode) -> None:
        """Update analysis panel from FileNode."""
        # FileNode analysis is handled by the existing update_analysis_panel() method
        # Just call it with self.selected_node set to the FileNode
        self.selected_node = file_node
        self.update_analysis_panel()
    
    def update_statistics_from_filenode(self, file_node: FileNode) -> None:
        """Update statistics from FileNode."""
        # FileNode statistics are handled by the existing update_statistics() method
        self.update_statistics(file_node)
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold cyan]FEATURES[/bold cyan]

Real-time file tree, analysis & statistics with AI-powered content evaluation.
Deep directory insights, pattern detection, and intelligent file categorization.

[bold cyan]KEYBOARD SHORTCUTS[/bold cyan]

q - Quit application
h - Show this help
s - Show statistics
a - Analyze selected item (file type)
d - Deep analysis of file contents using Copilot

[bold cyan]MOUSE INTERACTION[/bold cyan]

Single-click - Select item
Double-click - Expand/collapse folder
Click & drag on borders - Resize panels

[bold cyan]INTERFACE[/bold cyan]

LEFT: Directory tree with sizes (drag border to resize)
RIGHT TOP: File type statistics + Copilot analysis
RIGHT BOTTOM: File paths for selected type

[bold cyan]ANALYSIS FEATURES[/bold cyan]

'a' key: Shows file type classification
'd' key: Reads file contents + Copilot analysis
        (Works with text files, shows preview + AI insights)

Click items in the tree to navigate and view details.
        """
        self.notify(help_text, title="Help", timeout=15)
    
    def action_show_stats(self) -> None:
        """Show statistics panel."""
        self.notify("Statistics displayed in the right panel", timeout=5)
    
    def action_select_tree_node(self) -> None:
        """Select the currently-focused tree node."""
        try:
            tree = self.query_one("#file-tree", Tree)
            node = tree.cursor_node
            if node:
                # Manually trigger node selection
                self.on_tree_node_selected(Tree.NodeSelected(node))
        except Exception:
            pass
    
    def action_analyze(self) -> None:
        """Analyze selected item."""
        if not self.selected_node:
            self.notify("No item selected", severity="warning")
            return
        
        try:
            # Get file type info
            extension = self.selected_node.get_extension() if hasattr(self.selected_node, 'get_extension') else 'unknown'
            
            analysis = self.copilot_analyzer.analyze_file_type(
                extension,
                [],  # file_samples
                0,   # file_count
                self.selected_node.size
            )
            
            # Show analysis in notification instead of panel
            self.notify(f"[bold]{extension}[/bold] Analysis:\n{analysis}", timeout=10)
            
        except Exception as e:
            self.notify(f"Analysis error: {e}", severity="error")
    
    def action_deep_analyze(self) -> None:
        """Perform deep analysis of file contents using Copilot."""
        if not self.selected_node:
            self.notify("No item selected", severity="warning")
            return
        
        # Check if it's a directory
        is_dir = False
        file_size = 0
        file_name = ''
        
        if isinstance(self.selected_node, dict):
            # Dict-based node from lazy-loading
            is_dir = self.selected_node.get('is_dir', False)
            file_size = self.selected_node.get('size', 0)
            file_name = self.selected_node.get('name', '')
        else:
            # FileNode object
            is_dir = getattr(self.selected_node, 'is_dir', False)
            file_size = getattr(self.selected_node, 'size', 0)
            file_name = getattr(self.selected_node, 'name', '')
        
        # Can't read directories
        if is_dir:
            self.notify("Cannot read directory contents. Select a file.", severity="warning")
            return
        
        # Check file size limit for Copilot upload
        copilot_upload_limit = 5 * 1024 * 1024  # 5MB
        if file_size > copilot_upload_limit:
            size_mb = file_size / (1024 * 1024)
            limit_mb = copilot_upload_limit / (1024 * 1024)
            self.notify(
                f"[red]File too large for Copilot analysis[/red]\n\n"
                f"File size: {size_mb:.1f}MB\n"
                f"Copilot limit: {limit_mb:.0f}MB\n\n"
                f"Cannot upload files larger than {limit_mb:.0f}MB to Copilot service.",
                severity="error",
                timeout=8
            )
            return
        
        # Show immediate popup notification at bottom right
        self.notify(
            "[bold yellow]Deep Analysis executing via Copilot[/bold yellow]\n"
            "[dim]Please be patient...[/dim]",
            timeout=3
        )
        
        try:
            # Show immediate status in the analysis panel
            try:
                panel = self.query_one("#analysis-panel", Static)
                panel.update(
                    "[bold cyan]⏳ Analysing file...[/bold cyan]\n\n"
                    "[dim]Processing with Copilot AI[/dim]\n\n"
                    "[yellow]Uploading:[/yellow]\n"
                    "• Full file content (up to 5MB)\n"
                    "• All file types supported\n"
                    "• Timeout: 30-45 seconds\n\n"
                    "[dim]Please wait...[/dim]"
                )
                self.refresh()
            except:
                pass
            
            # Read file contents
            file_contents = self._read_file_safely()
            if not file_contents:
                self.notify("Could not read file contents", severity="warning")
                return
            
            # Get file extension
            if '.' in file_name:
                file_ext = '.' + file_name.split('.')[-1].lower()
            else:
                file_ext = 'unknown'
            
            # Get intelligent analysis of the content
            analysis = self.copilot_analyzer.analyze_file_contents(
                file_contents,
                file_name,
                file_ext
            )
            
            if not analysis or not analysis.strip():
                self.notify("[yellow]No analysis returned from Copilot[/yellow]", severity="warning")
                return
            
            # Update deep analysis panel with intelligent analysis results
            try:
                # Query the new deep analysis panel widget
                panel = self.query_one("#deep-analysis-panel", Static)
                
                # Update the panel with the analysis
                panel.update(analysis)
                
                # Scroll to top of the analysis
                scroll = self.query_one("#deep-analysis-scroll", VerticalScroll)
                scroll.scroll_home()
                
                # Give user feedback with char count
                self.notify(f"✓ Deep Analysis Complete ({len(analysis)} chars)", timeout=2)
                
            except Exception as panel_error:
                # Log the actual error with full details
                import traceback
                error_msg = f"{type(panel_error).__name__}: {panel_error}"
                tb = traceback.format_exc()
                self.notify(f"[red]Panel error: {error_msg}[/red]", severity="error", timeout=5)
                
                # Fallback: show in notification instead
                analysis_preview = analysis[:400].replace('\n', ' ')
                self.notify(f"[bold cyan]Analysis Preview:[/bold cyan]\n{analysis_preview}...", timeout=30)
            
        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {e}"
            self.notify(f"[red]Analysis error: {error_msg}[/red]", severity="error", timeout=5)
    

    def _read_file_safely(self) -> str:
        """Read file contents safely with size limits."""
        if not self.selected_node:
            return ""
        
        # Handle dict-based nodes (from lazy-loading)
        if isinstance(self.selected_node, dict):
            file_path = self.selected_node.get('path', '')
            file_size = self.selected_node.get('size', 0)
            file_name = self.selected_node.get('name', '')
        # Handle FileNode objects (legacy)
        else:
            if not hasattr(self.selected_node, 'path'):
                return ""
            file_path = self.selected_node.path
            file_size = getattr(self.selected_node, 'size', 0)
            file_name = getattr(self.selected_node, 'name', '')
        
        if not file_path:
            return ""
        
        try:
            # Copilot limit for file uploads
            copilot_upload_limit = 5 * 1024 * 1024  # 5MB
            
            if file_size > copilot_upload_limit:
                return f"[red]File too large for Copilot analysis ({self.format_size(file_size)})[/red]\n(Copilot limit: 5MB)"
            
            # Read the FULL file for analysis - no truncation, no filtering
            # Copilot can handle binary files intelligently
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Try to decode as UTF-8, fall back to latin-1 for binary files
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1', errors='replace')
        
        except FileNotFoundError:
            return "[red]File not found[/red]"
        except PermissionError:
            return "[red]Permission denied - cannot read file[/red]"
        except Exception as e:
            return f"[red]Error reading file: {str(e)[:100]}[/red]"


