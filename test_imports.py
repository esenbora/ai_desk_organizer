import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)

try:
    import PyQt6
    print("PyQt6 imported successfully")
except ImportError as e:
    print("PyQt6 import failed:", e)

try:
    import torch
    print("PyTorch imported successfully")
except ImportError as e:
    print("PyTorch import failed:", e)

try:
    import cv2
    print("OpenCV imported successfully")
except ImportError as e:
    print("OpenCV import failed:", e)