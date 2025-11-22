import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap

def test_image_loading():
    app = QApplication(sys.argv)
    
    # Test loading a sample image
    pixmap = QPixmap("test_image.jpg")  # Replace with your image path
    
    if pixmap.isNull():
        print("❌ Failed to load image")
        print("Try with a different image file")
    else:
        print(f"✅ Image loaded successfully!")
        print(f"Dimensions: {pixmap.width()} x {pixmap.height()}")
        print(f"Has alpha: {pixmap.hasAlpha()}")
    
    app.quit()

if __name__ == "__main__":
    test_image_loading()