import cv2
import numpy as np
import json

class CalibrationManager:
    def __init__(self):
        self.card_width_cm = 8.5  # Standard credit card width
        self.card_height_cm = 5.4  # Standard credit card height
        self.calibration_points = []
        self.scale_factor = None
        self.desk_corners = []
    
    def add_calibration_point(self, x, y):
        """Add a calibration point (corner of the reference object)"""
        self.calibration_points.append((x, y))
        return len(self.calibration_points)
    
    def add_desk_corner(self, x, y):
        """Add a desk corner point"""
        self.desk_corners.append((x, y))
        return len(self.desk_corners)
    
    def is_calibration_complete(self):
        """Check if we have 4 calibration points"""
        return len(self.calibration_points) == 4
    
    def is_desk_complete(self):
        """Check if we have 4 desk corners"""
        return len(self.desk_corners) == 4
    
    def calculate_scale_factor(self):
        """
        Calculate pixels per cm from the calibration points
        Assumes points are ordered: top-left, top-right, bottom-right, bottom-left
        """
        if not self.is_calibration_complete():
            return None
        
        # Calculate pixel dimensions of the detected card
        top_left = self.calibration_points[0]
        top_right = self.calibration_points[1]
        bottom_right = self.calibration_points[2]
        bottom_left = self.calibration_points[3]
        
        # Calculate width in pixels (average of top and bottom edges)
        width_pixels_top = np.linalg.norm(np.array(top_right) - np.array(top_left))
        width_pixels_bottom = np.linalg.norm(np.array(bottom_right) - np.array(bottom_left))
        width_pixels = (width_pixels_top + width_pixels_bottom) / 2
        
        # Calculate height in pixels (average of left and right edges)
        height_pixels_left = np.linalg.norm(np.array(bottom_left) - np.array(top_left))
        height_pixels_right = np.linalg.norm(np.array(bottom_right) - np.array(top_right))
        height_pixels = (height_pixels_left + height_pixels_right) / 2
        
        # Calculate scale factors
        scale_x = width_pixels / self.card_width_cm
        scale_y = height_pixels / self.card_height_cm
        
        # Use average scale factor
        self.scale_factor = (scale_x + scale_y) / 2
        return self.scale_factor
    
    def pixels_to_cm(self, pixels):
        """Convert pixels to centimeters using the calculated scale factor"""
        if self.scale_factor is None:
            return None
        return pixels / self.scale_factor
    
    def cm_to_pixels(self, cm):
        """Convert centimeters to pixels using the calculated scale factor"""
        if self.scale_factor is None:
            return None
        return cm * self.scale_factor
    
    def get_desk_bounds_json(self):
        """Get desk corners as JSON string for storage"""
        return json.dumps(self.desk_corners)
    
    def reset_calibration(self):
        """Reset all calibration points"""
        self.calibration_points = []
        self.desk_corners = []
        self.scale_factor = None
    
    def transform_to_desk_coordinates(self, x, y):
        """
        Transform image coordinates to desk coordinate system
        Returns (x_cm, y_cm) relative to desk center
        """
        if not self.is_desk_complete() or self.scale_factor is None:
            return None, None
        
        # Calculate desk center
        desk_center_x = sum(corner[0] for corner in self.desk_corners) / 4
        desk_center_y = sum(corner[1] for corner in self.desk_corners) / 4
        
        # Convert to cm relative to desk center
        x_cm = self.pixels_to_cm(x - desk_center_x)
        y_cm = self.pixels_to_cm(y - desk_center_y)
        
        return x_cm, y_cm
    
    def get_desk_dimensions_cm(self):
        """Get desk dimensions in centimeters"""
        if not self.is_desk_complete() or self.scale_factor is None:
            return None, None
        
        # Calculate desk dimensions
        top_left = self.desk_corners[0]
        top_right = self.desk_corners[1]
        bottom_right = self.desk_corners[2]
        bottom_left = self.desk_corners[3]
        
        width_pixels = np.linalg.norm(np.array(top_right) - np.array(top_left))
        height_pixels = np.linalg.norm(np.array(bottom_left) - np.array(top_left))
        
        width_cm = self.pixels_to_cm(width_pixels)
        height_cm = self.pixels_to_cm(height_pixels)
        
        return width_cm, height_cm