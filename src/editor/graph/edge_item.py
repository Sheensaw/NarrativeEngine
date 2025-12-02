
# src/editor/graph/edge_item.py
import math
from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import QPointF, Qt, QLineF
from PyQt6.QtGui import QPen, QColor, QPainterPath, QPolygonF

from src.core.definitions import COLORS

class EdgeItem(QGraphicsPathItem):
    """
    Visual connection between two nodes.
    Supports single direction (A->B) and bi-directional (A<->B).
    """

    def __init__(self, source_node, target_node, is_bidirectional=False):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.is_bidirectional = is_bidirectional

        # Config
        self._color = QColor(COLORS["connection"])
        self._pen = QPen(self._color)
        self._pen.setWidthF(2.0)
        self.setPen(self._pen)
        self.setZValue(-1) # Behind nodes

        self.arrow_head_dest = None
        self.arrow_head_src = None

        self.update_path()

    def update_path(self):
        """Calculates path and arrows."""
        if not self.source_node or not self.target_node:
            return

        # Get centers
        src_rect = self.source_node.sceneBoundingRect()
        dst_rect = self.target_node.sceneBoundingRect()
        src_center = src_rect.center()
        dst_center = dst_rect.center()

        # Calculate Intersections for Start and End points
        # We use the line connecting centers to find the best intersection point on the rects
        start_res = self._get_intersection(dst_center, src_center, src_rect)
        end_res = self._get_intersection(src_center, dst_center, dst_rect)

        # Fallback to centers if intersection fails (e.g. overlap)
        if start_res:
            start_point, start_normal = start_res
        else:
            start_point, start_normal = src_center, QPointF(1, 0) # Default right

        if end_res:
            end_point, end_normal = end_res
        else:
            end_point, end_normal = dst_center, QPointF(-1, 0) # Default left

        path = QPainterPath(start_point)
        
        # Cubic Bezier for smooth connection
        dist = math.sqrt((end_point.x() - start_point.x())**2 + (end_point.y() - start_point.y())**2)
        
        # Adjust control points based on normals
        # Project control points out along the normal vector
        tangent_length = min(dist * 0.5, 150.0)
        if tangent_length < 50: tangent_length = 50

        ctrl1 = start_point + start_normal * tangent_length
        ctrl2 = end_point + end_normal * tangent_length
        
        path.cubicTo(ctrl1, ctrl2, end_point)
        self.setPath(path)
        
        # Calculate Arrow Heads at Endpoints
        # Destination Arrow
        # Use the vector from ctrl2 to end_point for angle
        self.arrow_head_dest = self._get_arrow_poly(ctrl2, end_point)
        
        # Source Arrow (Bidirectional)
        if self.is_bidirectional:
            self.arrow_head_src = self._get_arrow_poly(ctrl1, start_point)
        else:
            self.arrow_head_src = None

    def _get_intersection(self, p1, p2, rect):
        """
        Finds the intersection point between line segment p1-p2 and the rectangle rect.
        Returns (QPointF, QPointF) -> (Intersection Point, Normal Vector) or None.
        """
        l = QLineF(p1, p2)
        
        # Rectangle edges and their normals (pointing OUTWARDS)
        edges_info = [
            (QLineF(rect.topLeft(), rect.bottomLeft()), QPointF(-1, 0)),   # Left
            (QLineF(rect.topRight(), rect.bottomRight()), QPointF(1, 0)),  # Right
            (QLineF(rect.topLeft(), rect.topRight()), QPointF(0, -1)),     # Top
            (QLineF(rect.bottomLeft(), rect.bottomRight()), QPointF(0, 1)) # Bottom
        ]
        
        for edge, normal in edges_info:
            # QLineF.intersects returns (IntersectionType, intersectionPoint)
            type, intersection_point = l.intersects(edge)
            if type == QLineF.IntersectionType.BoundedIntersection:
                return intersection_point, normal
                
        return None

    def _get_arrow_poly(self, ctrl_point, end_point):
        """Calculates arrow polygon at end_point pointing from ctrl_point."""
        arrow_size = 15  # Increased size
        arrow_angle = math.pi / 6  # 30 degrees

        # Calculate angle from ctrl_point to end_point
        dx = end_point.x() - ctrl_point.x()
        dy = end_point.y() - ctrl_point.y()
        angle = math.atan2(dy, dx)

        # Arrow points back from end_point
        # Point 1
        p1_x = end_point.x() - arrow_size * math.cos(angle - arrow_angle)
        p1_y = end_point.y() - arrow_size * math.sin(angle - arrow_angle)
        p1 = QPointF(p1_x, p1_y)

        # Point 2
        p2_x = end_point.x() - arrow_size * math.cos(angle + arrow_angle)
        p2_y = end_point.y() - arrow_size * math.sin(angle + arrow_angle)
        p2 = QPointF(p2_x, p2_y)

        return QPolygonF([end_point, p1, p2])

    def boundingRect(self):
        """
        Override to include arrowheads which are drawn manually in paint().
        """
        rect = super().boundingRect()
        
        # Add arrowheads to the bounding rect
        if self.arrow_head_dest:
            rect = rect.united(self.arrow_head_dest.boundingRect())
            
        if self.is_bidirectional and self.arrow_head_src:
            rect = rect.united(self.arrow_head_src.boundingRect())
            
        # Add a small margin for pen width and anti-aliasing
        margin = 5.0
        return rect.adjusted(-margin, -margin, margin, margin)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        if self.arrow_head_dest:
            painter.drawPolygon(self.arrow_head_dest)
            
        if self.is_bidirectional and self.arrow_head_src:
            painter.drawPolygon(self.arrow_head_src)
