import cv2
import numpy as np
import json

class MockObjectDetector:
    """Mock detector for testing without PyTorch"""
    def __init__(self):
        self.model = None
        
    def detect_objects(self, image_path):
        """Mock detection - returns some sample items"""
        # For testing, return some mock detected items
        return [
            {
                'slug': 'keyboard',
                'x': 200,
                'y': 300,
                'width': 300,
                'height': 100,
                'confidence': 0.85,
                'rotation': 0,
                'original_class': 'keyboard'
            },
            {
                'slug': 'mouse',
                'x': 550,
                'y': 320,
                'width': 60,
                'height': 90,
                'confidence': 0.78,
                'rotation': 0,
                'original_class': 'mouse'
            },
            {
                'slug': 'monitor',
                'x': 400,
                'y': 150,
                'width': 400,
                'height': 250,
                'confidence': 0.92,
                'rotation': 0,
                'original_class': 'tv'
            }
        ]
    
    def add_manual_item(self, item_slug, x, y, width=50, height=50):
        """Add a manually identified item"""
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