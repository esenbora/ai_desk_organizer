import cv2
import numpy as np
from ultralytics import YOLO
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ObjectDetector:
    def __init__(self, model_path=None):
        try:
            # Load YOLOv8 model
            model_path = model_path or Config.YOLO_MODEL_NAME
            logger.info(f"Loading YOLO model: {model_path}...")
            self.model = YOLO(model_path)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}", exc_info=True)
            raise RuntimeError(f"Could not initialize object detector: {e}")

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
        try:
            if not image_path or not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            logger.info(f"Starting object detection on: {image_path}")
            results = self.model(image_path)
            detected_items = []

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        try:
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            confidence = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())

                            # Get class name
                            class_name = self.model.names[class_id]

                            # Map to our categories if recognized
                            if class_name in self.class_mapping:
                                item_slug = self.class_mapping[class_name]

                                # Calculate center and dimensions
                                center_x = float((x1 + x2) / 2)
                                center_y = float((y1 + y2) / 2)
                                width = float(x2 - x1)
                                height = float(y2 - y1)

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
                                logger.debug(f"Detected {item_slug} at ({center_x:.1f}, {center_y:.1f}) with confidence {confidence:.2f}")
                        except Exception as e:
                            logger.warning(f"Error processing detection box: {e}")
                            continue

            logger.info(f"Detection complete: {len(detected_items)} items found")
            return detected_items

        except Exception as e:
            logger.error(f"Object detection failed: {e}", exc_info=True)
            raise RuntimeError(f"Detection error: {e}")
    
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