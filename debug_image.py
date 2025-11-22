import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap

class ImageTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Display Test")
        self.setGeometry(100, 100, 1000, 800)
        
        layout = QVBoxLayout(self)
        
        # Test loading different ways
        label1 = QLabel("Direct QPixmap load:")
        pixmap1 = QPixmap("test.jpg")  # Change to your image
        if not pixmap1.isNull():
            label1.setPixmap(pixmap1)
            label1.setText(f"Success: {pixmap1.width()}x{pixmap1.height()}")
        else:
            label1.setText("Failed to load")
        
        layout.addWidget(label1)
        
        # Add file info
        if os.path.exists("test.jpg"):
            size = os.path.getsize("test.jpg")
            layout.addWidget(QLabel(f"File size: {size} bytes"))
        else:
            layout.addWidget(QLabel("File not found"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageTestWindow()
    window.show()
    sys.exit(app.exec())