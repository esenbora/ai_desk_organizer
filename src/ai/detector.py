import cv2
import numpy as np
from ultralytics import YOLO
import json

class ObjectDetector:
    def __init__(self):
        # Load YOLOv8 model
        self.model = YOLO('yolov8n.pt')  # nano version for speed
        
        # Mapping of YOLO classes to our desk item categories
        self.class_mapping = {
            'laptop': 'laptop',
            'cell phone': 'phone',
            'book': 'notebook',
            'cup': 'cup',
            'mouse': 'mouse',
            'keyboard': 'keyboard',
            'tv': 'monitor',  # TV often used as monitor
            'remote': 'mouse',  # Sometimes detected as remote
        }
    
    def detect_objects(self, image_path):
        """
        Detect objects in the image using YOLOv8
        Returns list of detected items with their positions
        """
        results = self.model(image_path)
        detected_items = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Get class name
                    class_name = self.model.names[class_id]
                    
                    # Map to our categories if recognized
                    if class_name in self.class_mapping:
                        item_slug = self.class_mapping[class_name]
                        
                        # Calculate center and dimensions
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        width = x2 - x1
                        height = y2 - y1
                        
                        detected_items.append({
                            'slug': item_slug,
                            'x': center_x,
                            'y': center_y,
                            'width': width,
                            'height': height,
                            'confidence': confidence,
                            'rotation': 0,
                            'original_class': class_name
                        })
        
        return detected_items
    
    def add_manual_item(self, item_slug, x, y, width=50, height=50):
        """
        Add a manually identified item
        """
        return {
            'slug': item_slug,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'confidence': 1.0,
            'rotation': 0,
            'original_class': item_slug
        }