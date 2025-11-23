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
            # Core peripherals
            'laptop': 'laptop',
            'mouse': 'mouse',
            'keyboard': 'keyboard',
            'tv': 'monitor',  # Large displays often detected as TV

            # Communication devices
            'cell phone': 'phone',

            # Desk items
            'book': 'notebook',
            'cup': 'cup',
            'bottle': 'bottle',

            # Furniture & accessories
            'chair': 'chair',
            'clock': 'clock',

            # Note: Removed bad mappings
            # 'remote': 'mouse' - This was incorrect and caused false positives
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

                            # Filter by confidence threshold
                            if confidence < Config.YOLO_CONFIDENCE_THRESHOLD:
                                logger.debug(f"Skipping {class_name} with low confidence {confidence:.2f}")
                                continue

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

            # Remove duplicates - keep highest confidence for each item type at similar locations
            detected_items = self._remove_duplicates(detected_items)

            logger.info(f"Detection complete: {len(detected_items)} items found")
            return detected_items

        except Exception as e:
            logger.error(f"Object detection failed: {e}", exc_info=True)
            raise RuntimeError(f"Detection error: {e}")

    def _remove_duplicates(self, items, distance_threshold=100):
        """
        Remove duplicate detections of the same item type at similar locations.
        Keeps the detection with highest confidence.

        Args:
            items: List of detected items
            distance_threshold: Maximum distance (pixels) to consider items as duplicates

        Returns:
            Filtered list with duplicates removed
        """
        if not items:
            return items

        # Group items by slug
        grouped = {}
        for item in items:
            slug = item['slug']
            if slug not in grouped:
                grouped[slug] = []
            grouped[slug].append(item)

        # For each slug group, remove duplicates
        filtered_items = []
        for slug, slug_items in grouped.items():
            if len(slug_items) == 1:
                filtered_items.append(slug_items[0])
                continue

            # Sort by confidence (highest first)
            slug_items.sort(key=lambda x: x['confidence'], reverse=True)

            # Keep items that are far enough apart
            kept_items = []
            for item in slug_items:
                is_duplicate = False
                for kept in kept_items:
                    # Calculate distance
                    dx = item['x'] - kept['x']
                    dy = item['y'] - kept['y']
                    distance = (dx**2 + dy**2)**0.5

                    if distance < distance_threshold:
                        is_duplicate = True
                        logger.debug(f"Removing duplicate {slug} at ({item['x']:.1f}, {item['y']:.1f}), keeping higher confidence one")
                        break

                if not is_duplicate:
                    kept_items.append(item)

            filtered_items.extend(kept_items)

        if len(filtered_items) < len(items):
            logger.info(f"Removed {len(items) - len(filtered_items)} duplicate detections")

        return filtered_items

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