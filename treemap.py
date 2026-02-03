"""
Treemap Layout Algorithm - Converts hierarchical data to 2D rectangles
Uses squarify algorithm for better aspect ratios
"""

from dataclasses import dataclass
from typing import List
from disk_scanner import FileNode


@dataclass
class Rectangle:
    """Represents a rectangular region in the terminal."""
    x: int
    y: int
    width: int
    height: int
    node: FileNode
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (width/height), minimizing extreme values."""
        if self.height == 0:
            return float('inf')
        ratio = self.width / self.height
        return max(ratio, 1/ratio) if ratio > 0 else float('inf')


class TreemapLayout:
    """Generates treemap layout for terminal display."""
    
    @staticmethod
    def calculate(node: FileNode, x: int, y: int, width: int, height: int,
                  max_items: int = 20) -> List[Rectangle]:
        """
        Calculate treemap layout for a node's children.
        
        Args:
            node: FileNode to create treemap for
            x, y: Top-left corner coordinates
            width, height: Available space
            max_items: Maximum items to display (show only largest)
        
        Returns:
            List of Rectangle objects representing layout
        """
        if not node.children or width <= 0 or height <= 0:
            return []
        
        # Get top N children by size
        children = node.get_sorted_children()[:max_items]
        
        if not children:
            return []
        
        # Calculate total size
        total_size = sum(child.total_size for child in children)
        if total_size == 0:
            return []
        
        rectangles = []
        TreemapLayout._squarify(
            children, 
            total_size,
            x, y, width, height,
            rectangles
        )
        
        return rectangles
    
    @staticmethod
    def _squarify(children: List[FileNode], total_size: int,
                  x: int, y: int, width: int, height: int,
                  rectangles: List[Rectangle],
                  row: List[tuple] = None):
        """
        Recursive squarify algorithm for better aspect ratios.
        Adapted from original squarify algorithm.
        """
        if row is None:
            row = []
        
        if not children:
            return
        
        if len(children) == 0:
            TreemapLayout._layout_row(row, x, y, width, height, rectangles)
            return
        
        # Use horizontal or vertical split based on dimensions
        if width >= height:
            # Horizontal layout
            row_width = width
            child_height = height
            
            row.append(children[0])
            row_size = sum(c.total_size for c in row)
            
            # Check if we should start a new row
            if len(children) > 1:
                next_ratio = TreemapLayout._worst_ratio(row, row_size, row_width, child_height)
                next_with_child = TreemapLayout._worst_ratio(
                    row + [children[1]],
                    row_size + children[1].total_size,
                    row_width,
                    child_height
                )
                
                if next_ratio < next_with_child:
                    # Finalize row
                    TreemapLayout._layout_row(row, x, y, row_width, child_height, rectangles)
                    TreemapLayout._squarify(
                        children[1:],
                        total_size - row_size,
                        x, y + child_height,
                        width, height - child_height,
                        rectangles
                    )
                else:
                    # Continue row
                    TreemapLayout._squarify(
                        children[1:],
                        total_size,
                        x, y, width, height,
                        rectangles,
                        row
                    )
            else:
                # Last child
                TreemapLayout._layout_row(row, x, y, row_width, child_height, rectangles)
        
        else:
            # Vertical layout (similar logic)
            row_height = height
            child_width = width
            
            row.append(children[0])
            row_size = sum(c.total_size for c in row)
            
            if len(children) > 1:
                next_ratio = TreemapLayout._worst_ratio(row, row_size, child_width, row_height)
                next_with_child = TreemapLayout._worst_ratio(
                    row + [children[1]],
                    row_size + children[1].total_size,
                    child_width,
                    row_height
                )
                
                if next_ratio < next_with_child:
                    TreemapLayout._layout_row(row, x, y, child_width, row_height, rectangles)
                    TreemapLayout._squarify(
                        children[1:],
                        total_size - row_size,
                        x + child_width, y,
                        width - child_width, height,
                        rectangles
                    )
                else:
                    TreemapLayout._squarify(
                        children[1:],
                        total_size,
                        x, y, width, height,
                        rectangles,
                        row
                    )
            else:
                TreemapLayout._layout_row(row, x, y, child_width, row_height, rectangles)
    
    @staticmethod
    def _layout_row(row: List[FileNode], x: int, y: int, width: int, height: int,
                    rectangles: List[Rectangle]):
        """Layout a row of items."""
        if not row:
            return
        
        total_size = sum(node.total_size for node in row)
        if total_size == 0:
            return
        
        current_x = x
        
        for node in row:
            ratio = node.total_size / total_size
            node_width = int(width * ratio)
            
            rect = Rectangle(
                x=current_x,
                y=y,
                width=node_width,
                height=height,
                node=node
            )
            rectangles.append(rect)
            current_x += node_width
    
    @staticmethod
    def _worst_ratio(row: List[FileNode], total_size: int, 
                     width: int, height: int) -> float:
        """Calculate worst aspect ratio in row."""
        if not row or total_size == 0:
            return float('inf')
        
        ratios = []
        current_x = 0
        
        for node in row:
            ratio = node.total_size / total_size
            node_width = int(width * ratio)
            
            if node_width > 0 and height > 0:
                aspect = max(node_width / height, height / node_width)
                ratios.append(aspect)
        
        return max(ratios) if ratios else float('inf')
